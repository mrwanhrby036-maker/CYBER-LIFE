# حالة التنفيذ — CYBER LIFE

**التاريخ:** 2026-11-08

## المشروع والوظائف

المشروع الأصلي محفوظ: 12 صفحة عربية RTL، المنهج والمختبرات والمهمات والفرق والتقارير والإنجازات ولوحة الإدارة. لا تستبدل الواجهة أو المحتوى في هذا التغيير.

## الإصلاحات المنفذة في هذه الجولة

- إصلاح إدارة Firebase Auth: تهيئة أحادية تمنع تكرار Firebase app، Google popup، حفظ Firebase persistence صراحة، واستعادة Firebase user وتجديد ID token بعد تحديث الصفحة.
- اعتماد نجاح الدخول فقط بعد استرجاع الملف من `GET /api/auth/me`. عند انقطاع Backend تظل جلسة Firebase محفوظة وتظهر إعادة محاولة بدل مطالبة المستخدم بتسجيل الدخول مرة أخرى.
- معالجة الخروج بإغلاق جلسة Firebase ومسح token/cache محليًا. أخطاء الشبكة/الخادم لا تمحو جلسة صالحة.
- إضافة اختبار لوحدة استعادة الجلسة من دون ادعاء اختبار Firebase حي.
- إصلاح تسريب `password_hash` وحقول غير عامة من رد `/api/auth/me`، مع ملف عام بقائمة حقول مسموحة.
- توثيق سبب عدم عمل API على Vercel: `vercel.json` ينشر `frontend/` فقط، و`frontend/config.js` لا يحدد Backend، ولا يوجد Python Function أو proxy route.
- تحديث تعليمات Firebase/Backend وCORS، والتنبيه إلى أن قواعد RTDB المنشورة وإعداد Firebase الحي يجب التحقق منها يدويًا.
- تحويل سكريبتات الاختبار والمعاينة والرفع من Bash/PowerShell إلى Python. أداة الرفع الجديدة لا تعيد تسمية الفرع ولا تدفع `main/master`.

## الاختبارات

- Backend: 52 اختبارًا ناجحًا.
- Frontend: 20 اختبارًا ناجحًا.
- صياغة JavaScript وPython compileall: ناجحة.
- المجموع: 72 اختبارًا ناجحًا، 0 فاشلة.
- التفاصيل: `docs/TEST_REPORT.md`.

## ما لم يكتمل قبل الإنتاج

- إعداد Vercel static الحالي لا يحتوي عنوان Backend. يجب اختيار مضيف ASGI/Docker ثم وضع عنوان HTTPS الحقيقي في `frontend/config.js`.
- إعداد secrets في استضافة Backend: service account، `CYBERLIFE_*` وCORS origin الدقيق.
- التحقق الحي من Google provider، Authorized domains، نشر قواعد RTDB واتصال قاعدة البيانات.
- اختبار Google OAuth وFirebase ID Token وRealtime Database end-to-end على نطاقات الإنتاج.

لم يتم نشر أي تغيير على Vercel أو Firebase أو أي Backend. لا تعتبر بوابة تسجيل الدخول متكاملة للإنتاج حتى تكتمل الخطوات في `docs/DEPLOYMENT.md` وينجح اختبار المتصفح الحي.
