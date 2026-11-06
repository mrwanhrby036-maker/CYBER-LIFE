# إعداد Firebase — الخطوات المطلوبة منك

كل حاجة في المشروع جاهزة. ناقص **٦ قيم** من حسابك، ومش هقدر أخترعها.

المشروع القائم: `hamo-8132e`

---

## الجزء الأول: إعدادات الواجهة (٥ قيم)

### من فين؟

1. افتح https://console.firebase.google.com
2. اختار مشروع **hamo-8132e**
3. اضغط ⚙️ → **Project settings**
4. انزل لقسم **Your apps** → اختار تطبيق الويب (`</>`)
5. هتلاقي كود شكله كده:

```js
const firebaseConfig = {
  apiKey: "AIzaSy.....................",
  authDomain: "hamo-8132e.firebaseapp.com",
  projectId: "hamo-8132e",
  storageBucket: "hamo-8132e.firebasestorage.app",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abc123def456",
  measurementId: "G-XXXXXXXXXX"
};
```

### فين تحطها؟

افتح `frontend/js/auth-firebase-config.js` واملأ القيم:

| الحقل | مطلوب؟ | ملاحظة |
|---|---|---|
| `apiKey` | ✅ لازم | مفتاح الويب العام |
| `authDomain` | ✅ لازم | غالبًا `hamo-8132e.firebaseapp.com` |
| `projectId` | ✅ لازم | `hamo-8132e` |
| `appId` | ✅ لازم | شكله `1:...:web:...` |
| `databaseURL` | ✅ لازم | من خطوة Realtime Database تحت |
| `storageBucket` | اختياري | مش مستخدم |
| `messagingSenderId` | اختياري | مش مستخدم |

> **مهم:** القيم دي **عامة** بطبيعتها (أي حد يفتح الموقع يشوفها). الحماية الحقيقية من قواعد قاعدة البيانات + تحقق الخادم. **ممنوع** تحط مفتاح Admin SDK هنا.

---

## الجزء الثاني: تفعيل طرق الدخول

Firebase Console → **Authentication** → **Sign-in method**:

- ✅ فعّل **Email/Password**
- ✅ فعّل **Google** (اختار بريد الدعم)

---

## الجزء الثالث: Realtime Database

> ⚠️ **Realtime Database** وليس Firestore. لو اخترت Firestore بالغلط، المنصة مش هتشتغل.

1. Firebase Console → **Build** → **Realtime Database**
2. **Create Database** → اختار المنطقة
3. ابدأ بـ **Locked mode** (هننشر قواعدنا)
4. انسخ العنوان اللي يظهر، شكله:
   ```
   https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app
   ```
   أو حسب المنطقة:
   ```
   https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app
   ```
5. حطّه في `databaseURL` في ملف الواجهة **وفي** `backend/.env`

### نشر القواعد

```bash
npm install -g firebase-tools
firebase login
cd CYBER-LIFE
firebase deploy --only database --project hamo-8132e
```

---

## الجزء الرابع: مفتاح الخادم (سرّي)

1. ⚙️ **Project settings** → تبويب **Service accounts**
2. **Generate new private key** → نزّل ملف JSON
3. سمّيه `firebase-service-account.json`
4. حطّه **خارج مجلد المشروع** (مثلاً `~/secrets/`)

> 🔒 **السر ده خطير**: يدي صلاحية كاملة على القاعدة. ممنوع يترفع على GitHub، وممنوع يحط في الواجهة. `.gitignore` بيمنعه تلقائيًا.

---

## الجزء الخامس: ملف إعدادات الخادم

انسخ `backend/.env.example` إلى `backend/.env` واملأ:

```env
CYBERLIFE_ENV=production
CYBERLIFE_AUTH_MODE=firebase
CYBERLIFE_STORAGE_MODE=firebase
CYBERLIFE_SERVE_FRONTEND=false

CYBERLIFE_FIREBASE_PROJECT_ID=hamo-8132e
CYBERLIFE_FIREBASE_DATABASE_URL=https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app
CYBERLIFE_FIREBASE_CREDENTIALS_FILE=/home/youruser/secrets/firebase-service-account.json

CYBERLIFE_ADMIN_UIDS=(uid بتاعك من الخطوة الجاية)
CYBERLIFE_CORS_ORIGINS=https://cyber-life.vercel.app
```

---

## الجزء السادس: تعيين الأدمن

1. سجّل دخول على المنصة بحسابك (بعد النشر)
2. Firebase Console → **Authentication** → **Users**
3. انسخ **User UID** بتاعك
4. حطّه في `CYBERLIFE_ADMIN_UIDS` وأعد تشغيل الخادم

> الأدمن بيتحدد بالـ **UID** مش بالبريد، لأن البريد ممكن يتزوّر لو مش متحقق منه.

---

## ملخص: اللي محتاجه منك

| # | القيمة | مكانها |
|---|---|---|
| 1 | `apiKey` | الواجهة |
| 2 | `appId` | الواجهة |
| 3 | `databaseURL` | الواجهة + الخادم |
| 4 | ملف service account | الخادم (سرّي، خارج Git) |
| 5 | `ADMIN_UID` | الخادم |
| 6 | تفعيل Email/Password + Google | Console |

**ابعتلي القيم ١ و ٢ و ٣ وأنا أكمل الباقي.**
الملف السرّي (رقم ٤) **متبعتهوش في الشات** — حطّه على جهازك أو في مدير أسرار الاستضافة.

---

## بعد ما تديني القيم

1. أعمّر ملف الواجهة
2. أختبر إن الدخول شغال فعلًا
3. أرفع على GitHub
4. أربط Vercel ينشر تلقائي
5. أديك رابط شغال
