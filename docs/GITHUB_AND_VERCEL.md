# رفع المشروع على GitHub + Vercel

الترتيب الصح: **Firebase ← GitHub ← Vercel ← الخادم**.
السبب: لو رفعت قبل Firebase، الموقع هيفتح بس الدخول مش هيشتغل.

---

## الخطوة ١: ظبّط Firebase الأول

اتبع [FIREBASE_SETUP.md](FIREBASE_SETUP.md) وخلّص القيم المطلوبة.

---

## الخطوة ٢: GitHub

أنا مش قادر أعمل الـ repo بنفسي (ربط GitHub مش متاح في المحادثة)، فالخطوة دي منك.

### أ) اعمل الـ repo

1. افتح https://github.com/new
2. الاسم: `cyber-life`
3. اختار **Private** (أأمن لمشروع فيه إعدادات)
4. **متعلمش** على "Add a README" ولا ".gitignore" — المشروع فيه الاتنين
5. **Create repository**

### ب) ارفع الملفات

الملفات جاهزة ومتعملة كـ commit محلي. من داخل مجلد المشروع:

```bash
cd CYBER-LIFE
git remote add origin https://github.com/<اسمك>/cyber-life.git
git branch -M main
git push -u origin main
```

لو Git طلب كلمة مرور، استخدم **Personal Access Token** مش كلمة مرور الحساب:
GitHub → Settings → Developer settings → Personal access tokens → Generate (صلاحية `repo`).

### ج) اتأكد إن مفيش أسرار اترفعت

```bash
git ls-files | grep -E "\.env$|service-account|\.data/|credentials"
```

المفروض الناتج **فاضي**. لو طلع أي حاجة، متكمّلش — قوللي.

---

## الخطوة ٣: Vercel

### الطريقة الأفضل: الربط بـ GitHub (نشر تلقائي)

1. افتح https://vercel.com/new
2. **Import Git Repository** → اختار `cyber-life`
3. الإعدادات:

| الحقل | القيمة |
|---|---|
| Framework Preset | **Other** |
| Root Directory | `frontend` |
| Build Command | (فاضي) |
| Output Directory | (فاضي — Root هو frontend) |

4. **Deploy**

بعد كده أي `git push` هينشر تلقائيًا.

> لو استخدمت Root Directory = `frontend`، فإن `vercel.json` الموجود في الجذر مش هيتقرأ.
> البديل: سيب Root Directory فاضي، و`vercel.json` هيتولى تحديد `frontend` كمجلد الإخراج.
> **الأسهل: سيب Root Directory فاضي واعتمد على `vercel.json`.**

### متغير البيئة المطلوب

في Vercel → Project → Settings → Environment Variables ضيف:

| Key | Value |
|---|---|
| `CYBERLIFE_API_BASE` | عنوان الخادم الخلفي (الخطوة ٤) |

وبعدين عدّل `frontend/config.js` عشان يقراه، أو حدّده مباشرة:

```js
window.CYBERLIFE_API_BASE = 'https://api.your-domain.com';
```

---

## الخطوة ٤: الخادم الخلفي (منفصل)

Vercel **مش هيشغّل** FastAPI بشكل دائم — هو للواجهات والدوال القصيرة.
الخادم محتاج استضافة تشغّل عملية مستمرة.

اختار واحدة (كلها مدفوعة أو بحدود معقولة، وتجنب Render Free لأنه بينام):

| المنصة | ملاحظة |
|---|---|
| **Railway** | أسهل، Docker جاهز |
| **Fly.io** | تحكم أكبر، Docker جاهز |
| **DigitalOcean App Platform** | مستقر |
| **VPS** (Hetzner/Contabo) | أرخص على المدى الطويل |

### الأوامر

```bash
docker build -f backend/Dockerfile -t cyberlife-api .
docker run -p 8000:8000 --env-file backend/.env \
  -v ~/secrets:/run/secrets:ro cyberlife-api
```

### متغيرات البيئة على الاستضافة

انسخ من `backend/.env.example` واملأ القيم الحقيقية.
ملف service account ارفعه كـ **Secret File** مش كنص عادي.

