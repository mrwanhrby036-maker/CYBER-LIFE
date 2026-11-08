# إعداد Firebase المطلوب قبل الإنتاج

تطبيق الويب الحالي مضبوط في `frontend/js/auth-firebase-config.js` على المشروع `hamo-8132e`. إعدادات الويب العامة ليست أسرارًا؛ لا تستبدلها إلا إذا أكد Firebase Console أن التطبيق/المشروع تغيّر. لا تضع Service Account في JavaScript.

## Authentication

1. في Firebase Console اختر المشروع `hamo-8132e`.
2. Authentication → Sign-in method: فعّل Google، وكذلك Email/Password ما دامت هذه الطريقة ظاهرة في الواجهة.
3. Authentication → Settings → Authorized domains: أضف `cyber-life-wheat.vercel.app` وأي نطاق مخصص مستخدم للإنتاج. أضف Preview domain محددًا عند الحاجة فقط.
4. اختبر `signInWithPopup` من النطاق المنشور بعد تفعيله؛ الاختبارات المحلية لا تستطيع إثبات تهيئة Firebase الحية أو صلاحية Google OAuth في المتصفح.

## Realtime Database

- يستخدم Backend Realtime Database، وليس Firestore.
- عنوان المشروع المضبوط: `https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app`؛ طابقه مع القيمة الظاهرة في Firebase Console.
- القواعد المحفوظة في `database/database.rules.json` تمنع القراءة والكتابة العامة، وتسمح بقراءة بيانات المستخدم لصاحب UID/أدمن محدد، وتجعل الكتابة عبر الخادم فقط.
- بعد مراجعة القواعد انشرها يدويًا:
  ```bash
  firebase deploy --only database --project hamo-8132e
  ```
  لا تفتح القواعد للعامة عند ظهور خطأ صلاحيات.

## Backend credentials

1. أنشئ Service Account للمشروع من Firebase Project settings → Service accounts.
2. وفر بياناته للخادم عبر Secret Manager أو `CYBERLIFE_FIREBASE_CREDENTIALS_FILE`، أو المتغير السري `CYBERLIFE_FIREBASE_CREDENTIALS_JSON`.
3. لا ترفع ملف Service Account، ولا تضعه في إعدادات Vercel frontend أو المحادثة.
4. عيّن `CYBERLIFE_ADMIN_UIDS` على الخادم بمعرف UID موثوق فقط، عند الحاجة لمنح الدور الإداري.

## ما يلزم للموقع

الإعداد الحالي على Vercel ملفات ثابتة ولا يوجد Backend منشور/عنوان API في المستودع. قبل اعتبار Firebase login مكتملًا يجب أيضًا استضافة FastAPI مستقلًا، وضع عنوان HTTPS الفعلي في `frontend/config.js`، وضبط `CYBERLIFE_CORS_ORIGINS` على أصل Vercel الدقيق. الخطوات في [DEPLOYMENT.md](DEPLOYMENT.md).

ملاحظات الفحص الحي السابقة في `FIREBASE_VERIFIED.md` تاريخية فقط وليست إثباتًا للحالة الحالية أو لاختبار OAuth end-to-end.
