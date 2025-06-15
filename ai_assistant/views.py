from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
import json
import time
from .models import Conversation, Message, AIUsageStats, TaskSuggestion
from .services import GeminiAIService
from tasks.models import Task, Category


@login_required
def chat_view(request, conversation_id=None):
    """صفحة المحادثة مع المساعد الذكي"""
    
    # الحصول على المحادثة أو إنشاء واحدة جديدة
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    else:
        conversation = None
    
    # الحصول على المحادثات الأخيرة
    recent_conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')[:10]
    
    # إحصائيات الاستخدام
    stats, created = AIUsageStats.objects.get_or_create(user=request.user)
    stats.reset_daily_count()
    
    # التأكد من أن الإحصائيات تحتوي على قيم صحيحة
    if not hasattr(stats, 'daily_messages_count') or stats.daily_messages_count is None:
        stats.daily_messages_count = 0

    daily_limit = 50  # حد يومي للرسائل

    context = {
        'conversation': conversation,
        'recent_conversations': recent_conversations,
        'usage_stats': stats,
        'daily_limit': daily_limit,
    }
    
    return render(request, 'ai_assistant/chat.html', context)


@login_required
@require_POST
def send_message_api(request):
    """API لإرسال رسالة إلى المساعد الذكي"""

    try:
        # التحقق من نوع المحتوى
        content_type = request.content_type

        if content_type and 'multipart/form-data' in content_type:
            # إذا كان هناك ملف مرفق، استخدم POST data
            message_content = request.POST.get('message', '').strip()
            conversation_id = request.POST.get('conversation_id')
        else:
            # إذا كان JSON عادي
            try:
                data = json.loads(request.body)
                message_content = data.get('message', '').strip()
                conversation_id = data.get('conversation_id')
            except (json.JSONDecodeError, UnicodeDecodeError):
                # في حالة فشل قراءة JSON، جرب POST data
                message_content = request.POST.get('message', '').strip()
                conversation_id = request.POST.get('conversation_id')

        if not message_content:
            return JsonResponse({
                'success': False,
                'error': _('الرسالة فارغة')
            })
        
        # التحقق من الحد اليومي
        stats, created = AIUsageStats.objects.get_or_create(user=request.user)
        stats.reset_daily_count()
        
        if stats.daily_messages_count >= 50:  # حد يومي
            return JsonResponse({
                'success': False,
                'error': _('تم تجاوز الحد اليومي للرسائل (50 رسالة)')
            })
        
        # الحصول على المحادثة أو إنشاء واحدة جديدة
        conversation = None

        # التحقق من صحة conversation_id
        if conversation_id and conversation_id != 'null' and conversation_id != 'undefined':
            try:
                conversation_id = int(conversation_id)
                conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
                print(f"✅ تم العثور على المحادثة: {conversation.id}")
            except (ValueError, TypeError):
                print(f"❌ conversation_id غير صحيح: {conversation_id}")
                conversation = None

        # إنشاء محادثة جديدة إذا لم توجد
        if not conversation:
            conversation = Conversation.objects.create(user=request.user)
            print(f"✅ تم إنشاء محادثة جديدة: {conversation.id}")
        
        # حفظ رسالة المستخدم
        try:
            user_message = Message.objects.create(
                conversation=conversation,
                message_type='user',
                content=message_content
            )
            print(f"✅ تم حفظ رسالة المستخدم: {user_message.id}")
        except Exception as e:
            print(f"❌ خطأ في حفظ رسالة المستخدم: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'{_("خطأ في حفظ الرسالة")}: {str(e)}'
            })
        
        # الحصول على تاريخ المحادثة
        conversation_history = conversation.messages.order_by('created_at')
        
        # إرسال الرسالة إلى Gemini AI
        ai_service = GeminiAIService()
        
        # التحقق من وجود صورة
        image_data = None
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            image_data = image_file.read()
            user_message.image = image_file
            user_message.save()
        
        print(f"🤖 إرسال رسالة للمساعد الذكي: {message_content[:50]}...")

        response = ai_service.send_message(
            message_content,
            request.user,
            image_data=image_data,
            conversation_history=conversation_history
        )

        print(f"📊 نتيجة المساعد الذكي: {response.get('success', False)}")
        if not response.get('success'):
            print(f"❌ خطأ المساعد الذكي: {response.get('error', 'غير محدد')}")

        if response['success']:
            # حفظ رد المساعد الذكي
            try:
                ai_message = Message.objects.create(
                    conversation=conversation,
                    message_type='assistant',
                    content=response['response'],
                    tokens_used=response.get('tokens_used', 0),
                    response_time=response.get('response_time', 0)
                )
                print(f"✅ تم حفظ رد المساعد الذكي: {ai_message.id}")
            except Exception as e:
                print(f"❌ خطأ في حفظ رد المساعد الذكي: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'{_("خطأ في حفظ رد المساعد")}: {str(e)}'
                })
            
            # تحديث عنوان المحادثة إذا كانت جديدة
            conversation.update_title_from_first_message()
            
            # البحث عن اقتراحات المهام
            suggestions = ai_service.extract_task_suggestions(response['response'])
            suggestion_ids = []

            for suggestion in suggestions:
                try:
                    task_suggestion = TaskSuggestion.objects.create(
                        user=request.user,
                        conversation=conversation,
                        suggested_title=suggestion['title'],
                        suggested_description=suggestion.get('description', ''),
                        suggested_priority=suggestion.get('priority', 'medium')
                    )
                    suggestion_ids.append(task_suggestion.id)
                    print(f"✅ تم حفظ اقتراح المهمة: {task_suggestion.id}")
                except Exception as e:
                    print(f"❌ خطأ في حفظ اقتراح المهمة: {str(e)}")
                    # لا نوقف العملية، فقط نسجل الخطأ
            
            return JsonResponse({
                'success': True,
                'conversation_id': conversation.id,
                'user_message': {
                    'id': user_message.id,
                    'content': user_message.content,
                    'created_at': user_message.created_at.isoformat(),
                    'has_image': bool(user_message.image)
                },
                'ai_message': {
                    'id': ai_message.id,
                    'content': ai_message.content,
                    'created_at': ai_message.created_at.isoformat(),
                    'response_time': ai_message.response_time
                },
                'suggestions': suggestion_ids,
                'remaining_messages': 50 - stats.daily_messages_count
            })
        else:
            return JsonResponse({
                'success': False,
                'error': response['error']
            })
            
    except json.JSONDecodeError as e:
        print(f"❌ خطأ في تحليل JSON: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': _('خطأ في تنسيق البيانات المرسلة')
        })
    except UnicodeDecodeError as e:
        print(f"❌ خطأ في ترميز النص: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': _('خطأ في ترميز النص')
        })
    except Exception as e:
        print(f"💥 خطأ غير متوقع في send_message_api: {str(e)}")
        print(f"📋 نوع المحتوى: {getattr(request, 'content_type', 'غير محدد')}")
        print(f"📋 طريقة الطلب: {request.method}")
        return JsonResponse({
            'success': False,
            'error': f'{_("خطأ في النظام")}: {str(e)}'
        })


