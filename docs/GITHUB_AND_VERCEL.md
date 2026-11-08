# GitHub وVercel — إعداد CYBER LIFE

## GitHub

المستودع هو `mrwanhrby036-maker/CYBER-LIFE`. التغييرات في فرع عمل مستقل، ولا تُدفع مباشرة إلى `main`. أداة الرفع (إن استخدمت محليًا) ترفض `main/master`:

```bash
python scripts/push_to_github.py
```

## Vercel

الواجهة على `https://cyber-life-wheat.vercel.app/`. أُضيف في هذا الفرع مدخل Vercel Python Runtime (`api/[...path].py`) لتشغيل تطبيق FastAPI الحالي، مع إبقاء `frontend/` هو مجلد إخراج الملفات الثابتة. مسارات `/api/*` تستخدم نفس النطاق؛ اترك `CYBERLIFE_API_BASE` فارغًا في `frontend/config.js`.

تم إعداد Vercel project مسبقًا بالوضع `production` ومصادقة/تخزين Firebase، وقيمة CORS تشمل أصل الموقع. لكن إعدادات Vercel التي فُحصت لا تحتوي بيانات Service Account اللازمة لـFirebase Admin/RTDB. لذلك لن تعمل نقاط الحساب والبيانات حتى يضيف مالك المشروع السر `CYBERLIFE_FIREBASE_CREDENTIALS_JSON` من Vercel Project Settings → Environment Variables. أضفه إلى **Preview** أولًا فقط؛ لا تضعه في Git ولا في المحادثة ولا في إعدادات الواجهة.

## خطوات تحقق Preview

1. أضف Service Account JSON كسِرّ في Preview Environment Variables.
2. انشر Preview من فرع العمل لا من `main`.
3. اختبر `/api/health`، وCORS/`/api/auth/me`، ثم Google Auth واستعادة الجلسة وRealtime Database.
4. راجع النتائج قبل ترقية أي Deployment إلى Production.

تفاصيل متغيرات Vercel وFirebase في [DEPLOYMENT.md](DEPLOYMENT.md). لا تروّج هذا الفرع للإنتاج تلقائيًا.
