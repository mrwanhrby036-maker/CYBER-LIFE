import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get, post } from './api-client.js';
import { escapeHtml, qs, qsa } from './core-dom.js';
import { toast } from './core-toast.js';
import { setBusy } from './core-forms.js';

const { content } = await mountLayout('lessons.html');
const params = new URLSearchParams(location.search);
loading(content);

function questionHtml(q, prefix) {
  const name = `${prefix}_${q.id}`;
  let input = '';
  if (q.type === 'multi') {
    input = (q.options || []).map(o => `<label class="checkbox"><input type="checkbox" name="${name}" value="${escapeHtml(o.id)}"><span>${escapeHtml(o.text)}</span></label>`).join('');
  } else if (q.type === 'short') {
    input = `<input class="input" name="${name}" autocomplete="off" placeholder="إجابة قصيرة">`;
  } else if (q.type === 'report') {
    input = `<textarea class="input" name="${name}" placeholder="اكتب إجابتك التقريرية وفق المعيار المعلن في الدرس"></textarea>`;
  } else {
    input = (q.options || []).map(o => `<label class="radio"><input type="radio" name="${name}" value="${escapeHtml(o.id)}"><span>${escapeHtml(o.text)}</span></label>`).join('');
  }
  return `<div class="question" data-qid="${escapeHtml(q.id)}" data-type="${escapeHtml(q.type)}"><div class="q-title">${escapeHtml(q.prompt)}</div>${input}<div class="feedback-slot"></div></div>`;
}
function collectAnswers(root, prefix) {
  const answers = [];
  qsa('.question', root).forEach(node => {
    const qid = node.dataset.qid, type = node.dataset.type, name = `${prefix}_${qid}`;
    let answer;
    if (type === 'multi') answer = qsa(`input[name="${name}"]:checked`, node).map(i => i.value);
    else if (type === 'short' || type === 'report') answer = qs(`[name="${name}"]`, node)?.value || '';
    else answer = qs(`input[name="${name}"]:checked`, node)?.value || '';
    answers.push({ question_id: qid, answer });
  });
  return answers;
}
function showFeedback(root, results) {
  qsa('.question', root).forEach(node => {
    const r = (results || []).find(x => x.question_id === node.dataset.qid);
    const slot = qs('.feedback-slot', node);
    if (!r || !slot) return;
    slot.innerHTML = `<div class="feedback ${r.correct ? 'correct' : 'incorrect'}">${r.correct ? 'صحيح' : 'يحتاج مراجعة'} · ${escapeHtml(r.feedback || '')} (${r.earned}/${r.points})</div>`;
  });
}

async function renderList(chapterId) {
  const url = chapterId ? `/api/curriculum/lessons?chapter_id=${chapterId}` : '/api/curriculum/lessons';
  const data = await get(url);
  const chapter = chapterId ? (await get(`/api/curriculum/chapters/${chapterId}`)).chapter : null;
  content.innerHTML = pageHead(chapter ? chapter.title : 'الدروس', chapter ? chapter.description : 'اختر درساً للشرح والتمرين والتقييم.', `<a class="btn" href="curriculum.html">المنهج</a>`) + `
    <div class="grid grid-2">${(data.items || []).map(l => `<article class="card hover"><h3>${escapeHtml(l.title)}</h3><p class="muted">${l.estimated_minutes || 0} دقيقة</p><a class="btn primary small" href="lessons.html?lesson=${l.id}">فتح الدرس</a></article>`).join('') || '<div class="empty">لا دروس منشورة.</div>'}</div>`;
}

async function renderAssessment(assessmentId) {
  const { assessment } = await get(`/api/curriculum/assessments/${assessmentId}`);
  content.innerHTML = pageHead(assessment.title, 'تقييم يُقيّم آلياً بمفاتيح إجابة ومعايير معلنة. لا يوجد تقييم ذكاء اصطناعي غير مهيأ.') + `
    <section class="card"><form id="assessmentForm">${(assessment.questions || []).map(q => questionHtml(q, 'as')).join('')}<button class="btn primary" type="submit">تسليم التقييم</button></form><div id="assessmentResult" class="mt-2"></div></section>`;
  const form = qs('#assessmentForm');
  form.addEventListener('submit', async e => {
    e.preventDefault(); const btn = form.querySelector('button'); setBusy(btn, true);
    try {
      const res = await post(`/api/progress/assessments/${assessmentId}/submit`, { answers: collectAnswers(form, 'as') });
      const a = res.attempt;
      qs('#assessmentResult').innerHTML = `<div class="alert ${a.passed ? 'success' : 'warn'}">الدرجة: ${a.percentage}% · ${a.passed ? 'اجتياز' : 'لم تجتز بعد'}</div>`;
      showFeedback(form, a.results); toast(a.passed ? 'اجتزت التقييم' : 'راجع التغذية الراجعة', a.passed ? 'success' : 'info');
    } catch (err) { qs('#assessmentResult').innerHTML = `<div class="alert error">${escapeHtml(err.message)}</div>`; }
    setBusy(btn, false);
  });
}