@login_required
def conversations_api(request):
    """API لجلب المحادثات"""
    conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    
    data = []
    for conv in conversations:
        last_message = conv.messages.last()
        data.append({
            'id': conv.id,
            'title': conv.title,
            'created_at': conv.created_at.isoformat(),
            'updated_at': conv.updated_at.isoformat(),
            'message_count': conv.messages.count(),
            'last_message': last_message.content[:100] if last_message else '',
        })
    
    return JsonResponse(data, safe=False)


@login_required
def conversation_list_view(request):
    """قائمة المحادثات"""
    conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'ai_assistant/conversations.html', context)


@login_required
@require_POST
def delete_conversation(request, pk):
    """حذف محادثة"""
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    conversation.delete()
    
    messages.success(request, _('تم حذف المحادثة بنجاح'))
    return redirect('ai_assistant:conversation_list')


@login_required
def task_suggestions_view(request):
    """عرض اقتراحات المهام"""
    suggestions = TaskSuggestion.objects.filter(
        user=request.user,
        is_accepted=False
    ).order_by('-created_at')
    
    paginator = Paginator(suggestions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'ai_assistant/suggestions.html', context)


@login_required
@require_POST
def accept_suggestion(request, pk):
    """قبول اقتراح مهمة وإنشاؤها"""
    suggestion = get_object_or_404(TaskSuggestion, pk=pk, user=request.user)
    
    if suggestion.is_accepted:
        return JsonResponse({
            'success': False,
            'error': _('تم قبول هذا الاقتراح مسبقاً')
        })
    
    # إنشاء المهمة
    try:
        # البحث عن التصنيف المناسب
        category = None
        if suggestion.suggested_category:
            category = Category.objects.filter(
                name__icontains=suggestion.suggested_category
            ).first()
        
        task = Task.objects.create(
            user=request.user,
            title=suggestion.suggested_title,
            description=suggestion.suggested_description,
            category=category,
            priority=suggestion.suggested_priority or 'medium',
            due_date=suggestion.suggested_due_date
        )
        
        # تحديث الاقتراح
        suggestion.is_accepted = True
        suggestion.created_task = task
        suggestion.save()
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'task_url': task.get_absolute_url(),
            'message': _('تم إنشاء المهمة بنجاح')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'{_("خطأ في إنشاء المهمة")}: {str(e)}'
        })


@login_required
def usage_stats_view(request):
    """عرض إحصائيات الاستخدام"""
    stats, created = AIUsageStats.objects.get_or_create(user=request.user)
    stats.reset_daily_count()
    
    # إحصائيات إضافية
    recent_conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')[:5]
    accepted_suggestions = TaskSuggestion.objects.filter(user=request.user, is_accepted=True).count()
    pending_suggestions = TaskSuggestion.objects.filter(user=request.user, is_accepted=False).count()
    
    context = {
        'stats': stats,
        'recent_conversations': recent_conversations,
        'accepted_suggestions': accepted_suggestions,
        'pending_suggestions': pending_suggestions,
        'daily_limit': 50,
    }
    
    return render(request, 'ai_assistant/usage_stats.html', context)
