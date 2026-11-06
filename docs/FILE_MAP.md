# خريطة الملفات — كل ملف ووظيفته

هذا الدليل يجيب على سؤال واحد: **أفتح أي ملف لو عايز أعدّل حاجة معينة؟**

القاعدة الجديدة: **مجلد واحد لكل طبقة، والملفات مسطحة بداخله، واسم الملف يقول وظيفته.**
لا يوجد مجلد داخل مجلد داخل مجلد.

---

## الجذر

| الملف | وظيفته |
|---|---|
| `README_AR.md` | مدخل المشروع بالعربي |
| `firebase.json` | يقول لـ Firebase CLI أين ملف القواعد |
| `vercel.json` | إعداد نشر الواجهة على Vercel |
| `.gitignore` | يمنع رفع الأسرار والبيانات المحلية |
| `.dockerignore` | يمنع نسخ الملفات غير الضرورية لصورة Docker |

---

## `frontend/` — كل ما يراه المستخدم

### الصفحات (ملف HTML واحد لكل شاشة)

| الملف | الشاشة |
|---|---|
| `index.html` | الصفحة الرئيسية التعريفية |
| `login.html` | تسجيل الدخول / إنشاء حساب |
| `dashboard.html` | لوحة الطالب |
| `curriculum.html` | فهرس الفصول |
| `lessons.html` | الدرس والتقييم |
| `missions.html` | المهام والتحقيق |
| `laboratory.html` | المختبر والطرفية |
| `team.html` | الفريق والزملاء |
| `reports.html` | التقارير |
| `achievements.html` | الإنجازات |
| `profile.html` | الملف الشخصي |
| `admin.html` | لوحة الإدارة |
| `config.js` | عنوان الخادم عند النشر المنفصل |

### `frontend/js/` — كل ملفات JavaScript مسطحة

**البادئة تحدد النوع فورًا:**

| البادئة | المعنى |
|---|---|
| `core-` | أداة مشتركة تستخدمها كل الصفحات |
| `api-` | الاتصال بالخادم |
| `auth-` | تسجيل الدخول والصلاحيات |
| `page-` | منطق شاشة واحدة، واسمها نفس اسم ملف HTML |

| الملف | وظيفته |
|---|---|
| `core-config.js` | الثوابت وعنوان الـ API ومفاتيح التخزين |
| `core-dom.js` | أدوات DOM + تهريب النصوص لمنع الحقن |
| `core-forms.js` | التحقق من النماذج وقراءة قيمها |
| `core-icons.js` | أيقونات SVG |
| `core-layout.js` | الهيكل الجانبي وحارس الجلسة والأدمن |
| `core-toast.js` | رسائل التنبيه |
| `api-client.js` | عميل HTTP موحد يضيف الرمز ويفسر الأخطاء |
| `auth.js` | دخول Google/البريد، الخروج، حفظ المستخدم |
| `auth-firebase-config.js` | **الملف الذي تضع فيه إعدادات Firebase العامة** |
| `page-landing.js` | الصفحة الرئيسية |
| `page-login.js` | شاشة الدخول |
| `page-dashboard.js` | لوحة الطالب |
| `page-curriculum.js` | فهرس الفصول |
| `page-lessons.js` | الدروس والتقييمات |
| `page-missions.js` | المهام |
| `page-laboratory.js` | المختبر |
| `page-team.js` | الفريق |
| `page-reports.js` | التقارير |
| `page-achievements.js` | الإنجازات |
| `page-profile.js` | الملف الشخصي |
| `page-admin.js` | لوحة الإدارة |

### `frontend/css/`

| الملف | وظيفته |
|---|---|
| `base.css` | المتغيرات والألوان والخطوط |
| `layout.css` | الهيكل والشريط الجانبي |
| `components.css` | الأزرار والحقول والبطاقات |
| `landing.css` | الصفحة الرئيسية فقط |
| `dashboard.css` | لوحة الطالب |
| `lessons.css` | الدروس |
| `laboratory.css` | المختبر والطرفية |
| `admin.css` | لوحة الإدارة |
| `responsive.css` | مقاسات الموبايل |

### `frontend/assets/`

| الملف | وظيفته |
|---|---|
| `logo.svg` / `favicon.svg` | الشعار |
| `service-01..10-*.webp` | صور الخدمات **بخلفية شفافة** (WebP) |
| `character-01..05-*.webp` | صور الشخصيات **بخلفية شفافة** |

---

## `backend/` — الخادم

كل ملفات Python مسطحة داخل `backend/app/`. **البادئة تحدد النوع:**

| البادئة | المعنى |
|---|---|
| `route_` | يستقبل طلب HTTP ويتحقق من الصلاحية |
| `service_` | منطق العمل الفعلي |
| `db_` | القراءة والكتابة في قاعدة البيانات |
| بدون بادئة | ملف تأسيسي مشترك |

### الملفات التأسيسية

