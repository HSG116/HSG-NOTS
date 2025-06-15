from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.urls import reverse
from .models import Task, Category
from .forms import TaskForm, TaskFilterForm


@login_required
def dashboard_view(request):
    """لوحة التحكم الرئيسية"""
    user = request.user
    
    # إحصائيات المهام
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, status='completed').count()
    pending_tasks = Task.objects.filter(user=user, status='pending').count()
    overdue_tasks = Task.objects.filter(
        user=user, 
        status__in=['pending', 'in_progress'],
        due_date__lt=timezone.now()
    ).count()
    
    # المهام الحديثة
    recent_tasks = Task.objects.filter(user=user).order_by('-created_at')[:5]
    
    # المهام القادمة
    upcoming_tasks = Task.objects.filter(
        user=user,
        status__in=['pending', 'in_progress'],
        due_date__gte=timezone.now()
    ).order_by('due_date')[:5]
    
    # المهام المتأخرة
    overdue_task_list = Task.objects.filter(
        user=user,
        status__in=['pending', 'in_progress'],
        due_date__lt=timezone.now()
    ).order_by('due_date')[:5]
    
    # إحصائيات التصنيفات
    category_stats = Category.objects.annotate(
        task_count=Count('task', filter=Q(task__user=user))
    ).filter(task_count__gt=0)
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': user.completion_rate,
        'recent_tasks': recent_tasks,
        'upcoming_tasks': upcoming_tasks,
        'overdue_task_list': overdue_task_list,
        'category_stats': category_stats,
    }
    
    return render(request, 'tasks/dashboard.html', context)


@login_required
def task_list_view(request):
    """قائمة المهام مع الفلترة والبحث"""
    tasks = Task.objects.filter(user=request.user)
    
    # الفلترة
    filter_form = TaskFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data['status']:
            tasks = tasks.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['priority']:
            tasks = tasks.filter(priority=filter_form.cleaned_data['priority'])
        if filter_form.cleaned_data['category']:
            tasks = tasks.filter(category=filter_form.cleaned_data['category'])
        if filter_form.cleaned_data['search']:
            search_query = filter_form.cleaned_data['search']
            tasks = tasks.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
    
    # الترتيب
    sort_by = request.GET.get('sort', '-created_at')
    tasks = tasks.order_by(sort_by)
    
    # التقسيم إلى صفحات
    paginator = Paginator(tasks, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'sort_by': sort_by,
    }
    
    return render(request, 'tasks/list.html', context)


@login_required
def task_create_view(request):
    """إنشاء مهمة جديدة"""
    if request.method == 'POST':
        try:
            form = TaskForm(request.POST, request.FILES)
            if form.is_valid():
                task = form.save(commit=False)
                task.user = request.user
                task.save()

                # إذا كان طلب AJAX، إرجاع JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'task_id': task.pk,
                        'message': 'تم إنشاء المهمة بنجاح!'
                    })

                messages.success(request, _('تم إنشاء المهمة بنجاح'))
                return redirect('tasks:detail', pk=task.pk)
            else:
                # إذا كان طلب AJAX وهناك أخطاء
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': form.errors,
                        'message': 'يرجى تصحيح الأخطاء في النموذج'
                    })
        except Exception as e:
            # معالجة الأخطاء غير المتوقعة
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'حدث خطأ غير متوقع: {str(e)}'
                })
            messages.error(request, f'حدث خطأ في إنشاء المهمة: {str(e)}')
    else:
        form = TaskForm()

    return render(request, 'tasks/create.html', {'form': form})


