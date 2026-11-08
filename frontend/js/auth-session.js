// Framework-free auth persistence logic, kept separate so restoration semantics can
// be unit-tested without a live Firebase project or browser popup.
export async function restoreFirebaseProfile({
  getCurrentUser, getIdToken, requestProfile, setToken, cacheUser, clearSession
}) {
  const firebaseUser = await getCurrentUser();
  if (!firebaseUser) {
    clearSession();
    return null;
  }

  // Firebase Auth is the session source of truth. Refresh its ID token on every page
  // load before asking the backend for the authoritative profile and role.
  const token = await getIdToken(firebaseUser);
  setToken(token);
  const result = await requestProfile();
  if (!result?.user?.uid || !result.user.role) {
    throw new Error('استجاب الخادم دون بيانات حساب صالحة.');
  }
  cacheUser(result.user);
  return result.user;
}
