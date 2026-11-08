# توثيق API

كل المسارات تحت `/api`. الأخطاء بالشكل:

```json
{ "error": { "code": "validation_error", "message": "رسالة عربية", "details": {} }, "request_id": "..." }
```

المصادقة: `Authorization: Bearer <token>`. في الإنتاج الرمز هو Firebase ID token. في التطوير يمكن استخدام جلسة محلية.

## عام

| Method | Path | الوصف | صلاحية |
|---|---|---|---|
| GET | `/api/health` | حالة الخدمة دون كشف إعدادات داخلية | عام |
| GET | `/api/health/ready` | جاهزية قاعدة البيانات وبذر المحتوى | عام |

## المصادقة

| Method | Path | الوصف |
|---|---|---|
| POST | `/api/auth/local/login` | مسار اختبار معزول ومعطل افتراضياً؛ ليس للاستخدام العام |
| GET | `/api/auth/me` | التحقق من الرمز وإرجاع الملف العام الحالي والدور |
| POST | `/api/auth/logout` | تأكيد إنهاء جلسة التطبيق (يلزم العميل إنهاء Firebase Auth ومسح الرمز) |

## المنهج

| Method | Path | الوصف |
|---|---|---|
| GET | `/api/curriculum/chapters` | الفصول المنشورة |
| GET | `/api/curriculum/chapters/{id}` | فصل + دروسه |
| GET | `/api/curriculum/lessons?chapter_id=&q=` | بحث/قائمة الدروس |
| GET | `/api/curriculum/lessons/{id}` | درس كامل بدون مفاتيح |
| GET | `/api/curriculum/assessments/{id}` | أسئلة تقييم بدون مفاتيح |
| POST | `/api/curriculum/assessments/{id}/submit` | تصحيح تقييم فصل/درس |
| GET | `/api/curriculum/glossary` | المصطلحات |
| GET | `/api/curriculum/search?q=` | بحث في الدروس والمصطلحات |

## التقدم

| Method | Path | الوصف |
|---|---|---|
| GET | `/api/progress/me` | لوحة التقدم الحقيقية |
| POST | `/api/progress/lessons/{id}/complete` | إرسال `{exercise_answer, assessment:{answers}}` |
| GET | `/api/progress/lessons/{id}` | حالة درس |
| GET | `/api/achievements/me` | الإنجازات |
| GET | `/api/activity/me` | النشاط الأخير |

## الفرق

| Method | Path | الوصف |
|---|---|---|
| POST | `/api/teams` | إنشاء الفريق الدائم (مرة واحدة) |
| GET | `/api/teams/me` | فريقي والزملاء |
| GET | `/api/teams/teammates` | ملفات الزملاء المحاكين |
| POST | `/api/teams/contributions` | تسجيل مساهمة موسومة |
| GET | `/api/teams/contributions` | سجل المساهمات |

## المهام

| Method | Path | الوصف |
|---|---|---|
| GET | `/api/missions` | قائمة المهام |
| GET | `/api/missions/{id}` | مهمة + حالة تقديمي |
| POST | `/api/missions/{id}/assign` | استلام |
| POST | `/api/missions/{id}/transition` | نقل مرحلة (`investigating`, `under_review`, `resolved`, `closed`) |
| POST | `/api/missions/{id}/evidence` | جمع دليل |
| POST | `/api/missions/{id}/ask` | سؤال زميل |
| POST | `/api/missions/{id}/decide` | قرار مع تبرير |
| POST | `/api/missions/{id}/findings` | نتائج وإجراءات |
| POST | `/api/missions/{id}/report` | ربط تقرير |
| GET | `/api/missions/{id}/evaluation` | التقييم بعد الحل |

## المختبر

| Method | Path | الوصف |
|---|---|---|
| GET | `/api/laboratory/scenarios` | السيناريوهات |
| GET | `/api/laboratory/scenarios/{id}` | سيناريو + جلسة |
| POST | `/api/laboratory/scenarios/{id}/command` | تنفيذ أمر محاكى |
| POST | `/api/laboratory/scenarios/{id}/validate` | تحقق تمرين |
| POST | `/api/laboratory/scenarios/{id}/reset` | إعادة الجلسة |

## التقارير

| Method | Path | الوصف |
|---|---|---|
| POST | `/api/reports` | إنشاء تقرير |
| GET | `/api/reports/me` | تقاريري |
| GET | `/api/reports/{id}` | تقرير (المالك/أدمن) |
| PUT | `/api/reports/{id}` | تحديث مسودة |

## الأدمن (يتطلب دور admin)

| Method | Path | الوصف |
|---|---|---|
| GET | `/api/admin/overview` | إحصاءات |
| GET | `/api/admin/users` | المستخدمون |
| PATCH | `/api/admin/users/{uid}/role` | تغيير دور |
| PATCH | `/api/admin/users/{uid}/active` | تفعيل/تعطيل |
| GET | `/api/admin/content/{collection}` | قائمة محتوى |
| POST | `/api/admin/content/{collection}` | إنشاء |
| PUT | `/api/admin/content/{collection}/{id}` | تحديث |
| PATCH | `/api/admin/content/{collection}/{id}/publish` | نشر/إلغاء |
| POST | `/api/admin/content-seed` | إعادة بذر |
| GET | `/api/admin/reports` | تقارير للمراجعة |
| POST | `/api/admin/reports/{id}/review` | مراجعة |
| GET | `/api/admin/audit-logs` | سجل تدقيق |
| GET | `/api/admin/analytics` | تحليلات |

OpenAPI التفاعلي متاح على `/docs` عند تشغيل الخادم.
