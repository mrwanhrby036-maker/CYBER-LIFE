import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..',);
const read = p => readFileSync(join(root, p), 'utf8');

test('homepage is a public landing page, not an automatic login redirect', () => {
  const html = read('frontend/index.html');
  assert.match(html, /خدمات المنصة/);
  assert.match(html, /كيف تتعلم/);
  assert.match(html, /الأمان أولًا/);
  assert.ok(!html.includes('location.replace(getToken()'));
  assert.match(html, /login\.html/);
});

test('login UI does not expose development accounts or internal config paths', () => {
  // Import statements are code, not user-facing text: strip them before scanning.
  const visible = src => src.split('\n').filter(l => !/^\s*import\s/.test(l)).join('\n');
  const login = visible(read('frontend/js/page-login.js'));
  const auth = visible(read('frontend/js/auth.js'));
  for (const secret of ['CyberLife-Student', 'CyberLife-Admin', 'student@cyberlife.local', 'admin@cyberlife.local', 'firebase-config.js', 'Admin SDK', 'hamo-8132e']) {
    assert.ok(!login.includes(secret), `login exposes ${secret}`);
    assert.ok(!auth.includes(secret), `auth exposes ${secret}`);
  }
  assert.ok(!login.includes('signInLocal'));
});

test('public health endpoint does not reveal internal modes', () => {
  const health = read('backend/app/route_health.py');
  assert.ok(!health.includes('auth_mode'));
  assert.ok(!health.includes('storage_mode'));
  assert.ok(!health.includes('settings.env'));
});

test('local development login is disabled by default', () => {
  const config = read('backend/app/config.py');
  assert.match(config, /enable_local_dev: bool = False/);
  const router = read('backend/app/route_auth.py');
  assert.match(router, /not settings\.enable_local_dev/);
});

test('Firebase config is complete and points at the real project', async () => {
  const mod = await import('../frontend/js/auth-firebase-config.js');
  const c = mod.firebaseConfig;
  assert.equal(c.projectId, 'hamo-8132e');
  assert.equal(c.authDomain, 'hamo-8132e.firebaseapp.com');
  assert.ok(c.apiKey.length > 20, 'apiKey missing');
  assert.ok(c.appId.includes(':web:'), 'appId missing');
  assert.match(c.databaseURL, /^https:\/\/hamo-8132e-default-rtdb\..+firebasedatabase\.app$/);
  assert.equal(mod.isFirebaseConfigured(), true);
  // Admin SDK material must never appear in frontend config.
  const raw = read('frontend/js/auth-firebase-config.js');
  for (const forbidden of ['private_key', 'client_email', 'service_account', 'BEGIN PRIVATE KEY']) {
    assert.ok(!raw.includes(forbidden), `frontend config leaks ${forbidden}`);
  }
});

test('login errors are user-friendly, never raw technical codes', () => {
  const login = read('frontend/js/page-login.js');
  assert.match(login, /function friendlyError/);
  for (const code of ['email-already-in-use', 'weak-password', 'too-many-requests', 'unauthorized-domain']) {
    assert.ok(login.includes(code), `no friendly message for ${code}`);
  }
  const client = read('frontend/js/api-client.js');
  assert.ok(!client.includes('API_BASE'), 'api client exposes API_BASE to users');
});

test('login degrades gracefully when backend is not deployed yet', () => {
  const login = read('frontend/js/page-login.js');
  assert.match(login, /isBackendReachable/);
  assert.match(login, /المنصة في مرحلة التجهيز/);
  assert.ok(!/await signInWithGoogle\(\); location\.href = 'dashboard\.html'/.test(login),
            'must not hard-redirect to dashboard without a backend check');
});
