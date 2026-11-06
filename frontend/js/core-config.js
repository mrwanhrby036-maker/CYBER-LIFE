// إعداد الواجهة. لا تضع أسراراً هنا. عند نشر الواجهة منفصلة عن الخادم عدّل API_BASE.
export const API_BASE = (window.CYBERLIFE_API_BASE || '').replace(/\/$/, '');
export const APP_NAME = 'CYBER LIFE';
export const TOKEN_KEY = 'cyberlife_token';
export const USER_KEY = 'cyberlife_user';
export function apiUrl(path) { return `${API_BASE}${path.startsWith('/') ? path : '/' + path}`; }
