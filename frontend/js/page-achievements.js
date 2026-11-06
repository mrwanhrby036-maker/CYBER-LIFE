import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get } from './api-client.js';
import { escapeHtml, formatDate } from './core-dom.js';
import { icon } from './core-icons.js';

const { content } = await mountLayout('achievements.html');
loading(content);
try {
  const data = await get('/api/achievements');
  const earned = new Map((data.items || []).map(a => [a.id, a]));
  content.innerHTML = pageHead('الإنجازات', 'تُمنح الإنجازات من تقدمك الفعلي المخزن، وليس من قيم ثابتة.') + `
    <div class="grid grid-3">${(data.catalog || []).map(rule => {
      const got = earned.get(rule.id);
      return `<div class="card ${got ? '' : 'muted'}"><div class="flex">${icon(rule.icon || 'award')}<h3>${escapeHtml(rule.title)}</h3></div><p>${escapeHtml(rule.description)}</p>${got ? `<span class="badge ok">مُنح في ${formatDate(got.awarded_at)}</span>` : '<span class="badge">غير مكتمل</span>'}</div>`;
    }).join('')}</div>`;
} catch (err) { errorState(content, err.message); }
