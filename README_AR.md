# CYBER LIFE — منصة تعلم الأمن السيبراني بالعربية

منصة تعليمية عملية مستوحاة من فكرة الشركة الافتراضية: الطالب يعمل داخل شركة أمن سيبراني خيالية، يتعلم، يحقق، يتخذ قرارات، ويكتب تقارير.

## الصفحة الرئيسية

الواجهة تبدأ بصفحة رئيسية تعريفية بالمنصة وخدماتها وفريقها، ثم الانتقال إلى تسجيل الدخول عند الرغبة في بدء التدريب.

## التشغيل الحقيقي

الإنتاج يعتمد على Firebase Authentication وFirebase Realtime Database. إعداد Vercel في هذا الفرع يشغّل الواجهة الثابتة وFastAPI Python على النطاق نفسه؛ يلزم إضافة Firebase Service Account كسرّ في Vercel قبل أن تعمل البيانات.

راجع [دليل النشر](docs/DEPLOYMENT.md) لمعرفة متغير Vercel المطلوب واختبار Preview قبل Production.

## الاختبارات

```bash
python scripts/run_tests.py
```

الاختبارات تستخدم بيئة معزلة خاصة بالاختبار فقط، ولا تمثل بيانات الإنتاج.

## البنية

كل مجلد يحتوي ملفات مسطحة، واسم الملف يقول وظيفته مباشرة:

- `frontend/`: الصفحات، وداخلها `js/` و`css/` و`assets/` بشكل مسطح.
- `backend/app/`: كل ملفات الخادم مسطحة ببادئات `route_` و`service_` و`db_`.
- `content/`: ملفات المنهج والمهام والمختبر مباشرة بدون مجلدات فرعية.
- `database/`: قواعد وبنية Realtime Database.
- `docs/`: التوثيق الكامل.
- `tests-frontend/`: اختبارات الواجهة.
- `scripts/`: أدوات التشغيل والعدّ ومعالجة الصور.

**ابدأ بـ [خريطة الملفات](docs/FILE_MAP.md)** — جدول يقول لك وظيفة كل ملف وأي ملف تفتح لكل تعديل.

## التوثيق

- [خريطة الملفات](docs/FILE_MAP.md)
- [المعمارية](docs/ARCHITECTURE.md)
- [API](docs/API.md)
- [الأمان](docs/SECURITY.md)
- [إعداد Firebase](docs/FIREBASE_SETUP.md)
- [نتيجة فحص Firebase](docs/FIREBASE_VERIFIED.md)
- [GitHub و Vercel](docs/GITHUB_AND_VERCEL.md)
- [النشر](docs/DEPLOYMENT.md)
- [الاختبارات](docs/TESTING.md)
- [حالة التنفيذ](docs/IMPLEMENTATION_STATUS.md)
- [قاعدة البيانات](database/DATABASE_DOCUMENTATION.md)

## ملاحظة أمنية

لا توجد حسابات افتراضية معروضة في واجهة الدخول. تسجيل الدخول الحقيقي يتم عبر Firebase، والصلاحيات تتحدد من الخادم.
