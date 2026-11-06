import { signInWithGoogle, signInWithEmail, signUpWithEmail, cachedUser, isBackendReachable } from './auth.js';
import { isFirebaseConfigured } from './auth-firebase-config.js';
import { getToken } from './api-client.js';
import { qs } from './core-dom.js';
import { validateForm, formData, setBusy } from './core-forms.js';
import { toast } from './core-toast.js';
import { icon } from './core-icons.js';

const root = qs('#authRoot');
if (getToken() && cachedUser()) location.replace('dashboard.html');

// رسائل مفهومة للمستخدم بدل رموز الأخطاء التقنية.
function friendlyError(err) {
  const code = String(err?.code || err?.message || '');
  if (code.includes('email-already-in-use')) return 'البريد الإلكتروني مسجّل بالفعل. جرّب تسجيل الدخول.';
  if (code.includes('invalid-email')) return 'البريد الإلكتروني غير صحيح.';
  if (code.includes('weak-password')) return 'كلمة المرور ضعيفة. استخدم ٨ أحرف على الأقل.';
  if (code.includes('wrong-password') || code.includes('invalid-credential') || code.includes('invalid-login-credentials'))
    return 'البريد الإلكتروني أو كلمة المرور غير صحيحة.';
  if (code.includes('user-not-found')) return 'لا يوجد حساب بهذا البريد. أنشئ حساباً جديداً.';
  if (code.includes('too-many-requests')) return 'محاولات كثيرة. انتظر قليلاً ثم حاول مرة أخرى.';
  if (code.includes('popup-closed') || code.includes('cancelled-popup')) return 'تم إغلاق نافذة الدخول قبل الإكمال.';
  if (code.includes('popup-blocked')) return 'المتصفح منع النافذة المنبثقة. اسمح بها ثم حاول مرة أخرى.';
  if (code.includes('unauthorized-domain')) return 'هذا النطاق غير مضاف بعد لإعدادات الدخول. تواصل مع إدارة المنصة.';
  if (code.includes('operation-not-allowed')) return 'طريقة الدخول هذه غير متاحة حالياً. تواصل مع إدارة المنصة.';
  if (code.includes('network')) return 'تعذر الاتصال بالخدمة. تحقق من اتصالك بالإنترنت.';
  if (err?.status === 0) return 'تعذر الاتصال بالخدمة. حاول مرة أخرى بعد قليل.';
  return 'تعذر إكمال العملية. حاول مرة أخرى.';
}

