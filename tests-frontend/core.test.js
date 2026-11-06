import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..',);
const frontend = join(root, 'frontend');
let dom;

before(() => {
  dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://localhost/' });
  global.window = dom.window;
  global.document = dom.window.document;
  global.localStorage = dom.window.localStorage;
  global.location = dom.window.location;
  global.FormData = dom.window.FormData;
});

test('HTML pages are Arabic RTL and reference existing assets', () => {
  const pages = ['index.html','login.html','dashboard.html','admin.html','profile.html','team.html','curriculum.html','lessons.html','missions.html','laboratory.html','achievements.html','reports.html'];
  for (const page of pages) {
    const html = readFileSync(join(frontend, page), 'utf8');
    assert.match(html, /lang="ar"/, page);
    assert.match(html, /dir="rtl"/, page);
    assert.match(html, /name="viewport"/, page);
    const scripts = [...html.matchAll(/src="([^"]+\.js)"/g)].map(m => m[1]);
    for (const src of scripts) assert.ok(existsSync(join(frontend, src)), `${page} -> ${src}`);
    const css = [...html.matchAll(/href="([^"]+\.css)"/g)].map(m => m[1]);
    for (const href of css) assert.ok(existsSync(join(frontend, href)), `${page} -> ${href}`);
  }
});

test('navigation links cover required student pages', () => {
  const layout = readFileSync(join(frontend, 'js/core-layout.js'), 'utf8');
  for (const page of ['dashboard.html','curriculum.html','lessons.html','missions.html','laboratory.html','team.html','reports.html','achievements.html','profile.html']) {
    assert.ok(layout.includes(page), page);
  }
  assert.ok(layout.includes('admin.html'));
});

test('responsive CSS contains mobile breakpoints', () => {
  const css = readFileSync(join(frontend, 'css/responsive.css'), 'utf8');
  assert.match(css, /@media \(max-width:860px\)/);
  assert.match(css, /@media \(max-width:560px\)/);
  assert.match(css, /\.sidebar\.open/);
});

test('escapeHtml prevents injection', async () => {
  const { escapeHtml } = await import('../frontend/js/core-dom.js');
  assert.equal(escapeHtml('<script>alert(1)</script>'), '&lt;script&gt;alert(1)&lt;/script&gt;');
  assert.equal(escapeHtml('"\'&'), '&quot;&#39;&amp;');
});

test('form validation enforces required, min, email and json', async () => {
  const { validateForm, formData } = await import('../frontend/js/core-forms.js');
  document.body.innerHTML = `<form id="f">
    <div class="field"><input name="name" data-validate="required|min:3" value=""><div class="error"></div></div>
    <div class="field"><input name="email" data-validate="required|email" value="bad"><div class="error"></div></div>
    <div class="field"><textarea name="data" data-validate="json">{bad}</textarea><div class="error"></div></div>
  </form>`;
  const form = document.getElementById('f');
  assert.equal(validateForm(form), false);
  form.querySelector('[name="name"]').value = 'طالب';
  form.querySelector('[name="email"]').value = 'a@b.com';
  form.querySelector('[name="data"]').value = '{"a":1}';
  assert.equal(validateForm(form), true);
  const data = formData(form);
  assert.equal(data.name, 'طالب');
  assert.equal(data.email, 'a@b.com');
});

test('API client attaches bearer token and parses errors', async () => {
  localStorage.setItem('cyberlife_token', 'test-token');
  let captured;
  global.fetch = async (url, opts) => {
    captured = { url, opts };
    return { ok: true, status: 200, text: async () => JSON.stringify({ ok: true }) };
  };
  const { api, setToken } = await import('../frontend/js/api-client.js');
  const data = await api('/api/health');
  assert.deepEqual(data, { ok: true });
  assert.equal(captured.opts.headers.Authorization, 'Bearer test-token');
  global.fetch = async () => ({ ok: false, status: 403, text: async () => JSON.stringify({ error: { code: 'forbidden', message: 'ممنوع' } }) });
  await assert.rejects(() => api('/api/admin/overview', { silent: true }), err => err.status === 403 && err.code === 'forbidden');
  setToken('');
  assert.equal(localStorage.getItem('cyberlife_token'), null);
});

test('admin page requires admin role in layout guard', () => {
  const adminJs = readFileSync(join(frontend, 'js/page-admin.js'), 'utf8');
  assert.match(adminJs, /mountLayout\('admin\.html', \{ admin: true \}\)/);
  const layout = readFileSync(join(frontend, 'js/core-layout.js'), 'utf8');
  assert.match(layout, /user\.role !== 'admin'/);
});

test('laboratory terminal never calls eval or subprocess', () => {
  const lab = readFileSync(join(frontend, 'js/page-laboratory.js'), 'utf8');
  assert.ok(!lab.includes('eval('));
  const backendLab = readFileSync(join(root, 'backend/app/service_laboratory.py'), 'utf8');
  assert.ok(!/import\s+subprocess|from\s+subprocess/.test(backendLab));
  assert.ok(!/os\.system\s*\(/.test(backendLab));
  assert.ok(!/\beval\s*\(|\bexec\s*\(/.test(backendLab));
  assert.ok(backendLab.includes('ALLOWED_COMMANDS'));
});
