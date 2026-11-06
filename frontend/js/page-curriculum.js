import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get, post } from './api-client.js';
import { escapeHtml, qs, debounce } from './core-dom.js';
import { toast } from './core-toast.js';
import { icon } from './core-icons.js';

const { content } = await mountLayout('curriculum.html');
loading(content);
let chapters = [], glossary = [];
async function load() {
  const [c, g] = await Promise.all([get('/api/curriculum/chapters'), get('/api/curriculum/glossary')]);
  chapters = c.items || []; glossary = g.items || [];
}
function render() {
  content.innerHTML = pageHead('المنهج الدراسي', 'خمسة عشر فصلاً متدرجاً من الأساسيات إلى مشروع الشركة النهائي.', `<a class="btn" href="lessons.html">${icon('lesson')}<span>كل الدروس</span></a>`) + `
    <div class="card mb-2"><div class="field" style="margin:0"><label for="search">بحث في الدروس والمصطلحات</label><input class="input" id="search" placeholder="مثال: سجل، HTTP، تشفير…"><div id="searchResults" class="mt-1"></div></div></div>
    <div class="grid grid-3" id="chapters">${chapters.map(c => `
      <article class="card hover">
        <div class="flex-between"><span class="badge info">الفصل ${c.order}</span><span class="muted">${c.estimated_minutes || 0} دقيقة</span></div>
        <h3 class="mt-1">${escapeHtml(c.title)}</h3>
        <p class="muted">${escapeHtml(c.description || '')}</p>
        <div class="flex wrap">
          <a class="btn small primary" href="lessons.html?chapter=${c.id}">الدروس</a>
          <button class="btn small" data-enroll="${c.id}" type="button">التحاق</button>
          <a class="btn small ghost" href="lessons.html?assessment=${c.assessment_id}">تقييم الفصل</a>
        </div>
      </article>`).join('')}</div>
    <section class="card mt-3"><h2>قاموس المصطلحات</h2><div class="table-wrap"><table><thead><tr><th>المصطلح</th><th>بالعربية</th><th>التعريف</th></tr></thead><tbody>${glossary.map(g => `<tr><td><code>${escapeHtml(g.term)}</code></td><td>${escapeHtml(g.arabic || '')}</td><td>${escapeHtml(g.definition)}</td></tr>`).join('')}</tbody></table></div></section>`;
  content.querySelectorAll('[data-enroll]').forEach(btn => btn.addEventListener('click', async () => {
    btn.disabled = true;
    try { await post(`/api/progress/enroll/${btn.dataset.enroll}`, {}); toast('تم الالتحاق بالفصل', 'success'); }
    catch { btn.disabled = false; }
  }));
  const search = qs('#search');
  search.addEventListener('input', debounce(async () => {
    const q = search.value.trim(); const box = qs('#searchResults');
    if (q.length < 2) { box.innerHTML = ''; return; }
    try {
      const res = await get(`/api/curriculum/search?q=${encodeURIComponent(q)}`);
      box.innerHTML = `<div class="chip-list">${(res.lessons || []).map(l => `<a class="badge info" href="lessons.html?lesson=${l.id}">${escapeHtml(l.title)}</a>`).join('')}${(res.glossary || []).map(g => `<span class="badge">${escapeHtml(g.term)}: ${escapeHtml(g.definition)}</span>`).join('') || '<span class="muted">لا نتائج</span>'}</div>`;
    } catch (err) { box.innerHTML = `<div class="alert error">${escapeHtml(err.message)}</div>`; }
  }, 300));
}
try { await load(); render(); } catch (err) { errorState(content, err.message); }