---

## الخطوة ٥: اربط الاتنين

1. في الخادم: `CYBERLIFE_CORS_ORIGINS=https://<موقعك>.vercel.app`
2. في الواجهة: `window.CYBERLIFE_API_BASE = 'https://<خادمك>'`
3. في Firebase → Authentication → Settings → **Authorized domains**: ضيف دومين Vercel

---

## الخطوة ٦: تحقق إن كل حاجة شغالة

| الفحص | المتوقع |
|---|---|
| `GET https://<خادمك>/api/health` | `status: ok` |
| `GET https://<خادمك>/api/health/ready` | `content_seeded: true` |
| فتح الموقع | الصفحة الرئيسية التعريفية |
| الدخول بـ Google | يوديك للوحة الطالب |
| إنشاء فريق | ينجح مرة واحدة |
| إكمال درس | التقدم يتحفظ |
| محاولة كتابة مباشرة على RTDB | تُرفض |

---

## ليه GitHub أفضل من الرفع المباشر؟

| | رفع مباشر لـ Vercel | GitHub + Vercel |
|---|---|---|
| السرعة | أسرع مرة واحدة | يحتاج إعداد أول مرة |
| تاريخ التعديلات | ❌ | ✅ |
| الرجوع لنسخة سابقة | ❌ | ✅ |
| نشر تلقائي مع كل تعديل | ❌ | ✅ |
| نسخة احتياطية للكود | ❌ | ✅ |
| معاينة قبل النشر | ❌ | ✅ (لكل branch) |

**الخلاصة:** الرفع المباشر ينفع لتجربة سريعة. لمشروع طويل زي ده، **GitHub + Vercel** هو الصح.


---

# حالة النشر الفعلية (2026-11-06)

## تم إنشاؤه

| البند | القيمة |
|---|---|
| مستودع GitHub | `mrwanhrby036-maker/CYBER-LIFE` |
| مشروع Vercel | `cyber-life` |
| معرّف المشروع | `prj_HBZaSG0XDkrIsx8tjd831YFqvfRE` |
| الفريق | `team_jMxwyvBgLjtibR3BByJfM3u5` |
| فرع الإنتاج | `main` |
| مجلد الإخراج | `frontend` |
| أمر البناء | لا شيء (موقع ثابت) |
| الربط بـ GitHub | ✅ تم |

## ⚠️ المستودع فارغ

تم فحص المستودع مرتين (GitHub API + `git ls-remote`) — **لا يوجد به أي ملف**.
لا يمكن النشر قبل رفع الملفات.

للرفع: شغّل `scripts/push_to_github.ps1` على Windows،
أو `scripts/push_to_github.sh` على Mac/Linux،
أو اسحب الملفات إلى صفحة المستودع في المتصفح.

## ⚠️ النشر التلقائي معطّل

عند إنشاء المشروع عبر واجهة البرمجة، جاء الإعداد:

```
gitProviderOptions.createDeployments = "disabled"
```

معناه أن الرفع إلى GitHub **لن** ينشر تلقائيًا.

الحل: إما تشغيل النشر يدويًا عبر المساعد بعد كل رفع،
أو تفعيله من لوحة Vercel:
**Project → Settings → Git → Automatically deploy** (إن كان الخيار متاحًا لخطة Hobby).

## ⚠️ حماية المعاينة مفعّلة

```
ssoProtection.deploymentType = "all_except_custom_domains"
```

معناه أن روابط النشر تطلب تسجيل الدخول إلى Vercel قبل العرض.
هذا يمنع الزوار العاديين من رؤية الموقع، ويكسر تسجيل الدخول بـ Firebase.

الحل من لوحة Vercel:
**Project → Settings → Deployment Protection → Vercel Authentication → Disabled**

هذه الخطوة ضرورية قبل اختبار الدخول.

## الخطوة التالية بعد النشر

أضف نطاق الموقع إلى Firebase:
**Authentication → Settings → Authorized domains → Add domain**

النطاقات المصرّح لها حاليًا لا تتضمن أي نطاق لـ CYBER LIFE.
