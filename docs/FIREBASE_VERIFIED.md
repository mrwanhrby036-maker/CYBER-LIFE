# ملاحظات تحقق Firebase سابقة (ليست فحصًا حيًا حاليًا)

تحتوي هذه الصفحة على نتائج مكتوبة في 2026-11-06. لا تمثل إعادة تحقق ضمن التغيير الحالي، ولا تثبت أن إعدادات Firebase أو قواعد RTDB ما زالت منشورة أو أن دخول Google يعمل end-to-end على الموقع الآن.

## الإعدادات العامة المسجلة في المشروع

| الحقل | القيمة المسجلة |
|---|---|
| `projectId` | `hamo-8132e` |
| `authDomain` | `hamo-8132e.firebaseapp.com` |
| `databaseURL` | `https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app` |
| `storageBucket` | `hamo-8132e.firebasestorage.app` |
| `messagingSenderId` | `791335303883` |
| `appId` | `1:791335303883:web:637e0d0b7d09aac2b4b94e` |

هذه القيم موجودة في `frontend/js/auth-firebase-config.js`، وWeb API key/app ID إعدادات عمومية وليست بيانات اعتماد Admin.

## ملاحظات تاريخية يجب إعادة فحصها في Console

- ذُكر في الفحص السابق أن Authentication وRealtime Database تستجيبان؛ لا يمكنني تأكيد إعداداتهما الحالية من اختبارات المستودع.
- أشار التقرير السابق إلى أن `cyber-life-wheat.vercel.app` لم يكن ضمن Authorized domains. تحقق من ذلك وأضفه إذا كان لا يزال غائبًا.
- قواعد RTDB المنشورة لا يمكن استنتاجها من ملف المستودع؛ قارنها مع `database/database.rules.json` وانشرها يدويًا بعد المراجعة.
- لم يكن Backend منفصلًا مسجلًا؛ إعداد Vercel الحالي ينشر الملفات الثابتة فقط.

## خطوات التحقق المطلوبة قبل الإنتاج

1. Authentication → Sign-in method: تأكد من تمكين Google وEmail/Password.
2. Authentication → Settings → Authorized domains: تحقق من النطاق المنشور الفعلي.
3. Realtime Database → Rules: تحقق أن القواعد ليست عامة وأنها تطابق الملف في المستودع.
4. اختبر Google OAuth من Vercel، ثم تأكد من استدعاء `GET /api/auth/me` عبر Backend الحقيقي بعد المصادقة.
5. راجع [DEPLOYMENT.md](DEPLOYMENT.md) لإعداد Backend وCORS.
