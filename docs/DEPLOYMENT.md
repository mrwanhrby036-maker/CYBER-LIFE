# النشر على Vercel وFirebase

## إعداد Vercel في هذا الفرع

أُضيف مدخل Python ASGI في `main.py` يستورد تطبيق FastAPI الموجود في `backend/app` دون نسخ منطق API أو استبدال المنصة. يبقي `vercel.json` صفحات `frontend/` كملفات ثابتة ويضبط Function Python بملفات التطبيق ومحتوى `content/`. يحتوي `requirements.txt` الجذري على اعتمادات التشغيل فقط، و`.python-version` يطابق Python 3.12 المستخدم في Docker.

عند نجاح البناء، تكون الواجهة والـAPI على النطاق نفسه؛ اترك `window.CYBERLIFE_API_BASE` فارغًا في `frontend/config.js`، وستستخدم الواجهة المسارات النسبية مثل `/api/health` و`/api/auth/me`. لا تضع `/api` في عنوان أساس ولا تستخدم `localhost`.

## مانع التشغيل الحالي في Vercel

إعدادات المشروع المرتبطة متضمنة وضع الإنتاج وFirebase وRealtime Database، لكن لا يوجد متغير `CYBERLIFE_FIREBASE_CREDENTIALS_JSON` ولا `CYBERLIFE_FIREBASE_CREDENTIALS_FILE` مُعدّ في إعدادات المشروع التي فُحصت. لذلك لا يمكن للخادم إنشاء Firebase Admin SDK/الوصول إلى RTDB حتى يُضاف اعتماد Service Account الصحيح. لم أضع اعتمادًا وهميًا ولم أغيّر إعدادات الإنتاج.

أضف سرًّا من نوع **Sensitive/Secret** في Vercel Project → Settings → Environment Variables:

- الاسم: `CYBERLIFE_FIREBASE_CREDENTIALS_JSON`
- القيمة: محتوى JSON كامل لـFirebase Service Account للمشروع `hamo-8132e`
- النطاق: Preview أولًا للاختبار؛ لا تضفه إلى Production حتى مراجعة الاختبار والـPR.

لا ترسل هذا المفتاح في المحادثة ولا تحفظه في Git. إذا لم يتوفر Service Account، يمكن بدلًا منه إعداد ملف Secret على المنصة، لكن يلزم أيضًا ضبط `CYBERLIFE_FIREBASE_CREDENTIALS_FILE` على مسار الملف الذي يتيحه Runtime.

## متغيرات الخادم

إعدادات Vercel المعروفة تشمل `CYBERLIFE_ENV=production`، `CYBERLIFE_AUTH_MODE=firebase`، `CYBERLIFE_STORAGE_MODE=firebase`، `CYBERLIFE_SERVE_FRONTEND=false`، وProject ID/Realtime Database URL وCORS origin. احتفظ بها كما هي. لا تنشئ حسابات محلية أو تفتح قواعد RTDB لتجاوز نقص بيانات الاعتماد.

## Firebase

1. تأكد من تفعيل Google وEmail/Password في Firebase Authentication.
2. أضف `cyber-life-wheat.vercel.app` إلى Authorized domains، وأضف نطاق Preview المحدد عند اختباره إذا تطلبت Firebase ذلك.
3. قارن قواعد RTDB المنشورة مع `database/database.rules.json`. القواعد في المستودع تمنع القراءة والكتابة العامة وتجعل الكتابة عبر Backend.
4. لا أستطيع التحقق من الحالة الحية لـFirebase أو نشر القواعد ضمن اختبار محلي.

## البناء والاختبار

من جذر المستودع:

```bash
python scripts/run_tests.py
```

بعد إعداد اعتماد Preview، انشر Preview من الفرع الحالي فقط واختبر:

- `GET /api/health` يرجع `status: ok`.
- `GET /api/auth/me` بلا رمز يرجع 401، وبـFirebase ID Token فعلي يرجع الملف العام.
- Google OAuth، تحديث الصفحة، تسجيل الخروج، وقواعد RTDB.

لا تروّج Preview إلى Production قبل مراجعة المستخدم. لا يوجد عنوان Backend منفصل مطلوب عند تشغيل الـFunction والواجهة على نطاق Vercel نفسه.
