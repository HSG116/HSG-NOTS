import requests
import json
import base64
import time
from django.conf import settings
from django.utils.translation import gettext as _
from .models import AIUsageStats


class GeminiAIService:
    """خدمة التكامل مع Gemini AI"""

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', 'AIzaSyC5lLrmkNpz-WipRo4U1NcAw5v7pzQTu7o')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
    def _prepare_headers(self):
        """تحضير headers للطلب"""
        return {
            'Content-Type': 'application/json',
        }
    
    def _prepare_text_payload(self, message, conversation_history=None):
        """تحضير البيانات للرسائل النصية"""

        # إضافة السياق العربي والتعليمات الأساسية
        system_prompt = """أنت مساعد ذكي متخصص في إدارة المهام اليومية باللغة العربية. تساعد المستخدمين في:

🎯 **مهامك الأساسية:**
1. **تنظيم المهام**: تحويل الأفكار إلى مهام واضحة ومنظمة
2. **حل الواجبات**: مساعدة في الواجبات الدراسية والأسئلة الصعبة
3. **اقتراحات ذكية**: تقديم حلول إبداعية للمشاكل اليومية
4. **تحليل الصور**: فهم وتحليل الصور والمستندات
5. **التخطيط**: مساعدة في التخطيط اليومي والأسبوعي

💡 **أسلوبك:**
- تحدث بالعربية بشكل طبيعي ومفهوم
- كن مفيداً ومتعاوناً
- اعطِ إجابات واضحة ومفصلة
- اقترح مهام عملية عند الحاجة

🚀 **ابدأ بالمساعدة!**"""

        # بناء المحتوى
        full_message = f"{system_prompt}\n\n**سؤال المستخدم:** {message}"

        # إضافة السياق من المحادثة السابقة
        if conversation_history and conversation_history.exists():
            context = "\n\n**السياق من المحادثة السابقة:**\n"
            # الحصول على آخر 3 رسائل بطريقة آمنة
            recent_messages = list(conversation_history.order_by('-created_at')[:3])
            recent_messages.reverse()  # ترتيب من الأقدم للأحدث
            for msg in recent_messages:
                role = "المستخدم" if msg.message_type == "user" else "المساعد"
                context += f"{role}: {msg.content[:200]}...\n"
            full_message = context + "\n" + full_message

        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": full_message
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.8,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "stopSequences": []
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
    
    def _prepare_image_payload(self, message, image_data, conversation_history=None):
        """تحضير البيانات للرسائل التي تحتوي على صور"""

        # تحليل نوع الطلب لتخصيص التحليل
        message_lower = message.lower()

        if any(word in message_lower for word in ['نظم', 'رتب', 'مهام', 'جدول', 'وقت', 'organize', 'schedule']):
            system_prompt = """📅 **خبير تحليل الجداول والمهام من الصور**

أنت متخصص في تحليل الصور لاستخراج المهام والجداول الزمنية. مهامك:

🔍 **تحليل الصورة:**
- اقرأ جميع النصوص في الصورة بدقة عالية
- استخرج المهام والأنشطة المذكورة
- حدد الأوقات والمواعيد إن وجدت
- لاحظ أي ملاحظات أو تفاصيل إضافية

📋 **تنظيم المهام:**
- رتب المهام حسب الأولوية والوقت
- اقترح أوقات مناسبة للمهام غير المحددة
- أنشئ جدول زمني منطقي ومتوازن
- راعي فترات الراحة والوجبات

⏰ **تنسيق الجدول:**
```
📅 **جدول المهام المستخرج من الصورة**

🌅 **الصباح (6:00 - 12:00)**
⏰ [الوقت] | [رمز] [اسم المهمة] - [تفاصيل]

🌞 **بعد الظهر (12:00 - 18:00)**
⏰ [الوقت] | [رمز] [اسم المهمة] - [تفاصيل]

🌙 **المساء (18:00 - 22:00)**
⏰ [الوقت] | [رمز] [اسم المهمة] - [تفاصيل]
```

💡 **نصائح إضافية:**
- اقترح تحسينات على الجدول
- أضف مهام مهمة قد تكون مفقودة
- قدم نصائح لتحسين الإنتاجية"""

        elif any(word in message_lower for word in ['حل', 'واجب', 'مسألة', 'سؤال', 'homework', 'solve']):
            system_prompt = """📚 **خبير تحليل الواجبات والمسائل من الصور**

أنت مدرس ذكي متخصص في تحليل الواجبات والمسائل من الصور. مهامك:

🔍 **قراءة دقيقة:**
- اقرأ جميع النصوص والأرقام بعناية فائقة
- حدد نوع المسألة أو الواجب
- استخرج جميع المعطيات والمطلوب

📝 **تحليل المحتوى:**
- حدد المادة الدراسية (رياضيات، علوم، لغة...)
- اشرح المفاهيم المطلوبة
- حدد خطوات الحل المطلوبة

✅ **تقديم الحل:**
- اشرح الحل خطوة بخطوة
- وضح كل خطوة بالتفصيل
- قدم الإجابة النهائية بوضوح
- أضف نصائح لفهم أفضل

🎯 **أسلوب التعليم:**
- استخدم لغة بسيطة ومفهومة
- قدم أمثلة إضافية عند الحاجة
- تأكد من الفهم قبل الانتقال
- شجع على التعلم والاستكشاف"""

        else:
            system_prompt = """🖼️ **محلل الصور الذكي المتطور**

أنت خبير متقدم في تحليل الصور بجميع أنواعها. مهامك:

🔍 **تحليل شامل:**
- وصف دقيق ومفصل لمحتوى الصورة
- تحديد جميع العناصر والتفاصيل المهمة
- قراءة أي نصوص أو كتابات موجودة
- تحليل الألوان والأشكال والرموز

📋 **استخراج المعلومات:**
- استخرج أي معلومات مفيدة
- حدد السياق والغرض من الصورة
- اربط المحتوى بالطلب المحدد
- قدم تفسيرات منطقية

💡 **تقديم المساعدة:**
- أجب على السؤال المطروح بدقة
- اقترح حلول أو تفسيرات إضافية
- قدم معلومات ذات صلة
- ساعد في فهم المحتوى بشكل أفضل

🎨 **أسلوب التحليل:**
- كن دقيقاً ومفصلاً في الوصف
- استخدم لغة واضحة ومفهومة
- نظم المعلومات بطريقة منطقية
- قدم تحليل شامل ومفيد"""

        # تحويل الصورة إلى base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # بناء الرسالة مع الصورة
        full_message = f"{system_prompt}\n\n**طلب المستخدم:** {message}\n\n**يرجى تحليل الصورة المرفقة والإجابة على السؤال.**"

        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": full_message
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
    
    def send_message(self, message, user, image_data=None, conversation_history=None):
        """إرسال رسالة إلى Gemini AI مع حل بديل محلي"""

        # محاولة استخدام Gemini AI أولاً
        try:
            start_time = time.time()

            # تحضير البيانات
            if image_data:
                payload = self._prepare_image_payload(message, image_data, conversation_history)
            else:
                payload = self._prepare_text_payload(message, conversation_history)

            # إرسال الطلب
            url = f"{self.api_url}?key={self.api_key}"
            headers = self._prepare_headers()

            print(f"🚀 إرسال طلب إلى Gemini API: {url}")
            print(f"📝 محتوى الرسالة: {message[:100]}...")

            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response_time = time.time() - start_time

            print(f"📊 كود الاستجابة: {response.status_code}")
            print(f"⏱️ وقت الاستجابة: {response_time:.2f} ثانية")

            if response.status_code == 200:
                data = response.json()
                print(f"📦 بيانات الاستجابة: {str(data)[:200]}...")

                # استخراج النص من الاستجابة
                if 'candidates' in data and len(data['candidates']) > 0:
                    candidate = data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        ai_response = candidate['content']['parts'][0]['text']

                        print(f"✅ تم الحصول على استجابة: {ai_response[:100]}...")

                        # تحديث إحصائيات الاستخدام
                        self._update_usage_stats(user, response_time, image_data is not None)

                        return {
                            'success': True,
                            'response': ai_response,
                            'response_time': response_time,
                            'tokens_used': self._estimate_tokens(message + ai_response)
                        }
                    else:
                        print("❌ بنية الاستجابة غير صحيحة - لا توجد أجزاء")
                else:
                    print("❌ بنية الاستجابة غير صحيحة - لا توجد مرشحين")

                return {
                    'success': False,
                    'error': _('لم يتم الحصول على استجابة صحيحة من المساعد الذكي'),
                    'response_time': response_time,
                    'raw_response': data
                }

            else:
                error_msg = _('خطأ في الاتصال بالمساعد الذكي')
                error_details = ""

                try:
                    error_data = response.json()
                    error_details = str(error_data)
                    print(f"❌ تفاصيل الخطأ: {error_details}")
                except:
                    error_details = response.text
                    print(f"❌ نص الخطأ: {error_details}")

                if response.status_code == 400:
                    error_msg = _('طلب غير صحيح - تحقق من البيانات المرسلة')
                elif response.status_code == 401:
                    error_msg = _('مفتاح API غير صحيح أو منتهي الصلاحية')
                elif response.status_code == 403:
                    error_msg = _('ليس لديك صلاحية للوصول لهذه الخدمة')
                elif response.status_code == 429:
                    error_msg = _('تم تجاوز الحد المسموح من الطلبات - حاول لاحقاً')
                elif response.status_code == 500:
                    error_msg = _('خطأ في خادم Google - حاول لاحقاً')
                elif response.status_code == 503:
                    print("🔄 الخادم محمل بشدة، التبديل إلى المساعد المحلي...")
                    return self._local_assistant_response(message, user, image_data)

                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'error_details': error_details
                }

        except requests.exceptions.Timeout:
            print("⏰ انتهت مهلة الاتصال")
            return {
                'success': False,
                'error': _('انتهت مهلة الاتصال بالمساعد الذكي - حاول مرة أخرى')
            }
        except requests.exceptions.ConnectionError:
            print("🌐 خطأ في الاتصال بالإنترنت")
            return {
                'success': False,
                'error': _('خطأ في الاتصال بالإنترنت - تحقق من اتصالك')
            }
        except requests.exceptions.RequestException as e:
            print(f"🌐 خطأ في الطلب: {str(e)}")
            return {
                'success': False,
                'error': _('خطأ في إرسال الطلب للمساعد الذكي')
            }
        except json.JSONDecodeError as e:
            print(f"📦 خطأ في تحليل استجابة JSON: {str(e)}")
            return {
                'success': False,
                'error': _('خطأ في تحليل استجابة المساعد الذكي')
            }
        except Exception as e:
            print(f"💥 خطأ في Gemini API: {str(e)}")
            print("🔄 التبديل إلى المساعد المحلي...")

            # استخدام المساعد المحلي كحل بديل
            return self._local_assistant_response(message, user, image_data)

    def _local_assistant_response(self, message, user, image_data=None):
        """مساعد ذكي محلي كحل بديل"""

        start_time = time.time()

        # إذا كانت هناك صورة، نقدم استجابة خاصة بالصور
        if image_data:
            return self._handle_image_locally(message, user, image_data, start_time)

        # تحليل الرسالة وتقديم استجابة ذكية
        message_lower = message.lower()

        # استجابات للترحيب
        if any(word in message_lower for word in ['مرحبا', 'السلام', 'أهلا', 'hello', 'hi']):
            response = f"""مرحباً {user.first_name}! 👋

أنا مساعدك الذكي لإدارة المهام. يمكنني مساعدتك في:

🎯 **تنظيم المهام**: تحويل أفكارك إلى مهام واضحة
📚 **حل الواجبات**: مساعدة في الدراسة والأسئلة
💡 **اقتراحات ذكية**: حلول للمشاكل اليومية
📋 **التخطيط**: تنظيم وقتك بفعالية

كيف يمكنني مساعدتك اليوم؟"""

        # استجابات لتنظيم المهام
        elif any(word in message_lower for word in ['نظم', 'رتب', 'مهام', 'organize', 'tasks']):
            # استخراج المهام من النص
            import re

            # البحث عن المهام في النص
            tasks_found = []
            task_patterns = [
                r'(?:مهمة|مهام|task|todo)[\s:]*([^،.]+)',
                r'(?:يجب|ينبغي|need to|should)[\s]*([^،.]+)',
                r'(?:أريد|أود|want to|wish to)[\s]*([^،.]+)',
            ]

            for pattern in task_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                tasks_found.extend(matches)

            # إذا لم نجد مهام محددة، نقدم مثال عام
            if not tasks_found:
                response = f"""📋 **مرحباً {user.first_name}! دعني أساعدك في تنظيم مهامك**

لم أجد مهام محددة في رسالتك. إليك مثال على كيفية تنظيم المهام:

📅 **جدول يوم مثالي**

🌅 **الصباح (6:00 - 12:00)**
⏰ 7:00 - 8:00 | 🏃‍♂️ ممارسة الرياضة
⏰ 8:00 - 9:00 | 🍳 الإفطار والاستعداد
⏰ 9:00 - 11:00 | 📚 دراسة أو عمل مهم (تركيز عالي)
⏰ 11:00 - 12:00 | ☕ استراحة وتحضير للغداء

🌞 **بعد الظهر (12:00 - 18:00)**
⏰ 12:00 - 13:00 | 🍽️ الغداء
⏰ 13:00 - 15:00 | 💼 مهام العمل أو المشاريع
⏰ 15:00 - 16:00 | 🛒 المهام الخارجية (تسوق، مواعيد)
⏰ 16:00 - 18:00 | 📖 مراجعة أو مهام إضافية

🌙 **المساء (18:00 - 22:00)**
⏰ 18:00 - 19:00 | 🍽️ العشاء مع العائلة
⏰ 19:00 - 21:00 | 🎯 هوايات أو وقت شخصي
⏰ 21:00 - 22:00 | 📱 استرخاء ومراجعة اليوم

💡 **نصائح ذهبية:**
- ابدأ بالمهام الصعبة في الصباح
- خذ استراحة كل ساعتين
- اترك وقت للطوارئ
- راجع إنجازاتك في نهاية اليوم

**أخبرني بمهامك المحددة وسأنظمها لك بشكل مثالي!**"""
            else:
                # تنظيم المهام المستخرجة
                organized_tasks = []
                for i, task in enumerate(tasks_found[:8], 1):  # أقصى 8 مهام
                    clean_task = task.strip()
                    if len(clean_task) > 3:
                        organized_tasks.append(f"{i}. **{clean_task}**")

                response = f"""📋 **جدول مهامك المنظم - {user.first_name}**

استخرجت المهام التالية من رسالتك:

🎯 **المهام المحددة:**
{chr(10).join(organized_tasks)}

📅 **جدول زمني مقترح:**

🌅 **الصباح (7:00 - 12:00)**
⏰ 7:00 - 8:00 | 🏃‍♂️ ممارسة الرياضة والإفطار
⏰ 8:00 - 10:00 | 📚 {organized_tasks[0].split('**')[1] if organized_tasks else 'المهمة الأولى'}
⏰ 10:00 - 12:00 | 💼 {organized_tasks[1].split('**')[1] if len(organized_tasks) > 1 else 'المهمة الثانية'}

🌞 **بعد الظهر (12:00 - 18:00)**
⏰ 12:00 - 13:00 | 🍽️ الغداء واستراحة
⏰ 13:00 - 15:00 | 🎯 {organized_tasks[2].split('**')[1] if len(organized_tasks) > 2 else 'المهمة الثالثة'}
⏰ 15:00 - 17:00 | ⚡ {organized_tasks[3].split('**')[1] if len(organized_tasks) > 3 else 'المهمة الرابعة'}
⏰ 17:00 - 18:00 | 🛒 مهام خارجية أو استراحة

🌙 **المساء (18:00 - 22:00)**
⏰ 18:00 - 19:00 | 🍽️ العشاء
⏰ 19:00 - 21:00 | 📖 {organized_tasks[4].split('**')[1] if len(organized_tasks) > 4 else 'مراجعة أو استرخاء'}
⏰ 21:00 - 22:00 | 🎮 وقت شخصي

💡 **نصائح مخصصة لك:**
- رتبت المهام حسب مستوى الطاقة المطلوب
- المهام الذهنية في الصباح عندما يكون التركيز أعلى
- المهام العملية في بعد الظهر
- وقت للاسترخاء في المساء

هل تريد تعديل هذا الجدول أو إضافة تفاصيل أكثر؟"""

        # استجابات لحل الواجبات
        elif any(word in message_lower for word in ['حل', 'واجب', 'مسألة', 'solve', 'homework', '×', '*', '+', '-', '÷']):
            # البحث عن عمليات حسابية
            import re
            math_pattern = r'(\d+)\s*[×*]\s*(\d+)'
            match = re.search(math_pattern, message)

            if match:
                num1, num2 = int(match.group(1)), int(match.group(2))
                result = num1 * num2
                response = f"""🧮 **حل المسألة الرياضية**

المسألة: {num1} × {num2} = ؟

**الحل خطوة بخطوة:**
1. نضرب {num1} في {num2}
2. {num1} × {num2} = {result}

**الإجابة النهائية: {result}** ✅

💡 **نصيحة**: يمكنك استخدام جدول الضرب أو الآلة الحاسبة للتأكد من النتيجة!"""
            else:
                response = """📚 **مساعدة في الواجبات**

أنا هنا لمساعدتك! يمكنني:

🧮 **الرياضيات**: حل المعادلات والعمليات الحسابية
📖 **العلوم**: شرح المفاهيم العلمية
📝 **اللغة**: مساعدة في القواعد والإملاء
🌍 **الجغرافيا**: معلومات عن البلدان والقارات

اكتب سؤالك بوضوح وسأساعدك في حله خطوة بخطوة!"""

        # استجابات للاقتراحات
        elif any(word in message_lower for word in ['اقترح', 'نصيحة', 'ساعد', 'suggest', 'help']):
            response = """💡 **اقتراحات ذكية لتحسين إنتاجيتك**

**⏰ إدارة الوقت:**
- استخدم تقنية البومودورو (25 دقيقة عمل + 5 دقائق راحة)
- حدد أهدافاً يومية واضحة
- تجنب المشتتات أثناء العمل

**📋 تنظيم المهام:**
- اكتب مهامك في قائمة واضحة
- رتبها حسب الأولوية والموعد النهائي
- قسم المهام الكبيرة إلى خطوات صغيرة

**🎯 تحسين التركيز:**
- اختر مكان هادئ للدراسة
- أغلق الهاتف أثناء العمل المهم
- خذ فترات راحة منتظمة

**💪 الحفاظ على الطاقة:**
- نم 7-8 ساعات يومياً
- اشرب الماء بانتظام
- مارس الرياضة 30 دقيقة يومياً

أي من هذه النصائح تريد التفصيل فيها أكثر؟"""

        # استجابة افتراضية
        else:
            response = f"""مرحباً {user.first_name}! 🤖

فهمت رسالتك وأقدر ثقتك بي. كمساعد ذكي، يمكنني مساعدتك في:

🎯 **تنظيم المهام**: قل "نظم مهامي" وأخبرني بمهامك
📚 **حل الواجبات**: اكتب سؤالك وسأساعدك في حله
💡 **اقتراحات**: قل "اقترح علي" وسأعطيك نصائح مفيدة
📋 **التخطيط**: ساعدك في تنظيم يومك أو أسبوعك

**مثال**: "نظم مهامي: دراسة الرياضيات، شراء البقالة، ممارسة الرياضة"

كيف يمكنني مساعدتك بشكل أكثر تحديداً؟"""

        response_time = time.time() - start_time

        # تحديث إحصائيات الاستخدام
        self._update_usage_stats(user, response_time, image_data is not None)

        return {
            'success': True,
            'response': response,
            'response_time': response_time,
            'tokens_used': self._estimate_tokens(message + response),
            'source': 'local_assistant'
        }
    
    def _estimate_tokens(self, text):
        """تقدير عدد الرموز المستخدمة"""
        # تقدير تقريبي: كل 4 أحرف = رمز واحد
        return len(text) // 4
    
    def _update_usage_stats(self, user, response_time, has_image=False):
        """تحديث إحصائيات الاستخدام"""
        try:
            stats, created = AIUsageStats.objects.get_or_create(user=user)
            stats.reset_daily_count()  # إعادة تعيين العداد اليومي إذا لزم الأمر
            
            stats.total_messages += 1
            stats.daily_messages_count += 1
            
            if has_image:
                stats.total_images_analyzed += 1
            
            stats.save()
            
        except Exception as e:
            # تسجيل الخطأ ولكن لا نوقف العملية
            print(f"Error updating usage stats: {e}")
    
    def extract_task_suggestions(self, ai_response):
        """استخراج اقتراحات المهام من استجابة المساعد الذكي"""
        suggestions = []

        # البحث عن كلمات مفتاحية تدل على المهام
        task_keywords = [
            'مهمة:', 'مهام:', 'يجب عليك:', 'ينبغي:', 'اقترح:', 'خطوة:',
            'Task:', 'TODO:', 'Action:', 'Suggestion:', 'Step:', '✅', '📝', '🎯'
        ]

        # البحث عن أنماط القوائم المرقمة والنقطية
        import re
        list_patterns = [
            r'^\d+\.\s*(.+)',  # 1. مهمة
            r'^-\s*(.+)',      # - مهمة
            r'^\*\s*(.+)',     # * مهمة
            r'^•\s*(.+)',      # • مهمة
        ]

        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()

            # البحث عن الكلمات المفتاحية
            for keyword in task_keywords:
                if keyword in line:
                    task_text = line.split(keyword, 1)[1].strip()
                    if task_text and len(task_text) > 5:
                        # تحديد الأولوية بناءً على الكلمات
                        priority = 'medium'
                        if any(word in task_text.lower() for word in ['عاجل', 'مهم', 'urgent', 'important']):
                            priority = 'high'
                        elif any(word in task_text.lower() for word in ['بسيط', 'سهل', 'simple', 'easy']):
                            priority = 'low'

                        suggestions.append({
                            'title': task_text[:80],  # أول 80 حرف كعنوان
                            'description': task_text,
                            'priority': priority
                        })
                    break

            # البحث عن الأنماط المرقمة والنقطية
            for pattern in list_patterns:
                match = re.match(pattern, line)
                if match:
                    task_text = match.group(1).strip()
                    if task_text and len(task_text) > 5:
                        # تنظيف النص من الرموز التعبيرية
                        clean_text = re.sub(r'[🎯📝✅🔥💡⭐]', '', task_text).strip()
                        if clean_text:
                            suggestions.append({
                                'title': clean_text[:80],
                                'description': clean_text,
                                'priority': 'medium'
                            })
                    break

        # إزالة المكررات
        unique_suggestions = []
        seen_titles = set()
        for suggestion in suggestions:
            if suggestion['title'].lower() not in seen_titles:
                seen_titles.add(suggestion['title'].lower())
                unique_suggestions.append(suggestion)

        return unique_suggestions[:5]  # أقصى 5 اقتراحات

    def _handle_image_locally(self, message, user, image_data, start_time):
        """معالجة الصور محلياً عندما لا يتوفر Gemini"""

        message_lower = message.lower()

        # تحديد نوع الطلب
        if any(word in message_lower for word in ['نظم', 'رتب', 'مهام', 'جدول', 'وقت', 'organize', 'schedule']):
            response = f"""📅 **تحليل الصورة لتنظيم المهام - {user.first_name}**

🖼️ **تم استلام الصورة بنجاح!**

للأسف، لا يمكنني قراءة محتوى الصورة حالياً بسبب عدم توفر خدمة التحليل المتقدمة. ولكن يمكنني مساعدتك بطرق أخرى:

📋 **ما يمكنني فعله:**
1. **اكتب المهام نصياً** - انسخ المهام من الصورة واكتبها لي
2. **أنظم المهام** - سأرتبها في جدول زمني مثالي
3. **أقترح أوقات** - سأحدد أفضل الأوقات لكل مهمة
4. **أضيف نصائح** - سأقدم نصائح لتحسين الإنتاجية

📝 **مثال على كيفية كتابة المهام:**
"نظم مهامي: دراسة الرياضيات، شراء البقالة، ممارسة الرياضة، الاتصال بالطبيب"

🎯 **أو أخبرني:**
- ما هي المهام الموجودة في الصورة؟
- هل هناك أوقات محددة مذكورة؟
- ما هي أولوياتك؟

سأكون سعيداً لمساعدتك في تنظيم مهامك بأفضل طريقة ممكنة! 💪"""

        elif any(word in message_lower for word in ['حل', 'واجب', 'مسألة', 'سؤال', 'homework', 'solve']):
            response = f"""📚 **تحليل الواجب من الصورة - {user.first_name}**

🖼️ **تم استلام صورة الواجب!**

أعتذر، لا يمكنني قراءة النصوص في الصورة حالياً. ولكن يمكنني مساعدتك بطرق فعالة:

✍️ **اكتب السؤال نصياً:**
- انسخ نص السؤال أو المسألة
- اكتب المعطيات والمطلوب
- حدد المادة الدراسية

🧮 **أمثلة على ما يمكنني حله:**
- **الرياضيات**: معادلات، هندسة، حساب
- **الفيزياء**: قوانين، مسائل حركة
- **الكيمياء**: معادلات كيميائية، تفاعلات
- **اللغة العربية**: قواعد، إعراب، بلاغة

📖 **كيفية طرح السؤال:**
"حل هذه المسألة: إذا كان س + 5 = 12، فما قيمة س؟"

💡 **مميزات المساعدة:**
- شرح خطوة بخطوة
- أمثلة إضافية للفهم
- نصائح لحل مسائل مشابهة
- تبسيط المفاهيم الصعبة

اكتب سؤالك وسأساعدك فوراً! 🎓"""

        else:
            response = f"""🖼️ **تحليل الصورة - {user.first_name}**

تم استلام الصورة بنجاح! 📸

للأسف، خدمة تحليل الصور غير متاحة حالياً، ولكن يمكنني مساعدتك بطرق أخرى:

💡 **اقتراحات للمساعدة:**

📝 **إذا كانت الصورة تحتوي على نص:**
- اكتب النص الموجود في الصورة
- سأساعدك في تحليله أو الإجابة عليه

📋 **إذا كانت قائمة مهام:**
- اكتب المهام نصياً
- سأنظمها في جدول زمني مثالي

🧮 **إذا كانت مسألة رياضية:**
- اكتب المسألة بالأرقام والرموز
- سأحلها خطوة بخطوة

🎯 **إذا كنت تريد تحليل عام:**
- صف ما تراه في الصورة
- أخبرني ما تريد معرفته عنها

**مثال:** "في الصورة قائمة مهام تحتوي على: دراسة، تسوق، رياضة - نظمها لي"

أنا هنا لمساعدتك بأي طريقة ممكنة! 🤖✨"""

        response_time = time.time() - start_time

        # تحديث إحصائيات الاستخدام
        self._update_usage_stats(user, response_time, True)

        return {
            'success': True,
            'response': response,
            'response_time': response_time,
            'tokens_used': self._estimate_tokens(message + response),
            'source': 'local_assistant_image'
        }