@login_required
def task_detail_view(request, pk):
    """تفاصيل المهمة"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    context = {
        'task': task,
    }
    
    return render(request, 'tasks/detail.html', context)


@login_required
def task_edit_view(request, pk):
    """تحرير المهمة"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    print(f"Editing task: {task.title} (ID: {task.pk})")  # تشخيص

    if request.method == 'POST':
        print(f"POST data received: {request.POST}")  # تشخيص
        form = TaskForm(request.POST, request.FILES, instance=task)

        if form.is_valid():
            print("Form is valid, attempting to save...")  # تشخيص
            try:
                # حفظ المهمة المحدثة
                updated_task = form.save(commit=False)
                updated_task.user = request.user  # التأكد من أن المستخدم صحيح

                print(f"Before save - Title: {updated_task.title}, Priority: {updated_task.priority}")  # تشخيص

                # حفظ المهمة (سيتم تحديث updated_at تلقائياً في النموذج)
                updated_task = form.save()

                print(f"After save - Title: {updated_task.title}, Priority: {updated_task.priority}")  # تشخيص

                messages.success(request, _('تم تحديث المهمة "{}" بنجاح! ✅ جميع التغييرات تم حفظها.').format(updated_task.title))

                # إذا كان الطلب AJAX، أرجع JSON response
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': _('تم تحديث المهمة بنجاح! ✅'),
                        'redirect_url': reverse('tasks:detail', kwargs={'pk': updated_task.pk})
                    })

                return redirect('tasks:detail', pk=updated_task.pk)

            except Exception as e:
                messages.error(request, _('حدث خطأ أثناء حفظ المهمة: {}').format(str(e)))
                print(f"Error saving task: {e}")  # للتشخيص
        else:
            messages.error(request, _('يرجى تصحيح الأخطاء أدناه'))
            print(f"Form errors: {form.errors}")  # للتشخيص
    else:
        form = TaskForm(instance=task)

    context = {
        'form': form,
        'task': task,
        'page_title': _('تحرير المهمة'),
    }
    return render(request, 'tasks/edit.html', context)


@login_required
def task_delete_view(request, pk):
    """حذف المهمة"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        task.delete()
        # تحديث إحصائيات المستخدم
        request.user.total_tasks -= 1
        if task.status == 'completed':
            request.user.completed_tasks -= 1
        request.user.save()
        
        messages.success(request, _('تم حذف المهمة بنجاح'))
        return redirect('tasks:list')
    
    return render(request, 'tasks/delete.html', {'task': task})


@login_required
def task_toggle_status(request, pk):
    """تغيير حالة المهمة (مكتملة/غير مكتملة)"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if task.status == 'completed':
        task.status = 'pending'
        task.completed_at = None
        request.user.completed_tasks -= 1
    else:
        task.status = 'completed'
        task.completed_at = timezone.now()
        request.user.completed_tasks += 1
    
    task.save()
    request.user.save()
    
    return JsonResponse({
        'success': True,
        'new_status': task.status,
        'message': _('تم تحديث حالة المهمة')
    })


@login_required
def calendar_view(request):
    """عرض التقويم"""
    tasks = Task.objects.filter(
        user=request.user,
        due_date__isnull=False
    ).order_by('due_date')
    
    context = {
        'tasks': tasks,
    }
    
    return render(request, 'tasks/calendar.html', context)


@login_required
def category_list_view(request):
    """قائمة التصنيفات"""
    categories = Category.objects.annotate(
        task_count=Count('task', filter=Q(task__user=request.user))
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'tasks/categories.html', context)


@login_required
def api_tasks_json(request):
    """API لإرجاع المهام بصيغة JSON للتقويم"""
    tasks = Task.objects.filter(
        user=request.user,
        due_date__isnull=False
    )
    
    events = []
    for task in tasks:
        events.append({
            'id': task.id,
            'title': task.title,
            'start': task.due_date.isoformat(),
            'backgroundColor': task.priority_color,
            'borderColor': task.priority_color,
            'url': task.get_absolute_url(),
            'extendedProps': {
                'priority': task.priority,
                'status': task.status,
                'category': task.category.name if task.category else '',
            }
        })
    
    return JsonResponse(events, safe=False)


@login_required
def api_categories_json(request):
    """API لإرجاع التصنيفات بصيغة JSON"""
    from .models import Category

    categories = Category.objects.all().values('id', 'name', 'icon', 'color')
    categories_list = list(categories)

    return JsonResponse(categories_list, safe=False)
