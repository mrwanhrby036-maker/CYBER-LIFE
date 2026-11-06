import { get, setToken, getToken } from './api-client.js';
import { USER_KEY } from './core-config.js';
import { firebaseConfig, isFirebaseConfigured } from './auth-firebase-config.js';

let firebaseApp = null, firebaseAuth = null, googleProvider = null;

export function cachedUser() { try { return JSON.parse(localStorage.getItem(USER_KEY) || 'null'); } catch { return null; } }
export function cacheUser(user) { user ? localStorage.setItem(USER_KEY, JSON.stringify(user)) : localStorage.removeItem(USER_KEY); }

export async function loadHealth() { return get('/api/health', { auth: false, silent: true }); }

// هل الخدمة الخلفية متاحة فعلاً؟ تُستخدم لعرض حالة واضحة بدل فشل غامض بعد الدخول.
export async function isBackendReachable() {
  try { await loadHealth(); return true; } catch { return false; }
}

export async function ensureFirebase() {
  if (!isFirebaseConfigured()) throw new Error('خدمة تسجيل الدخول غير متاحة حاليًا. حاول لاحقًا.');
  if (firebaseAuth) return firebaseAuth;
  const appMod = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js');
  const authMod = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
  firebaseApp = appMod.initializeApp(firebaseConfig);
  firebaseAuth = authMod.getAuth(firebaseApp);
  googleProvider = new authMod.GoogleAuthProvider();
  return firebaseAuth;
}

export async function signInWithGoogle() {
  const auth = await ensureFirebase();
  const authMod = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
  const cred = await authMod.signInWithPopup(auth, googleProvider);
  const idToken = await cred.user.getIdToken();
  setToken(idToken);
  const me = await get('/api/auth/me');
  cacheUser(me.user);
  return me.user;
}

export async function signInWithEmail(email, password) {
  const auth = await ensureFirebase();
  const authMod = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
  const cred = await authMod.signInWithEmailAndPassword(auth, email, password);
  const idToken = await cred.user.getIdToken();
  setToken(idToken);
  const me = await get('/api/auth/me');
  cacheUser(me.user);
  return me.user;
}

export async function signUpWithEmail(email, password, displayName) {
  const auth = await ensureFirebase();
  const authMod = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
  const cred = await authMod.createUserWithEmailAndPassword(auth, email, password);
  if (displayName) await authMod.updateProfile(cred.user, { displayName });
  try { await authMod.sendEmailVerification(cred.user); } catch { /* optional */ }
  const idToken = await cred.user.getIdToken();
  setToken(idToken);
  const me = await get('/api/auth/me');
  cacheUser(me.user);
  return me.user;
}

export async function signOut() {
  try {
    if (firebaseAuth) {
      const authMod = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
      await authMod.signOut(firebaseAuth);
    }
  } catch { /* ignore client signout errors */ }
  setToken(''); cacheUser(null);
}

export async function requireUser() {
  if (!getToken()) { location.href = 'login.html'; throw new Error('redirect'); }
  try {
    const me = await get('/api/auth/me', { silent: true });
    cacheUser(me.user);
    return me.user;
  } catch (err) {
    setToken(''); cacheUser(null); location.href = 'login.html'; throw err;
  }
}

export async function refreshFirebaseToken() {
  if (firebaseAuth?.currentUser) {
    const token = await firebaseAuth.currentUser.getIdToken(true);
    setToken(token);
    return token;
  }
  return getToken();
}
