import { apiUrl, TOKEN_KEY } from './core-config.js';
import { toast } from './core-toast.js';

export class ApiError extends Error {
  constructor(status, code, message, details) { super(message); this.status = status; this.code = code; this.details = details; }
}
let memoryFirebaseToken = '';
export function getToken() {
  const persisted = localStorage.getItem(TOKEN_KEY) || '';
  // Local-development bearer tokens are app-owned; Firebase ID tokens remain only
  // in memory and are rehydrated from Firebase Auth after each full-page navigation.
  return persisted.startsWith('local.') ? persisted : memoryFirebaseToken;
}
export function setToken(token) {
  const value = token || '';
  if (value.startsWith('local.')) {
    memoryFirebaseToken = '';
    localStorage.setItem(TOKEN_KEY, value);
  } else {
    memoryFirebaseToken = value;
    localStorage.removeItem(TOKEN_KEY);
  }
}

export async function api(path, { method = 'GET', body, auth = true, silent = false } = {}) {
  const headers = { 'Accept': 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (auth && token) headers['Authorization'] = `Bearer ${token}`;
  let requestUrl;
  try { requestUrl = apiUrl(path); }
  catch (err) { throw new ApiError(0, err?.code || 'api_config_error', err?.message || 'عنوان API غير صالح'); }
  let response;
  try {
    response = await fetch(requestUrl, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch {
    if (!silent) toast('تعذر الاتصال بالخدمة. تحقق من اتصالك بالإنترنت وحاول مرة أخرى.', 'error');
    throw new ApiError(0, 'network_error', 'تعذر الاتصال بالخدمة');
  }
  let data = null;
  const text = await response.text();
  try { data = text ? JSON.parse(text) : null; } catch { data = null; }
  if (!response.ok) {
    const error = data?.error || {};
    const apiError = new ApiError(response.status, error.code || 'http_error', error.message || `خطأ ${response.status}`, error.details);
    if (!silent) {
      if (response.status === 401) { setToken(''); }
      toast(apiError.message, 'error');
    }
    throw apiError;
  }
  return data;
}
export const get = (path, opts) => api(path, opts);
export const post = (path, body, opts) => api(path, { ...opts, method: 'POST', body });
export const put = (path, body, opts) => api(path, { ...opts, method: 'PUT', body });
export const patch = (path, body, opts) => api(path, { ...opts, method: 'PATCH', body });