| الملف | وظيفته |
|---|---|
| `main.py` | يشغّل التطبيق ويجمع المسارات |
| `config.py` | الإعدادات والتحقق منها |
| `dependencies.py` | حقن الخدمات والتحقق من المستخدم/الأدمن |
| `schemas.py` | شكل البيانات المقبولة في الطلبات |
| `errors.py` | أنواع الأخطاء ورسائلها العربية |
| `helpers.py` | دوال مساعدة (تطبيع النص، المعرفات، التوقيت) |
| `logging_setup.py` | السجل المنظم |
| `middleware.py` | ترقيم الطلبات، حد المعدل، حجم الجسم |
| `tokens.py` | التحقق من رموز الدخول |

### `route_*` — نقاط الـ API

`route_health` الصحة · `route_auth` الدخول · `route_curriculum` المنهج · `route_progress` التقدم · `route_teams` الفرق · `route_missions` المهام · `route_laboratory` المختبر · `route_reports` التقارير · `route_achievements` الإنجازات · `route_admin` الإدارة.

### `service_*` — منطق العمل

| الملف | وظيفته |
|---|---|
| `service_users.py` | الحسابات والأدوار |
| `service_content.py` | تحميل وبذر ونشر المحتوى |
| `service_scoring.py` | التصحيح الحقيقي بالمفاتيح والمعايير |
| `service_progress.py` | إكمال الدروس والتخرج |
| `service_teams.py` | الفريق والزملاء والمساهمات |
| `service_missions.py` | مراحل المهمة وبواباتها |
| `service_laboratory.py` | الطرفية المحاكية والأوامر المسموحة |
| `service_reports.py` | التقارير والمراجعة |
| `service_achievements.py` | الإنجازات |
| `service_activity.py` | سجل النشاط |
| `service_analytics.py` | الإحصاءات |
| `service_audit.py` | سجل التدقيق الإداري |

### `db_*` — التخزين

| الملف | وظيفته |
|---|---|
| `db_base.py` | الواجهة المشتركة |
| `db_firebase.py` | Firebase Realtime Database (الإنتاج) |
| `db_local.py` | ملف محلي للاختبارات المعزولة فقط |

### ملفات أخرى

| الملف | وظيفته |
|---|---|
| `requirements.txt` | مكتبات Python |
| `.env.example` | قالب الإعدادات الحقيقية |
| `Dockerfile` | بناء صورة الخادم |
| `tests/` | اختبارات الخادم |

---

## `content/` — المادة التعليمية (مسطح)

| الملف | وظيفته |
|---|---|
| `chapter-01.json` … `chapter-15.json` | الفصل ودروسه وتقييمه |
| `missions.json` | المهام الخمس عشرة |
| `laboratory.json` | سيناريوهات المختبر |
| `teammates.json` | الزملاء الثلاثة |
| `glossary.json` | المصطلحات |

---

## `database/`

| الملف | وظيفته |
|---|---|
| `database.rules.json` | قواعد الأمان التي تُنشر على Firebase |
| `realtime_database_structure.json` | شكل العقد والحقول |
| `DATABASE_DOCUMENTATION.md` | شرح القاعدة بالعربي |

---

## `docs/` · `scripts/` · `tests-frontend/`

| الملف | وظيفته |
|---|---|
| `docs/FILE_MAP.md` | هذا الملف |
| `docs/ARCHITECTURE.md` | المعمارية |
| `docs/API.md` | نقاط الـ API |
| `docs/SECURITY.md` | الأمان |
| `docs/FIREBASE_SETUP.md` | إعداد Firebase خطوة بخطوة |
| `docs/FIREBASE_VERIFIED.md` | نتيجة فحص إعدادات Firebase الحقيقية |
| `docs/GITHUB_AND_VERCEL.md` | الرفع على GitHub والنشر على Vercel |
| `docs/DEPLOYMENT.md` | النشر |
| `docs/TESTING.md` | كيف تشغّل الاختبارات |
| `docs/TEST_REPORT.md` | نتيجة الاختبارات |
| `docs/IMPLEMENTATION_STATUS.md` | ما تم وما تبقى |
| `docs/LINE_COUNT_REPORT.md` | عدّ الأسطر |
| `scripts/serve_preview.sh` | تشغيل المعاينة على منفذ 8000 (بيانات معزولة) |
| `scripts/push_to_github.sh` | رفع المشروع إلى GitHub مع فحص أسرار |
| `scripts/run_tests.sh` | تشغيل كل الاختبارات |
| `scripts/count_lines.py` | توليد تقرير الأسطر |
| `scripts/make_transparent.py` | تحويل صور الخلفية البيضاء إلى شفافة |
| `tests-frontend/` | اختبارات الواجهة |

---

## أمثلة سريعة

| عايز تعمل إيه؟ | افتح |
|---|---|
| تغيّر نص في الصفحة الرئيسية | `frontend/index.html` |
| تغيّر شكل زر | `frontend/css/components.css` |
| تعدّل درس | `content/chapter-XX.json` |
| تعدّل مهمة | `content/missions.json` |
| تغيّر طريقة تصحيح سؤال | `backend/app/service_scoring.py` |
| تضيف أمر مسموح في المختبر | `backend/app/service_laboratory.py` |
| تغيّر صلاحية قراءة في القاعدة | `database/database.rules.json` |
| تحط إعدادات Firebase | `frontend/js/auth-firebase-config.js` |
