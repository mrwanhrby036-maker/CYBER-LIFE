# تم التحقق من إعدادات Firebase فعليًا

**التاريخ:** 2026-11-06
**المشروع الحقيقي:** `hamo-8132e` ← لاحظ حرف **e** في الآخر

> كان المشروع مفترضًا `hamo-8132` بدون e. تم تصحيحه في كل الملفات.

---

## الإعدادات المُركّبة

| الحقل | القيمة |
|---|---|
| `projectId` | `hamo-8132e` |
| `authDomain` | `hamo-8132e.firebaseapp.com` |
| `databaseURL` | `https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app` |
| `storageBucket` | `hamo-8132e.firebasestorage.app` |
| `messagingSenderId` | `791335303883` |
| `appId` | `1:791335303883:web:637e0d0b7d09aac2b4b94e` |
| المنطقة | **europe-west1** (بلجيكا) |

مكانها: `frontend/js/auth-firebase-config.js`

---

## نتائج الفحص الحي

| الفحص | الطريقة | النتيجة |
|---|---|---|
| القاعدة موجودة؟ | `GET /.json` بدون مصادقة | **401 Permission denied** ✅ موجود ومحمي |
| المفتاح صالح؟ | `GET /v1/projects?key=` | **200** ✅ |
| Email/Password مفعّل؟ | محاولة دخول ببريد غير موجود | `INVALID_LOGIN_CREDENTIALS` ✅ مفعّل |
| Google مفعّل؟ | محاولة برمز مزيّف | `INVALID_IDP_RESPONSE` ✅ مفعّل (رفض الرمز لا الطريقة) |

**كل طرق الدخول جاهزة.** لم يُنشأ أي حساب أثناء الفحص.

---

## ⚠️ خطوة ناقصة: Authorized Domains

النطاقات المصرّح لها حاليًا في مشروعك:

```
localhost
hamo-8132e.firebaseapp.com
hamo-8132e.web.app
efootball-drab.vercel.app
arena.ai
```

**نطاق CYBER LIFE الجديد غير موجود.** لازم تضيفه بعد النشر:

1. Firebase Console → **Authentication** → **Settings** → **Authorized domains**
2. **Add domain** → اكتب نطاق Vercel، مثلاً `cyber-life.vercel.app`
3. Save

بدون الخطوة دي، الدخول هيفشل برسالة: «هذا النطاق غير مضاف بعد لإعدادات الدخول».

---

## ⚠️ خطوة ناقصة: نشر قواعد القاعدة

القاعدة الحالية ترفض كل شيء (Locked mode). لازم تنشر قواعد المشروع:

```bash
npm install -g firebase-tools
firebase login
cd CYBER-LIFE
firebase deploy --only database --project hamo-8132e
```

ملف `firebase.json` في الجذر يشير تلقائيًا إلى `database/database.rules.json`.

---

## ⚠️ خطوة ناقصة: الخادم الخلفي

الواجهة جاهزة، لكن الدروس والمهام والتقدم تحتاج الخادم.

ناقص منك:
1. **ملف service account** — من Project settings → Service accounts → Generate new private key
   - ضعه **خارج** مجلد المشروع
   - **لا ترفعه على GitHub ولا تبعته في الشات**
2. **استضافة للخادم** — Railway أو Fly.io أو VPS
3. **UID الأدمن** — بعد أول دخول، من Authentication → Users

التفاصيل: [GITHUB_AND_VERCEL.md](GITHUB_AND_VERCEL.md)

---

## ما يعمل الآن وما لا يعمل

| الميزة | الحالة |
|---|---|
| الصفحة الرئيسية والتصميم | ✅ جاهز |
| إنشاء حساب / دخول بـ Google | ✅ جاهز (بعد إضافة النطاق) |
| إنشاء حساب / دخول بالبريد | ✅ جاهز (بعد إضافة النطاق) |
| الدروس والمهام والتقدم | ⏸ يحتاج الخادم الخلفي |
| لوحة الأدمن | ⏸ يحتاج الخادم + UID |

الواجهة تعرض رسالة واضحة: «المنصة في مرحلة التجهيز» عندما يكون الخادم غير متاح،
بدل أن تفشل بشكل غامض بعد الدخول.

---

## ملاحظة أمنية

`apiKey` و `appId` **قيم عامة** تظهر لأي زائر في المتصفح — هذا تصميم Firebase الطبيعي.
الحماية الحقيقية تأتي من:
1. قواعد Realtime Database (كل الكتابة عبر الخادم فقط)
2. تحقق الخادم من رمز الدخول
3. قائمة Authorized domains

**ممنوع** وضع ملف service account في الواجهة أو في Git.
