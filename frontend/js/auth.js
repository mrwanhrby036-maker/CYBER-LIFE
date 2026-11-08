import { get, setToken, getToken } from './api-client.js';
import { USER_KEY } from './core-config.js';
import { firebaseConfig, isFirebaseConfigured } from './auth-firebase-config.js';
import { restoreFirebaseProfile } from './auth-session.js';

let firebaseApp = null;
let firebaseAuth = null;
let firebaseModules = null;
let firebaseInitPromise = null;
let authStateReady = null;
let authActionPending = false;

export function cachedUser() {
  try { return JSON.parse(localStorage.getItem(USER_KEY) || 'null'); }
  catch { return null; }
}

export function cacheUser(user) {
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  else localStorage.removeItem(USER_KEY);
}

export async function loadHealth() {
  return get('/api/health', { auth: false, silent: true });
}

// Health is only a connectivity check; it intentionally reveals no backend internals.
export async function isBackendReachable() {
  try {
    const health = await loadHealth();
    return health?.status === 'ok';
  } catch {
    return false;
  }
}

export async function ensureFirebase() {
  if (!isFirebaseConfigured()) {
    throw new Error('خدمة تسجيل الدخول غير مهيأة. يرجى التواصل مع إدارة المنصة.');
  }
  if (!firebaseInitPromise) {
    firebaseInitPromise = (async () => {
      const [appMod, authMod] = await Promise.all([
        import('https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js'),
        import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js')
      ]);
      firebaseModules = authMod;
      const existing = appMod.getApps().find(app => app.name === 'cyber-life');
      firebaseApp = existing || appMod.initializeApp(firebaseConfig, 'cyber-life');
      firebaseAuth = authMod.getAuth(firebaseApp);
      // Explicitly persist Firebase's own session. localStorage token is only a cache;
      // Firebase Auth remains the source of truth and refreshes ID tokens as needed.
      await authMod.setPersistence(firebaseAuth, authMod.browserLocalPersistence);
      authStateReady = new Promise((resolve, reject) => {
        let unsubscribe = () => {};
        try {
          unsubscribe = authMod.onAuthStateChanged(
            firebaseAuth,
            user => { unsubscribe(); resolve(user); },
            error => { unsubscribe(); reject(error); }
          );
        } catch (error) { reject(error); }
      });
      return firebaseAuth;
    })().catch(error => {
      firebaseInitPromise = null;
      firebaseAuth = null;
      firebaseApp = null;
      firebaseModules = null;
      authStateReady = null;
      throw error;
    });
  }
  return firebaseInitPromise;
}

async function firebaseUser() {
  await ensureFirebase();
  if (authStateReady) await authStateReady;
  return firebaseAuth.currentUser;
}

async function saveFirebaseToken(user) {
  if (!user) return '';
  const token = await user.getIdToken();
  setToken(token);
  return token;
}

async function withAuthAction(action) {
  if (authActionPending) {
    const error = new Error('توجد عملية تسجيل دخول قيد التنفيذ.');
    error.code = 'auth/in-progress';
    throw error;
  }
  authActionPending = true;
  try { return await action(); }
  finally { authActionPending = false; }
}

async function fetchCurrentProfile() {
  const me = await get('/api/auth/me', { silent: true });
  if (!me?.user?.uid || !me.user.role) {
    throw new Error('استجاب الخادم دون بيانات حساب صالحة.');
  }
  cacheUser(me.user);
  return me.user;
}

export async function signInWithGoogle() {
  return withAuthAction(async () => {
    await ensureFirebase();
    const credential = await firebaseModules.signInWithPopup(
      firebaseAuth, new firebaseModules.GoogleAuthProvider()
    );
    await saveFirebaseToken(credential.user);
    // Keep the Firebase session on transient API failures; the next page load can
    // restore it and retry /me rather than prompting the person to sign in again.
    return fetchCurrentProfile();
  });
}

export async function signInWithEmail(email, password) {
  return withAuthAction(async () => {
    await ensureFirebase();
    const credential = await firebaseModules.signInWithEmailAndPassword(firebaseAuth, email, password);
    await saveFirebaseToken(credential.user);
    return fetchCurrentProfile();
  });
}

export async function signUpWithEmail(email, password, displayName) {
  return withAuthAction(async () => {
    await ensureFirebase();
    const credential = await firebaseModules.createUserWithEmailAndPassword(firebaseAuth, email, password);
    if (displayName) await firebaseModules.updateProfile(credential.user, { displayName });
    try { await firebaseModules.sendEmailVerification(credential.user); } catch { /* optional */ }
    await saveFirebaseToken(credential.user);
    return fetchCurrentProfile();
  });
}

export async function hasRestoredFirebaseUser() {
  const existingToken = getToken();
  if (existingToken.startsWith('local.')) return Boolean(cachedUser());
  const user = await firebaseUser();
  if (!user) {
    setToken('');
    cacheUser(null);
    return false;
  }
  await saveFirebaseToken(user);
  return true;
}

export async function restoreUserSession() {
  // Development's signed local token doesn't require Firebase. Production Firebase
  // tokens are always regenerated from the persisted Firebase User on every load.
  const existingToken = getToken();
  if (existingToken.startsWith('local.')) return fetchCurrentProfile();
  return restoreFirebaseProfile({
    getCurrentUser: firebaseUser,
    getIdToken: user => user.getIdToken(),
    requestProfile: () => get('/api/auth/me', { silent: true }),
    setToken,
    cacheUser,
    clearSession: () => { setToken(''); cacheUser(null); }
  });
}

export async function signOut() {
  try {
    if (isFirebaseConfigured()) {
      await ensureFirebase();
      await firebaseModules.signOut(firebaseAuth);
    }
  } catch {
    // Always clear the local application session; the SDK can be unavailable offline.
  } finally {
    setToken('');
    cacheUser(null);
  }
}

export async function requireUser() {
  let user;
  try {
    user = await restoreUserSession();
  } catch (error) {
    // A revoked/expired credential requires a fresh login; network/5xx failures do
    // not. Never erase a valid Firebase session just because the API is offline.
    if (error?.status === 401) {
      await signOut();
      location.replace('login.html');
    } else if (error?.status === 0 || error?.status === 404 || error?.status >= 500) {
      // The login page recognizes the persisted Firebase user and offers a backend
      // retry without presenting another sign-in prompt or discarding the session.
      location.replace('login.html');
    }
    throw error;
  }
  if (!user) {
    location.replace('login.html');
    throw new Error('redirect');
  }
  return user;
}

export async function refreshFirebaseToken() {
  const user = await firebaseUser();
  if (!user) return getToken();
  return saveFirebaseToken(user);
}
