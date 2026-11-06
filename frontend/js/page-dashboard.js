import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get } from './api-client.js';
import { escapeHtml, formatDate, percent } from './core-dom.js';
import { icon } from './core-icons.js';

const { content } = await mountLayout('dashboard.html');
loading(content);
try {
  const d = await get('/api/progress/dashboard');
  const overall = d.overall || {};
  const current = d.current_chapter;
  const lesson = d.current_lesson;
  content.innerHTML = pageHead('لوحة التعلم', 'تابع تقدمك ومهامك وإنجازاتك بناءً على بياناتك المخزنة.', `<a class="btn primary" href="${lesson ? 'lessons.html?lesson=' + lesson.id : 'curriculum.html'}">${icon('lesson')}<span>متابعة التعلم</span></a>`) + `
    <div class="stat-grid">
      <div class="card stat"><span class="value">${percent(overall.percentage)}</span><span class="label">التقدم الكلي</span><div class="progress mt-1"><span style="width:${overall.percentage || 0}%"></span></div></div>
      <div class="card stat"><span class="value">${overall.completed_lessons || 0}</span><span class="label">دروس مكتملة</span></div>
      <div class="card stat"><span class="value">${overall.pending_lessons || 0}</span><span class="label">دروس متبقية</span></div>
      <div class="card stat"><span class="value">${d.achievements?.length || 0}</span><span class="label">إنجازات</span></div>
    </div>
    <div class="dashboard-grid">
      <div class="grid">
        <section class="card">
          <div class="flex-between"><h2>الفصل الحالي</h2><a class="btn small" href="curriculum.html">كل الفصول</a></div>
          ${current ? `<p><strong>${escapeHtml(current.title)}</strong></p><div class="progress"><span style="width:${current.percentage}%"></span></div><p class="muted">${current.completed}/${current.total} دروس · ${percent(current.percentage)}</p>` : '<p class="muted">أكملت كل الفصول المنشورة.</p>'}
          ${lesson ? `<a class="btn primary mt-1" href="lessons.html?lesson=${lesson.id}">الدرس التالي: ${escapeHtml(lesson.title)}</a>` : ''}
        </section>
        <section class="card">
          <h2>تقدم الفصول</h2>
          <div class="chapter-progress">${(d.chapters || []).map(c => `<div class="chapter-row"><div><div class="title">${escapeHtml(c.title)}</div><small class="muted">${c.completed}/${c.total}</small></div><div class="progress"><span style="width:${c.percentage}%"></span></div></div>`).join('')}</div>
        </section>
        <section class="card">
          <div class="flex-between"><h2>المهام</h2><a class="btn small" href="missions.html">فتح المهام</a></div>
          ${d.missions?.length ? `<div class="table-wrap"><table><thead><tr><th>المهمة</th><th>الحالة</th></tr></thead><tbody>${d.missions.map(m => `<tr><td><a href="missions.html?mission=${m.id}">${escapeHtml(m.title || m.id)}</a></td><td><span class="badge">${escapeHtml(m.state)}</span></td></tr>`).join('')}</tbody></table></div>` : '<div class="empty">لم تستلم مهام بعد. أنشئ فريقك ثم ابدأ من صفحة المهام.</div>'}
        </section>
      </div>
      <div class="grid">
        <section class="card">
          <h2>الفريق</h2>
          ${d.team ? `<p><strong>${escapeHtml(d.team.name)}</strong></p><a class="btn small" href="team.html">إدارة الفريق</a>` : `<p class="muted">لم تنشئ فريقك الدائم بعد.</p><a class="btn primary small" href="team.html">إنشاء الفريق</a>`}
        </section>
        <section class="card">
          <h2>أحدث الدرجات</h2>
          <div class="score-list">${(d.scores || []).slice(0, 6).map(s => `<div class="score-item"><span>${escapeHtml(s.title)}</span><span class="badge ${s.passed ? 'ok' : 'warn'}">${percent(s.percentage)}</span></div>`).join('') || '<div class="empty">لا توجد تقييمات بعد.</div>'}</div>
        </section>
        <section class="card">
          <h2>مراجعة مقترحة</h2>
          ${(d.review_lessons || []).map(l => `<a class="btn small ghost" style="margin:.2rem" href="lessons.html?lesson=${l.id}">${escapeHtml(l.title)}</a>`).join('') || '<p class="muted">لا توجد دروس تحتاج مراجعة حالياً.</p>'}
        </section>
        <section class="card">
          <h2>النشاط الأخير</h2>
          <ul class="activity-list">${(d.recent_activity || []).map(a => `<li><div>${escapeHtml(a.title)}</div><div class="time">${formatDate(a.created_at)}${a.score != null ? ' · ' + percent(a.score) : ''}</div></li>`).join('') || '<li class="muted">لا نشاط بعد.</li>'}</ul>
        </section>
        <section class="card">
          <h2>إنجازات</h2>
          <div class="achievement-mini">${(d.achievements || []).map(a => `<span class="badge ok">${icon('award')}${escapeHtml(a.title)}</span>`).join('') || '<span class="muted">لم تحصل على إنجازات بعد.</span>'}</div>
        </section>
      </div>
    </div>`;
} catch (err) { errorState(content, err.message || 'تعذر تحميل لوحة التعلم'); }