function render(backendOnline = true) {
  const ready = isFirebaseConfigured();
  root.innerHTML = `
    <div class="auth-brand">
      <div class="brand-logo" style="margin:0 auto 0.6rem;width:52px;height:52px;font-size:1.2rem">CL</div>
      <h1>CYBER LIFE</h1>
      <p class="muted">سجّل الدخول للمتابعة إلى فريقك ومهامك</p>
    </div>
    ${!backendOnline ? `
      <div class="alert info mb-2" style="font-size:.9rem;line-height:1.8">
        المنصة في مرحلة التجهيز. يمكنك إنشاء حسابك الآن، وستُفتح الدروس والمهام
        بمجرد اكتمال ربط الخدمة. تابعنا قريبًا.
      </div>
    ` : ''}
    ${ready ? `
      <button class="btn primary" id="googleBtn" type="button" style="width:100%">
        ${icon('google')}<span>المتابعة باستخدام Google</span>
      </button>
      <div class="divider"></div>
      <div class="tabs" role="tablist">
        <button class="tab active" type="button" data-tab="login">دخول</button>
        <button class="tab" type="button" data-tab="signup">حساب جديد</button>
      </div>
      <form id="loginForm" novalidate>
        <div class="field"><label for="loginEmail">البريد الإلكتروني</label><input class="input" id="loginEmail" name="email" type="email" data-validate="required|email" autocomplete="email"><div class="error"></div></div>
        <div class="field"><label for="loginPassword">كلمة المرور</label><input class="input" id="loginPassword" name="password" type="password" data-validate="required|min:8" autocomplete="current-password"><div class="error"></div></div>
        <button class="btn" type="submit" style="width:100%">دخول</button>
      </form>
      <form id="signupForm" novalidate hidden>
        <div class="field"><label for="signupName">الاسم</label><input class="input" id="signupName" name="displayName" data-validate="required|min:3|max:60" autocomplete="name"><div class="error"></div></div>
        <div class="field"><label for="signupEmail">البريد الإلكتروني</label><input class="input" id="signupEmail" name="email" type="email" data-validate="required|email" autocomplete="email"><div class="error"></div></div>
        <div class="field"><label for="signupPassword">كلمة المرور</label><input class="input" id="signupPassword" name="password" type="password" data-validate="required|min:8" autocomplete="new-password"><div class="error"></div></div>
        <button class="btn primary" type="submit" style="width:100%">إنشاء حساب</button>
      </form>
      <p class="muted mt-2" style="font-size:.85rem;text-align:center">
        سيتم إنشاء ملفك التدريبي تلقائيًا عند أول دخول.
      </p>
    ` : `
      <div class="alert warn mb-2">
        خدمة تسجيل الدخول غير متاحة حاليًا. يرجى المحاولة لاحقًا أو التواصل مع إدارة المنصة.
      </div>
    `}
    <div class="footer-note">
      باستخدامك للمنصة أنت تلتزم بالتدريب المسؤول وعدم فحص أنظمة حقيقية دون تفويض.
      <br><a href="index.html">العودة إلى الصفحة الرئيسية</a>
    </div>`;

  // بعد نجاح الدخول: انتقل للوحة فقط لو الخدمة متاحة، وإلا اعرض حالة واضحة.
  const afterSignIn = () => {
    if (backendOnline) { location.href = 'dashboard.html'; return; }
    toast('تم إنشاء حسابك بنجاح. الدروس والمهام ستُفتح بعد اكتمال التجهيز.', 'success');
    location.href = 'index.html';
  };

  const googleBtn = qs('#googleBtn');
  if (googleBtn) googleBtn.addEventListener('click', async () => {
    setBusy(googleBtn, true, 'جارٍ الدخول…');
    try { await signInWithGoogle(); afterSignIn(); }
    catch (err) { toast(friendlyError(err), 'error'); setBusy(googleBtn, false); }
  });

  for (const tab of root.querySelectorAll('[data-tab]')) {
    tab.addEventListener('click', () => {
      root.querySelectorAll('[data-tab]').forEach(t => t.classList.toggle('active', t === tab));
      qs('#loginForm').hidden = tab.dataset.tab !== 'login';
      qs('#signupForm').hidden = tab.dataset.tab !== 'signup';
    });
  }

  const loginForm = qs('#loginForm');
  if (loginForm) loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateForm(loginForm)) return;
    const btn = loginForm.querySelector('button[type=submit]');
    setBusy(btn, true, 'جارٍ الدخول…');
    try { const data = formData(loginForm); await signInWithEmail(data.email, data.password); afterSignIn(); }
    catch (err) { toast(friendlyError(err), 'error'); setBusy(btn, false); }
  });

  const signupForm = qs('#signupForm');
  if (signupForm) signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateForm(signupForm)) return;
    const btn = signupForm.querySelector('button[type=submit]');
    setBusy(btn, true, 'جارٍ إنشاء الحساب…');
    try { const data = formData(signupForm); await signUpWithEmail(data.email, data.password, data.displayName); afterSignIn(); }
    catch (err) { toast(friendlyError(err), 'error'); setBusy(btn, false); }
  });
}

// افحص الخدمة مرة واحدة عند فتح الشاشة، ولا تعطّل النموذج إذا كانت غير متاحة.
isBackendReachable().then(render);
