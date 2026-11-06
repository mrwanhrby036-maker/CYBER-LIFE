import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get, post } from './api-client.js';
import { escapeHtml, qs, qsa } from './core-dom.js';
import { toast } from './core-toast.js';
import { setBusy } from './core-forms.js';

const { content } = await mountLayout('laboratory.html');
loading(content);
let scenarios = [], allowed = [], current = null, session = null;

function terminalLine(entry) {
  return `<div class="line cmd">$ ${escapeHtml(entry.command)}</div>${entry.output ? `<div class="line out">${escapeHtml(entry.output)}</div>` : ''}${entry.explanation ? `<div class="explain">${escapeHtml(entry.explanation)}</div>` : ''}`;
}
function renderTerminal() {
  const term = qs('#terminal');
  term.innerHTML = (session.history || []).map(terminalLine).join('') || '<div class="line out">مختبر آمن. اكتب help لعرض الأوامر المتاحة. لا يتم تنفيذ أي أمر نظام حقيقي.</div>';
  term.scrollTop = term.scrollHeight;
}
function exerciseHtml(ex) {
  return `<div class="card lab-exercise" data-ex="${ex.id}"><h3>${escapeHtml(ex.title)}</h3><ul>${(ex.instructions || []).map(i => `<li>${escapeHtml(i)}</li>`).join('')}</ul>${(ex.hints || []).map(h => `<p class="muted">تلميح: ${escapeHtml(h)}</p>`).join('')}<form class="exForm">${(ex.questions || []).map(q => {
    if (q.type === 'mcq') return `<div class="question" data-qid="${q.id}" data-type="mcq"><div class="q-title">${escapeHtml(q.prompt)}</div>${q.options.map(o => `<label class="radio"><input type="radio" name="${q.id}" value="${o.id}"><span>${escapeHtml(o.text)}</span></label>`).join('')}</div>`;
    if (q.type === 'report') return `<div class="question" data-qid="${q.id}" data-type="report"><div class="q-title">${escapeHtml(q.prompt)}</div><textarea class="input" name="${q.id}"></textarea></div>`;
    return `<div class="question" data-qid="${q.id}" data-type="short"><div class="q-title">${escapeHtml(q.prompt)}</div><input class="input" name="${q.id}"></div>`;
  }).join('')}<button class="btn primary" type="submit">تحقق من التمرين</button><div class="exResult mt-1"></div></form></div>`;
}
async function loadScenario(id) {
  const data = await get(`/api/laboratory/scenarios/${id}`);
  current = data.scenario; session = data.session;
  qs('#scenarioTitle').textContent = current.title;
  qs('#scenarioDesc').textContent = current.description || '';
  qs('#exercises').innerHTML = (current.exercises || []).map(exerciseHtml).join('');
  qsa('.scenario-item').forEach(b => b.classList.toggle('active', b.dataset.id === id));
  renderTerminal();
  qsa('.exForm').forEach(form => form.addEventListener('submit', async e => {
    e.preventDefault();
    const exId = form.closest('[data-ex]').dataset.ex;
    const answers = qsa('.question', form).map(node => {
      const qid = node.dataset.qid, type = node.dataset.type;
      const answer = type === 'mcq' ? qs(`input[name="${qid}"]:checked`, node)?.value || '' : qs(`[name="${qid}"]`, node)?.value || '';
      return { question_id: qid, answer };
    });
    const btn = form.querySelector('button'); setBusy(btn, true);
    try {
      const res = await post(`/api/laboratory/scenarios/${id}/validate`, { exercise_id: exId, answers });
      const r = res.result;
      qs('.exResult', form).innerHTML = `<div class="alert ${r.passed ? 'success' : 'warn'}">${r.passed ? 'اجتزت التمرين' : 'لم تجتز بعد'} · الإجابات: ${r.answers_percentage}% · الأوامر: ${r.commands_ok ? 'مستوفاة' : 'ناقصة'}${r.missing_commands?.length ? ' · أنماط ناقصة: ' + escapeHtml(r.missing_commands.join(', ')) : ''}</div>`;
      toast(r.passed ? 'تمرين مجتاز' : 'راجع المتطلبات', r.passed ? 'success' : 'info');
    } catch (err) { qs('.exResult', form).innerHTML = `<div class="alert error">${escapeHtml(err.message)}</div>`; }
    setBusy(btn, false);
  }));
}
async function render() {
  const data = await get('/api/laboratory/scenarios');
  scenarios = data.items || []; allowed = data.allowed_commands || [];
  content.innerHTML = pageHead('المختبر الآمن', 'طرفية محاكاة بملفات اصطناعية وقائمة أوامر مسموحة. لا تنفيذ لأوامر نظام حقيقية.') + `
    <div class="lab-layout">
      <aside><div class="scenario-list">${scenarios.map(s => `<button class="scenario-item" data-id="${s.id}" type="button"><strong>${escapeHtml(s.title)}</strong><div class="muted">${escapeHtml(s.difficulty || '')}</div></button>`).join('')}</div><div class="card mt-2"><h3>أوامر مسموحة</h3><div class="allowed-commands">${allowed.map(c => `<code>${escapeHtml(c)}</code>`).join('')}</div></div></aside>
      <section>
        <div class="card"><h2 id="scenarioTitle">اختر سيناريو</h2><p id="scenarioDesc" class="muted"></p><div class="terminal" id="terminal" aria-live="polite"></div><form class="terminal-input" id="cmdForm"><span class="prompt">analyst@cyberlife:~$</span><input id="cmdInput" autocomplete="off" spellcheck="false" placeholder="اكتب أمراً مثل ls -la" aria-label="أمر الطرفية"><button class="btn primary" type="submit">تنفيذ</button></form></div>
        <div id="exercises"></div>
      </section>
    </div>`;
  qsa('.scenario-item').forEach(btn => btn.addEventListener('click', () => loadScenario(btn.dataset.id).catch(err => toast(err.message, 'error'))));
  const form = qs('#cmdForm');
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (!current) { toast('اختر سيناريو أولاً', 'error'); return; }
    const input = qs('#cmdInput'); const command = input.value.trim(); if (!command) return;
    const btn = form.querySelector('button'); setBusy(btn, true);
    try {
      const res = await post(`/api/laboratory/scenarios/${current.id}/command`, { command });
      session.history = [...(session.history || []), res.entry]; session.cwd = res.entry.cwd;
      if (command === 'clear') session.history = [];
      renderTerminal(); input.value = '';
    } catch (err) {
      const term = qs('#terminal'); term.insertAdjacentHTML('beforeend', `<div class="line cmd">$ ${escapeHtml(command)}</div><div class="line err">${escapeHtml(err.message)}</div>`); term.scrollTop = term.scrollHeight;
    }
    setBusy(btn, false); input.focus();
  });
  if (scenarios[0]) await loadScenario(scenarios[0].id);
}
try { await render(); } catch (err) { errorState(content, err.message); }
