# النشر والتكامل

## تشخيص البنية الحالية

- `vercel.json` ينشر محتويات `frontend/` كملفات ثابتة فقط؛ لا يعرّف دوال Python أو rewrite إلى FastAPI.
- `frontend/config.js` لا يحتوي عنوان Backend، لذلك يطلب المتصفح `/api/...` على نفس نطاق Vercel. هذا يعمل فقط إذا كان FastAPI على النطاق نفسه، وهو غير مُعدّ في هذا المستودع.
- لا يوجد عنوان استضافة Backend فعلي في الملفات؛ لا تضع عنوانًا تخمينيًا. يجب اختيار مضيف يدعم Docker/ASGI أولًا.
- إعدادات Firebase Web العامة الحالية موجودة في `frontend/js/auth-firebase-config.js`. مفاتيح Web ليست أسرارًا؛ لا تضع بيانات Service Account في الواجهة.

## 1) Firebase

1. في Firebase Console للمشروع `hamo-8132e`، تحقق من تفعيل Authentication → Sign-in method → Google. البريد وكلمة المرور مستخدمان أيضًا في واجهة الدخول.
2. أضف نطاق الإنتاج الفعلي `cyber-life-wheat.vercel.app` وأي نطاق إنتاج مخصص إلى Authentication → Settings → Authorized domains. أضف Preview domains عند الحاجة، ولا تضف نطاقات لا تثق بها.
3. تحقق أن Realtime Database تستخدم عنوان `https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app` وأن قواعدها المنشورة مطابقة لـ `database/database.rules.json`.
4. القواعد في المستودع تمنع القراءة والكتابة العامة، وتجعل الكتابة من الخادم فقط. شغّل النشر يدويًا بعد مراجعتها:
   ```bash
   firebase deploy --only database --project hamo-8132e
   ```
5. أنشئ Service Account للخادم فقط. خزّن JSON في Secret Manager أو ملف سر خارج Git.

> توجد في `docs/FIREBASE_VERIFIED.md` ملاحظات تحقق سابقة، لكنها لا تثبت أن إعدادات Firebase أو القواعد الحالية ما زالت منشورة. لا يمكن إعادة التحقق الحي من Firebase ضمن هذا التغيير.

## 2) استضافة Backend مستقلة

FastAPI يحتاج مضيفًا يدعم Docker/ASGI (مثل VPS أو خدمة حاويات/ASGI). لا يقوم إعداد Vercel الحالي بتشغيل هذا Backend تلقائيًا. بعد اختيار المضيف، اربط له نطاق HTTPS حقيقي، مثل `api.<your-domain>`؛ هذا مثال شكلي فقط وليس عنوانًا موجودًا.

ابنِ الحاوية من جذر المستودع:

```bash
docker build -f backend/Dockerfile -t cyberlife-api .
```

اضبط أسرار وبيئة الخادم في لوحة المضيف، على الأقل:

```text
CYBERLIFE_ENV=production
CYBERLIFE_AUTH_MODE=firebase
CYBERLIFE_STORAGE_MODE=firebase
CYBERLIFE_SERVE_FRONTEND=false
CYBERLIFE_FIREBASE_PROJECT_ID=hamo-8132e
CYBERLIFE_FIREBASE_DATABASE_URL=https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app
CYBERLIFE_FIREBASE_CREDENTIALS_JSON=<secret JSON from secret manager>
CYBERLIFE_CORS_ORIGINS=https://cyber-life-wheat.vercel.app
CYBERLIFE_ADMIN_UIDS=<trusted Firebase Auth UID(s), optional>
```

استخدم `CYBERLIFE_FIREBASE_CREDENTIALS_FILE` بدلًا من `..._JSON` إذا وفر المضيف ملف Secret. لا تحفظ السر في Git ولا في إعدادات Vercel frontend. سيشترط إعداد الإنتاج Firebase Auth وRTDB وعناوين CORS HTTPS صريحة.

يجب أن ينجح `GET https://<actual-backend-host>/api/health` وأن يرجع `{ "status": "ok", ... }`. نقطة الحساب هي `GET /api/auth/me` مع `Authorization: Bearer <Firebase ID token>`؛ يتحقق الخادم من الرمز، ينشئ ملف المستخدم للمرة الأولى، ثم يرجع ملفًا عامًا ودور المستخدم. لا تستخدم مسارات `localhost` في إعداد الإنتاج.

## 3) ربط واجهة Vercel

بعد اختيار عنوان Backend الحقيقي:

1. ضع عنوان HTTPS الجذري (من دون `/api`) في `frontend/config.js`:
   ```js
   window.CYBERLIFE_API_BASE = 'https://<actual-backend-host>';
   ```
2. أعد نشر واجهة Vercel بعد ضبط العنوان. هذا ملف إعداد عام مرئي للمتصفح، لذلك لا تضع أي سر فيه.
3. تأكد أن `CYBERLIFE_CORS_ORIGINS` في Backend يحتوي أصل Vercel الدقيق، بلا wildcard. إذا كانت هناك معاينات Vercel، أضف نطاقات محددة موثوقة فقط أو اترك المعاينات خارج CORS.
4. افحص في أدوات المتصفح أن الطلبين التاليين يذهبان إلى Backend الحقيقي لا إلى Vercel ولا إلى `localhost`:
   - `GET /api/health`
   - `GET /api/auth/me` بعد OAuth، مع رأس Authorization.

إذا كان Backend وواجهة الموقع على النطاق نفسه ويقدّم الخادم FastAPI تلك الملفات، اترك `CYBERLIFE_API_BASE` فارغًا؛ عندها تكون المسارات النسبية مقصودة. هذا ليس وضع النشر الحالي على Vercel.

## 4) قائمة التحقق قبل الإنتاج

- Google provider مفعّل والنطاق مصرح به في Firebase Auth.
- قواعد RTDB المنشورة ومراجعة؛ لا تستخدم قواعد عامة.
- Backend مستقل متاح عبر HTTPS، وأسرار Firebase على الخادم فقط.
- `CYBERLIFE_API_BASE` يشير إلى Backend الحقيقي، وCORS يطابق أصل Vercel.
- اختبر OAuth الفعلي، عودة المستخدم إلى المنصة، تحديث الصفحة، قراءة الملف، وتسجيل الخروج قبل نشر أي إصدار إنتاجي.
- لا توجد في هذا التغيير عملية نشر إلى Firebase أو Vercel أو مضيف Backend.
