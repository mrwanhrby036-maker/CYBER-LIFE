// إعداد تطبيق الويب في مشروع Firebase القائم: hamo-8132e
// هذه القيم عامة بطبيعتها (تظهر في المتصفح لأي زائر) وليست أسراراً.
// الحماية الحقيقية من قواعد Realtime Database + تحقق الخادم من الرمز + Authorized domains.
// ممنوع وضع مفتاح Admin SDK أو أي ملف خدمة هنا.
export const firebaseConfig = {
  apiKey: 'AIzaSyBzHHBny7xzUMyi8EouXtf1BFk7_5Qo8tg',
  authDomain: 'hamo-8132e.firebaseapp.com',
  databaseURL: 'https://hamo-8132e-default-rtdb.europe-west1.firebasedatabase.app',
  projectId: 'hamo-8132e',
  storageBucket: 'hamo-8132e.firebasestorage.app',
  messagingSenderId: '791335303883',
  appId: '1:791335303883:web:637e0d0b7d09aac2b4b94e'
};

// لا تعتبر الواجهة جاهزة إلا إذا كانت القيم المطلوبة موجودة فعلاً.
export function isFirebaseConfigured() {
  return Boolean(firebaseConfig.apiKey && firebaseConfig.appId
                 && firebaseConfig.projectId && firebaseConfig.databaseURL);
}
