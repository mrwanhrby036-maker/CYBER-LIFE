# GitHub وVercel — وضع التكامل

## GitHub

المستودع هو `mrwanhrby036-maker/CYBER-LIFE`. للتعامل من نسخة محلية، استخدم فرع عمل ولا ترفع مباشرة إلى `main`. أداة الرفع المتاحة ترفض الفرع الافتراضي وتدفع الفرع الحالي فقط:

```bash
python scripts/push_to_github.py
```

لا تغير الأداة عنوان `origin` إذا كان مضبوطًا، ولا تعيد تسمية الفرع. افحص التغييرات والاختبارات قبل الرفع أو فتح Pull Request.

## Vercel

إعداد `vercel.json` الحالي ينشر `frontend/` كموقع ثابت، بلا Build Command وبلا Python Function أو Rewrite إلى API. لذلك لا يشغّل Backend تلقائيًا. وجود مشروع Vercel أو نجاح نشر الملفات لا يعني أن مسارات `/api/*` متاحة.

الموقع المنشور المذكور في الإعداد الحالي هو `https://cyber-life-wheat.vercel.app/`. عند النشر، تحقق من إعدادات مشروع Vercel مباشرة؛ أسماء المشاريع والفروع وحماية Preview قد تتغير ولا تُستنتج من هذا المستودع.

## ربط API بعد إنشاء Backend فعلي

1. استضف FastAPI على مضيف مستقل يدعم ASGI/Docker، واربط نطاق HTTPS حقيقي به. لا يوجد عنوان Backend فعلي مسجل في المستودع الآن.
2. عيّن في `frontend/config.js` جذر عنوان Backend الحقيقي، من دون `/api`:
   ```js
   window.CYBERLIFE_API_BASE = 'https://<actual-backend-host>';
   ```
3. عيّن `CYBERLIFE_CORS_ORIGINS=https://cyber-life-wheat.vercel.app` في Backend (وأضف الأصول الإضافية المعروفة فقط).
4. أعد نشر الواجهة، ثم تحقق أن `/api/health` و`/api/auth/me` يذهبان إلى Backend المحدد.

تفاصيل البيئة، Firebase وCORS في [DEPLOYMENT.md](DEPLOYMENT.md). لا يوجد عنوان افتراضي/تخمين، ولا تنشر إلى الإنتاج قبل مراجعة التغييرات واجتياز الاختبارات.