async function renderLesson(lessonId) {
  const { lesson } = await get(`/api/curriculum/lessons/${lessonId}`);
  const { assessment } = await get(`/api/curriculum/assessments/${lesson.assessment_id}`);
  const sections = (lesson.sections || []).map(s => `<section class="lesson-section card"><h3>${escapeHtml(s.heading)}</h3><p>${escapeHtml(s.body)}</p></section>`).join('');
  const terms = (lesson.terminology || []).map(t => `<div class="term"><span class="en">${escapeHtml(t.term)}</span><div>${escapeHtml(t.definition)}</div></div>`).join('');
  const commands = (lesson.command_explanations || []).map(c => `<div class="command-card"><code class="cmd">${escapeHtml(c.command)}</code><dl>${[['ماذا يفعل', c.what], ['لماذا يوجد', c.why], ['أين يستخدم', c.where], ['الأجزاء', c.parts], ['المخرجات', c.output], ['التفسير', c.interpret], ['أخطاء شائعة', c.errors], ['مثال آمن', c.safe_example], ['متى تتجنبه', c.avoid], ['صلته بالأمن', c.security_connection]].map(([k, v]) => `<dt>${k}</dt><dd>${escapeHtml(v || '')}</dd>`).join('')}</dl></div>`).join('');
  const examples = (lesson.examples || []).map(x => `<div class="card mb-1"><strong>${escapeHtml(x.title)}</strong><p>${escapeHtml(x.explanation)}</p></div>`).join('');
  content.innerHTML = pageHead(lesson.title, lesson.completion_criterion || '', `<a class="btn" href="lessons.html?chapter=${lesson.chapter_id}">عودة للفصل</a>`) + `
    <div class="lesson-layout">
      <div>
        <section class="card mb-2"><h2>مقدمة</h2><p>${escapeHtml(lesson.introduction)}</p><h3>أهداف التعلم</h3><ul class="objectives">${(lesson.objectives || []).map(o => `<li>${escapeHtml(o)}</li>`).join('')}</ul></section>
        ${sections}
        ${commands ? `<section class="card mb-2"><h2>شرح الأوامر</h2>${commands}</section>` : ''}
        ${terms ? `<section class="card mb-2"><h2>المصطلحات</h2><div class="term-grid">${terms}</div></section>` : ''}
        ${examples ? `<section class="card mb-2"><h2>أمثلة عملية</h2>${examples}</section>` : ''}
        <section class="card mb-2"><h2>أخطاء شائعة وملاحظات</h2><ul>${(lesson.common_mistakes || []).map(m => `<li>${escapeHtml(m)}</li>`).join('')}</ul><ul>${(lesson.important_notes || []).map(n => `<li>${escapeHtml(n)}</li>`).join('')}</ul></section>
        <section class="card mb-2"><h2>التمرين العملي</h2><form id="exerciseForm">${questionHtml(lesson.exercise, 'ex')}<div id="exerciseFeedback"></div></form></section>
        <section class="card mb-2"><h2>تقييم الدرس</h2><form id="lessonAssessment">${(assessment.questions || []).map(q => questionHtml(q, 'la')).join('')}</form></section>
        <section class="card"><button class="btn primary" id="completeBtn" type="button">إنهاء الدرس وحفظ التقدم</button><div id="completeResult" class="mt-2"></div></section>
      </div>
      <aside class="lesson-side"><div class="card"><h3>دروس ذات صلة</h3>${(lesson.related_lessons || []).map(id => `<a class="btn small ghost" style="margin:.2rem" href="lessons.html?lesson=${id}">${escapeHtml(id)}</a>`).join('') || '<p class="muted">لا توجد</p>'}<div class="divider"></div><h3>معيار الإكمال</h3><p class="muted">${escapeHtml(lesson.completion_criterion || '')}</p></div></aside>
    </div>`;
  qs('#completeBtn').addEventListener('click', async () => {
    const btn = qs('#completeBtn'); setBusy(btn, true);
    const exAnswers = collectAnswers(qs('#exerciseForm'), 'ex');
    const exerciseAnswer = exAnswers[0]?.answer ?? '';
    const body = { exercise_answer: exerciseAnswer, assessment: { answers: collectAnswers(qs('#lessonAssessment'), 'la') } };
    try {
      const res = await post(`/api/progress/lessons/${lessonId}/complete`, body);
      showFeedback(qs('#exerciseForm'), [res.exercise]); showFeedback(qs('#lessonAssessment'), res.assessment.results);
      qs('#completeResult').innerHTML = `<div class="alert success">تم حفظ الإكمال. درجة التقييم: ${res.assessment.percentage}%</div>`;
      toast('تم إنهاء الدرس', 'success');
    } catch (err) {
      const details = err.details || {};
      if (details.exercise) showFeedback(qs('#exerciseForm'), [details.exercise]);
      if (details.assessment) showFeedback(qs('#lessonAssessment'), details.assessment.results);
      qs('#completeResult').innerHTML = `<div class="alert error">${escapeHtml(err.message)}</div>`;
    }
    setBusy(btn, false);
  });
}

try {
  if (params.get('lesson')) await renderLesson(params.get('lesson'));
  else if (params.get('assessment')) await renderAssessment(params.get('assessment'));
  else await renderList(params.get('chapter'));
} catch (err) { errorState(content, err.message || 'تعذر تحميل الدرس'); }
