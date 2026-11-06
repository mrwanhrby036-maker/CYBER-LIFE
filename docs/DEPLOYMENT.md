# النشر

> لا توجد مفاتيح حقيقية في المستودع. اتبع الخطوات واملأ القيم من مشروع Firebase الخاص بك `hamo-8132e`.

## 1) Firebase (المشروع القائم)

1. من Firebase Console → Project settings → Your apps → Web app، انسخ `firebaseConfig`.
2. ضع القيم في `frontend/js/auth-firebase-config.js` (الحقول الفارغة حاليًا). لا تخترع قيمًا.
3. فعّل Authentication → Sign-in method → Email/Password و Google.
4. أنشئ Realtime Database (ليس Firestore) وانسخ `databaseURL`.
5. أنشئ Service account key (JSON) من Project settings → Service accounts. احفظه خارج Git.
6. انشر القواعد:
   ```bash
   firebase login
   firebase deploy --only database --project hamo-8132e
   ```
7. ضع UID الأدمن الأول في `CYBERLIFE_ADMIN_UIDS`.

## 2) الخادم الخلفي (ASGI منفصل، ليس Render Free)

خيارات: Fly.io، Railway مدفوع، DigitalOcean App Platform، VPS، أو أي مضيف يدعم Docker/ASGI.

### Docker

```bash
docker build -f backend/Dockerfile -t cyberlife-api .
docker run -p 8000:8000 --env-file backend/.env cyberlife-api
```

### متغيرات البيئة (`backend/.env`)

انسخ `backend/.env.example` إلى `backend/.env` واملأ:

```
CYBERLIFE_ENV=production
CYBERLIFE_AUTH_MODE=firebase
CYBERLIFE_STORAGE_MODE=firebase
CYBERLIFE_SERVE_FRONTEND=false
CYBERLIFE_FIREBASE_PROJECT_ID=hamo-8132e
CYBERLIFE_FIREBASE_DATABASE_URL=https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app
CYBERLIFE_FIREBASE_CREDENTIALS_FILE=/run/secrets/firebase.json
CYBERLIFE_ADMIN_UIDS=<uid>
CYBERLIFE_CORS_ORIGINS=https://<your-vercel-app>.vercel.app
```

> `databaseURL` أعلاه مثال شائع؛ استخدم القيمة الفعلية من Console (قد تكون منطقة مختلفة).

شغّل: `uvicorn app.main:app --host 0.0.0.0 --port 8000` خلف HTTPS (reverse proxy أو المنصة).

## 3) الواجهة على Vercel

1. اربط المستودع بـ Vercel. الإعدادات في `vercel.json` تجعل `frontend` هو مجلد الإخراج.
2. عدّل `frontend/config.js`:
   ```js
   window.CYBERLIFE_API_BASE = 'https://api.your-domain.com';
   ```
3. عدّل `frontend/js/auth-firebase-config.js` بقيم Web App.
4. انشر. تأكد أن أصل Vercel مضاف في `CYBERLIFE_CORS_ORIGINS`.

## 4) التحقق بعد النشر

- `GET https://api.../api/health` → `auth: firebase`, `storage: firebase`.
- تسجيل دخول Google من الواجهة.
- إنشاء فريق، إكمال درس، استلام مهمة.
- محاولة كتابة مباشرة إلى RTDB من العميل يجب أن تُرفض.

## 5) المعاينة المعزولة (Sandbox)

لتشغيل المعاينة على منفذ 8000:

```bash
./scripts/serve_preview.sh
```

- يولّد بيانات دخول **مؤقتة عشوائية** أول مرة ويحفظها في `backend/.data/preview-credentials.json` (مستثنى من Git).
- لا تُعرض أي بيانات دخول في الواجهة.
- احذف الملف لتدوير البيانات، واحذف `backend/.data/database.json` لتصفير البيانات.
- **هذا ليس الإنتاج**: الإنتاج يتطلب `CYBERLIFE_ENV=production` مع Firebase.

## 5) التطوير المحلي

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # اترك auth/storage=local
uvicorn app.main:app --reload --port 8000
```

لا توجد حسابات دخول افتراضية معروضة. استخدم Firebase Authentication. وضع الاختبار المحلي معطل افتراضياً ومخصص للاختبارات المعزولة فقط.
