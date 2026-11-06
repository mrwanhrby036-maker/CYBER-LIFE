# البنية المعمارية — CYBER LIFE

## النظرة العامة

المنصة مقسمة إلى ثلاث طبقات قابلة للنشر المستقل:

1. **الواجهة الأمامية**: HTML5 + CSS3 + JavaScript ES Modules، بدون أطر عمل. تُنشر على Vercel كموقع ثابت.
2. **الخادم الخلفي**: FastAPI + Pydantic، يعمل كـ ASGI مستقل. يتحقق من رموز Firebase، يطبق RBAC، يقرأ/يكتب في Firebase Realtime Database عبر REST Admin، ويحتوي كل منطق التعلم والتقييم والمهام والمختبر.
3. **Firebase**: Authentication (بريد/كلمة مرور + Google) و Realtime Database. مشروع المستخدم القائم `hamo-8132e`. لا يُستخدم Firestore.

```
المتصفح (Vercel static)
   │  Authorization: Bearer <Firebase ID token | local dev token>
   ▼
FastAPI (ASGI منفصل)
   ├─ verify_id_token / local session
   ├─ RBAC + rate limit + structured errors + audit
   ├─ Services: curriculum, progress, teams, missions, laboratory, reports, admin
   └─ Repository
        ├─ FirebaseRepository (REST + service account)  [production]
        └─ LocalRepository (.data/database.json)         [development/tests only]
```

## لماذا Repository Pattern؟

- نفس الخدمات تعمل في الاختبارات بدون إنترنت أو مشروع Firebase.
- الإنتاج يستخدم `FirebaseRepository` فقط؛ `LocalRepository` مرفوض عندما `CYBERLIFE_ENV=production`.
- كل كتابة تمر عبر الخادم؛ قواعد RTDB تمنع كتابة العميل مباشرة.

## مسارات البيانات

- `content/*.json` هي **بذور** أولية. عند أول إقلاع (أو `POST /api/admin/content-seed`) تُنسخ إلى `curriculum/*` و `assessment_keys/*` في قاعدة البيانات. بعد ذلك الـ API يقرأ من القاعدة، لذلك تعديلات الأدمن تبقى محفوظة.
- مفاتيح الإجابة منفصلة دائمًا: `assessment_keys/lessons/{id}` و `assessment_keys/chapters/{id}`. لا تُرسل للمتصفح.
- تقدم الطالب: `progress/{uid}`, `assessments/{uid}`, `mission_submissions/{uid}`, `reports/{uid}`, `achievements/{uid}`.
- الفريق: `teams/{team_id}` + حجز اسم فريد في `team_names/{normalized_name}` عبر معاملة ذرية.

## الوحدات الخلفية

كل الملفات مسطحة داخل `backend/app/`، والبادئة تحدد الوظيفة.

| الملف | المسؤولية |
|---|---|
| `config.py` | إعدادات مُتحقق منها، fail-closed للإنتاج |
| `tokens.py` | التحقق من رموز الدخول وجلسات الاختبار المعزولة |
| `dependencies.py` | حقن المستودع/الخدمات، `require_user`, `require_admin` |
| `middleware.py` | request-id، حد المعدل، حجم الجسم، سجل منظم |
| `schemas.py` | شكل بيانات الطلبات |
| `errors.py` · `helpers.py` · `logging_setup.py` | أخطاء ودوال مساعدة وسجل |
| `db_base.py` · `db_firebase.py` · `db_local.py` | واجهة التخزين + تنفيذ Firebase + تنفيذ الاختبارات |
| `route_*.py` | نقاط استقبال HTTP لكل مجال |
| `service_content.py` | تحميل/بذر/تحقق/نشر المحتوى |
| `service_scoring.py` | تصحيح حقيقي بمفاتيح ومعايير rubric |
| `service_progress.py` | إكمال الدروس والفصول والتخرج |
| `service_teams.py` | فريق دائم + زملاء محاكون + تصنيف المساهمات |
| `service_missions.py` | آلة حالات المهام مع بوابات مراحل |
| `service_laboratory.py` | طرفية محاكاة بقائمة أوامر وملفات اصطناعية |
| `service_reports.py` | تقارير الطالب ومراجعة الأدمن |
| `service_users.py` · `service_audit.py` · `service_analytics.py` | مستخدمون/أدوار/تدقيق/إحصاءات |

## الوحدات الأمامية

- `js/core-*.js`: config, dom, forms, toast, icons, layout (حارس الجلسة والأدمن).
- `auth.js` و `auth-firebase-config.js`: تحميل Firebase SDK ديناميكيًا فقط عند اكتمال الإعداد.
- `js/api-client.js`: عميل fetch موحد يضيف Bearer token ويعرض أخطاء عربية.
- `page-*.js`: منطق شاشة واحدة، واسم الملف يطابق ملف HTML الخاص بها.

راجع [خريطة الملفات](FILE_MAP.md) لمعرفة وظيفة كل ملف بالتفصيل.

## قيود مقصودة

- المختبر **محاكاة** وليس حاويات حقيقية؛ لا ينفذ أوامر نظام.
- الزملاء **محاكون** بمحتوى مكتوب وموسوم (حقيقة/فرضية/رأي)، وليسوا نموذج ذكاء اصطناعي.
- حد النشر: 15 فصلًا منشورًا بالضبط.
- الإكمال: تمرين صحيح + تقييم ≥ 70٪. التخرج: 45 درسًا + 15 مهمة.
