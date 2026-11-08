import { test } from 'node:test';
import assert from 'node:assert/strict';
import { restoreFirebaseProfile } from '../frontend/js/auth-session.js';

const profile = { uid: 'firebase-user-1', email: 'learner@example.com', role: 'student' };

test('restores Firebase session, refreshes ID token, and fetches the backend profile', async () => {
  const events = [];
  const result = await restoreFirebaseProfile({
    getCurrentUser: async () => ({ uid: profile.uid }),
    getIdToken: async user => { events.push(`token:${user.uid}`); return 'fresh-id-token'; },
    requestProfile: async () => { events.push('api:/api/auth/me'); return { user: profile }; },
    setToken: token => events.push(`store-token:${token}`),
    cacheUser: user => events.push(`cache-user:${user.uid}`),
    clearSession: () => events.push('clear')
  });
  assert.deepEqual(result, profile);
  assert.deepEqual(events, [
    'token:firebase-user-1', 'store-token:fresh-id-token',
    'api:/api/auth/me', 'cache-user:firebase-user-1'
  ]);
});

test('clears stale cached application state when Firebase has no persisted user', async () => {
  const events = [];
  const result = await restoreFirebaseProfile({
    getCurrentUser: async () => null,
    getIdToken: async () => { throw new Error('must not request a token'); },
    requestProfile: async () => { throw new Error('must not call the API'); },
    setToken: token => events.push(`token:${token}`),
    cacheUser: user => events.push(`cache:${user}`),
    clearSession: () => events.push('clear')
  });
  assert.equal(result, null);
  assert.deepEqual(events, ['clear']);
});

test('keeps Firebase token and session when backend is temporarily unavailable', async () => {
  const events = [];
  await assert.rejects(() => restoreFirebaseProfile({
    getCurrentUser: async () => ({ uid: profile.uid }),
    getIdToken: async () => 'fresh-id-token',
    requestProfile: async () => { throw Object.assign(new Error('offline'), { status: 0 }); },
    setToken: token => events.push(`token:${token}`),
    cacheUser: () => events.push('cache'),
    clearSession: () => events.push('clear')
  }), error => error.status === 0);
  assert.deepEqual(events, ['token:fresh-id-token']);
});
