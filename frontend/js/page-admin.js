import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get, post, put, patch } from './api-client.js';
import { escapeHtml, qs, qsa, formatDate } from './core-dom.js';
import { toast } from './core-toast.js';
import { setBusy } from './core-forms.js';

const { content } = await mountLayout('admin.html', { admin: true });
loading(content);
const COLLECTIONS = [['chapters', 'الفصول'], ['lessons', 'الدروس'], ['assessments', 'التقييمات'], ['missions', 'المهام'], ['laboratory', 'المختبر'], ['teammates', 'الزملاء'], ['glossary', 'القاموس']];
let tab = 'overview';

function tabs() {
  const items = [['overview', 'نظرة عامة'], ['users', 'الطلاب'], ['content', 'المحتوى'], ['assessments', 'الدرجات'], ['reports', 'التقارير'], ['audit', 'سجل التدقيق']];
  return `<div class="tabs">${items.map(([id, label]) => `<button class="tab ${tab === id ? 'active' : ''}" data-tab="${id}" type="button">${label}</button>`).join('')}</div>`;
}
async function render() {
  content.innerHTML = pageHead('لوحة الإدارة', 'إجراءات محمية بتحقق الخادم من الدور، ومسجلة في سجل التدقيق.') + tabs() + '<div id="tabBody"></div>';
  qsa('[data-tab]').forEach(btn => btn.addEventListener('click', () => { tab = btn.dataset.tab; render(); }));
  const body = qs('#tabBody'); loading(body);
  try {
    if (tab === 'overview') await renderOverview(body);
    else if (tab === 'users') await renderUsers(body);
    else if (tab === 'content') await renderContent(body);
    else if (tab === 'assessments') await renderAssessments(body);
    else if (tab === 'reports') await renderReports(body);
    else await renderAudit(body);
  } catch (err) { errorState(body, err.message); }
}
async function renderOverview(body) {
  const d = await get('/api/admin/overview');
  body.innerHTML = `<div class="admin-stat-grid">
    <div class="card stat"><span class="value">${d.students}</span><span class="label">طلاب</span></div>
    <div class="card stat"><span class="value">${d.lessons}</span><span class="label">دروس</span></div>
    <div class="card stat"><span class="value">${d.average_score}%</span><span class="label">متوسط الدرجات</span></div>
    <div class="card stat"><span class="value">${d.pending_reports}</span><span class="label">تقارير بانتظار المراجعة</span></div>
  </div>
  <div class="grid grid-2"><section class="card"><h2>إكمال الفصول</h2><div class="table-wrap"><table><thead><tr><th>الفصل</th><th>إكمالات</th><th>النسبة</th></tr></thead><tbody>${(d.chapter_stats || []).map(c => `<tr><td>${escapeHtml(c.title)}</td><td>${c.completions}</td><td>${c.completion_rate}%</td></tr>`).join('')}</tbody></table></div></section>
  <section class="card"><h2>حالات المهام</h2><div class="chip-list">${Object.entries(d.mission_states || {}).map(([k, v]) => `<span class="badge">${escapeHtml(k)}: ${v}</span>`).join('') || '<span class="muted">لا مهام مسندة</span>'}</div><div class="divider"></div><button class="btn" id="seedBtn" type="button">إعادة زرع المحتوى من الملفات (لا يستبدل تعديلات الإدارة إلا بالقوة)</button><label class="checkbox mt-1"><input type="checkbox" id="seedForce"><span>فرض الاستبدال (يمسح تعديلات المحتوى المنشور من الملفات)</span></label></section></div>`;
  qs('#seedBtn').addEventListener('click', async () => {
    const btn = qs('#seedBtn'); setBusy(btn, true);
    try { const res = await post('/api/admin/content-seed', { force: qs('#seedForce').checked }); toast('تم زرع المحتوى', 'success'); await renderOverview(body); }
    catch { setBusy(btn, false); }
  });
}
async function renderUsers(body) {
  const d = await get('/api/admin/users?limit=200');
  body.innerHTML = `<div class="table-wrap"><table><thead><tr><th>الاسم</th><th>البريد</th><th>الدور</th><th>الحالة</th><th>إجراء</th></tr></thead><tbody>${(d.items || []).map(u => `<tr><td>${escapeHtml(u.display_name)}</td><td>${escapeHtml(u.email)}</td><td><span class="badge ${u.role === 'admin' ? 'info' : ''}">${u.role === 'admin' ? 'مدير' : 'طالب'}</span></td><td>${u.active === false ? 'موقوف' : 'نشط'}</td><td><select class="role-select" data-uid="${u.uid}"><option value="student" ${u.role !== 'admin' ? 'selected' : ''}>طالب</option><option value="admin" ${u.role === 'admin' ? 'selected' : ''}>مدير</option></select></td></tr>`).join('')}</tbody></table></div>`;
  qsa('.role-select').forEach(sel => sel.addEventListener('change', async () => {
    const previous = sel.dataset.previous || (sel.value === 'admin' ? 'student' : 'admin');
    try { await patch(`/api/admin/users/${sel.dataset.uid}/role`, { role: sel.value }); toast('تم تحديث الدور', 'success'); sel.dataset.previous = sel.value; }
    catch { sel.value = previous; }
  }));
}
async function renderContent(body) {
  body.innerHTML = `<div class="admin-toolbar"><select id="collection">${COLLECTIONS.map(([id, label]) => `<option value="${id}">${label}</option>`).join('')}</select><button class="btn" id="refreshContent" type="button">تحديث</button><button class="btn primary" id="newContent" type="button">عنصر جديد</button></div><div id="contentList"></div><div class="card mt-2 content-editor"><h2 id="editorTitle">محرر المحتوى</h2><form id="contentForm"><div class="field"><label>العنوان</label><input class="input" name="title" required></div><div class="field"><label>الوصف</label><textarea name="description"></textarea></div><div class="field"><label>بيانات JSON إضافية</label><textarea name="data" class="input" placeholder='{"order":1}'></textarea><div class="hint">للدروس والتقييمات والمهام، ضع الحقول الكاملة المطلوبة في الخادم.</div></div><label class="checkbox"><input type="checkbox" name="published"><span>منشور</span></label><input type="hidden" name="id"><div class="flex mt-1"><button class="btn primary" type="submit">حفظ</button><button class="btn" type="button" id="publishToggle">نشر/إلغاء نشر</button></div></form></div>`;
  const collection = qs('#collection');
  async function loadList() {
    const d = await get(`/api/admin/content/${collection.value}`);
    qs('#contentList').innerHTML = `<div class="table-wrap"><table><thead><tr><th>المعرّف</th><th>العنوان</th><th>منشور</th><th>تحديث</th><th></th></tr></thead><tbody>${(d.items || []).map(i => `<tr><td><code>${escapeHtml(i.id)}</code></td><td>${escapeHtml(i.title || i.term || i.name || i.id)}</td><td>${i.published ? 'نعم' : 'لا'}</td><td>${formatDate(i.updated_at)}</td><td><button class="btn small" data-edit="${escapeHtml(i.id)}" type="button">تحرير</button></td></tr>`).join('')}</tbody></table></div>`;
    qsa('[data-edit]').forEach(btn => btn.addEventListener('click', async () => {
      const item = (d.items || []).find(x => x.id === btn.dataset.edit);
      const form = qs('#contentForm');
      form.title.value = item.title || item.term || item.name || '';
      form.description.value = item.description || '';
      form.published.checked = Boolean(item.published);
      form.id.value = item.id;
      const extra = { ...item }; delete extra.title; delete extra.description; delete extra.published;
      form.data.value = JSON.stringify(extra, null, 2);
      qs('#editorTitle').textContent = `تحرير ${item.id}`;
    }));
  }
  collection.addEventListener('change', loadList);
  qs('#refreshContent').addEventListener('click', loadList);
  qs('#newContent').addEventListener('click', () => { const f = qs('#contentForm'); f.reset(); f.id.value = ''; qs('#editorTitle').textContent = 'عنصر جديد'; });
  qs('#contentForm').addEventListener('submit', async e => {
    e.preventDefault(); const f = e.target; const btn = f.querySelector('button[type=submit]'); setBusy(btn, true);
    let data = {};
    try { data = f.data.value.trim() ? JSON.parse(f.data.value) : {}; } catch { toast('JSON غير صالح', 'error'); setBusy(btn, false); return; }
    const payload = { title: f.title.value, description: f.description.value, published: f.published.checked, data };
    try {
      if (f.id.value) await put(`/api/admin/content/${collection.value}/${f.id.value}`, payload);
      else await post(`/api/admin/content/${collection.value}`, payload);
      toast('تم الحفظ', 'success'); await loadList();
    } catch { }
    setBusy(btn, false);
  });
  qs('#publishToggle').addEventListener('click', async () => {
    const f = qs('#contentForm'); if (!f.id.value) { toast('اختر عنصراً أولاً', 'error'); return; }
    try { await patch(`/api/admin/content/${collection.value}/${f.id.value}/publish`, { published: !f.published.checked }); f.published.checked = !f.published.checked; toast('تم تحديث النشر', 'success'); await loadList(); } catch { }
  });
  await loadList();
}
async function renderAssessments(body) {
  const d = await get('/api/admin/assessments?limit=200');
  body.innerHTML = `<div class="table-wrap"><table><thead><tr><th>الطالب</th><th>التقييم</th><th>النوع</th><th>الدرجة</th><th>اجتياز</th><th>الوقت</th></tr></thead><tbody>${(d.items || []).map(a => `<tr><td>${escapeHtml(a.student_name)}</td><td>${escapeHtml(a.title || '')}</td><td>${escapeHtml(a.kind || '')}</td><td>${a.percentage}%</td><td>${a.passed ? 'نعم' : 'لا'}</td><td>${formatDate(a.created_at)}</td></tr>`).join('') || '<tr><td colspan="6">لا نتائج</td></tr>'}</tbody></table></div>`;
}
async function renderReports(body) {
  const d = await get('/api/admin/reports?limit=200');
  body.innerHTML = `<div class="grid">${(d.items || []).map(r => `<div class="card"><div class="flex-between"><strong>${escapeHtml(r.title)}</strong><span class="badge">${escapeHtml(r.student_name)}</span></div><small class="muted">${formatDate(r.created_at)} · ${r.evaluation?.percentage ?? 0}% · ${escapeHtml(r.review?.status || 'pending')}</small><p>${escapeHtml(r.summary)}</p><details><summary>التفاصيل</summary><p><strong>أدلة:</strong> ${escapeHtml(r.evidence)}</p><p><strong>تحليل:</strong> ${escapeHtml(r.analysis)}</p><p><strong>إجراءات:</strong> ${escapeHtml(r.actions)}</p></details><div class="review-actions mt-1"><select data-report="${r.id}" data-uid="${r.uid}"><option value="approved">اعتماد</option><option value="needs_revision">يحتاج تعديلاً</option><option value="pending">معلق</option></select><input class="input" style="max-width:320px" placeholder="تعليق المراجعة" data-comment="${r.id}"><button class="btn small" data-review="${r.id}" data-uid="${r.uid}" type="button">حفظ المراجعة</button></div></div>`).join('') || '<div class="empty">لا تقارير</div>'}</div>`;
  qsa('[data-review]').forEach(btn => btn.addEventListener('click', async () => {
    const id = btn.dataset.review, uid = btn.dataset.uid;
    const status = qs(`[data-report="${id}"]`).value;
    const comment = qs(`[data-comment="${id}"]`).value;
    setBusy(btn, true);
    try { await patch(`/api/admin/reports/${id}/review`, { uid, status, comment }); toast('تمت المراجعة', 'success'); await renderReports(body); }
    catch { setBusy(btn, false); }
  }));
}
async function renderAudit(body) {
  const d = await get('/api/admin/audit?limit=200');
  body.innerHTML = `<div class="table-wrap"><table><thead><tr><th>الوقت</th><th>الفاعل</th><th>الإجراء</th><th>الهدف</th><th>تفاصيل</th></tr></thead><tbody>${(d.items || []).map(a => `<tr class="audit-row"><td>${formatDate(a.created_at)}</td><td>${escapeHtml(a.actor_uid)}</td><td>${escapeHtml(a.action)}</td><td><code>${escapeHtml(a.target)}</code></td><td><details><summary>عرض</summary><pre>${escapeHtml(JSON.stringify({ before: a.before, after: a.after }, null, 2))}</pre></details></td></tr>`).join('') || '<tr><td colspan="5">لا سجلات</td></tr>'}</tbody></table></div>`;
}
await render();
