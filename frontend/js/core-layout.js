import { icon } from './core-icons.js';
import { escapeHtml, qs } from './core-dom.js';
import { requireUser, signOut, cachedUser } from './auth.js';
import { get } from './api-client.js';
import { toast } from './core-toast.js';

const NAV = [
  ['dashboard.html', 'dashboard', 'لوحة التعلم'],
  ['curriculum.html', 'book', 'المنهج'],
  ['lessons.html', 'lesson', 'الدروس'],
  ['missions.html', 'shield', 'المهام'],
  ['laboratory.html', 'terminal', 'المختبر'],
  ['team.html', 'team', 'الفريق'],
  ['reports.html', 'document', 'التقارير'],
  ['achievements.html', 'award', 'الإنجازات'],
  ['profile.html', 'user', 'الملف الشخصي']
];

export async function mountLayout(active, { admin = false } = {}) {
  const user = await requireUser();
  if (admin && user.role !== 'admin') { toast('هذه الصفحة للإدارة فقط', 'error'); location.href = 'dashboard.html'; throw new Error('forbidden'); }
  const team = await get('/api/teams/mine', { silent: true }).catch(() => ({ team: null }));
  const shell = qs('#app');
  const nav = NAV.map(([href, ic, label]) => `<a href="${href}" class="${href === active ? 'active' : ''}">${icon(ic)}<span>${label}</span></a>`).join('');
  const adminLink = user.role === 'admin' ? `<a href="admin.html" class="${active === 'admin.html' ? 'active' : ''}">${icon('admin')}<span>الإدارة</span></a>` : '';
  shell.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar" id="sidebar" aria-label="التنقل الرئيسي">
        <div class="brand"><div class="brand-logo">CL</div><div><div class="brand-title">CYBER LIFE</div><div class="brand-sub">شركة تدريب سيبراني</div></div></div>
        <nav class="nav">${nav}${adminLink}</nav>
        <div class="divider"></div>
        <button class="btn ghost" id="logoutBtn" type="button">${icon('logout')}<span>تسجيل الخروج</span></button>
      </aside>
      <div class="main">
        <header class="topbar">
          <div class="flex">
            <button class="btn ghost menu-toggle" id="menuToggle" type="button" aria-label="فتح القائمة">${icon('menu')}</button>
            <div><strong id="pageTitle">${escapeHtml(document.title)}</strong><div class="muted" style="font-size:.8rem">${team.team ? 'الفريق: ' + escapeHtml(team.team.name) : 'لم تنشئ فريقك بعد'}</div></div>
          </div>
          <div class="topbar-user"><span class="badge ${user.role === 'admin' ? 'info' : ''}">${user.role === 'admin' ? 'مدير' : 'طالب'}</span><div class="avatar">${escapeHtml((user.display_name || 'ط')[0])}</div><span>${escapeHtml(user.display_name || 'متعلم')}</span></div>
        </header>
        <main class="content" id="pageContent"></main>
      </div>
    </div>`;
  qs('#logoutBtn').addEventListener('click', async () => { await signOut(); location.href = 'login.html'; });
  qs('#menuToggle').addEventListener('click', () => qs('#sidebar').classList.toggle('open'));
  return { user, team: team.team, content: qs('#pageContent') };
}

export function pageHead(title, subtitle, actions = '') {
  return `<div class="page-head"><div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(subtitle || '')}</p></div><div class="flex wrap">${actions}</div></div>`;
}
export function loading(target) { target.innerHTML = '<div class="empty"><span class="spinner"></span> جارٍ التحميل…</div>'; }
export function errorState(target, message) { target.innerHTML = `<div class="alert error">${escapeHtml(message)}</div>`; }
