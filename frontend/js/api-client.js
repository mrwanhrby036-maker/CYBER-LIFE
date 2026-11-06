import { apiUrl, TOKEN_KEY } from './core-config.js';
import { toast } from './core-toast.js';

export class ApiError extends Error {
  constructor(status, code, message, details) { super(message); this.status = status; this.code = code; this.details = details; }
}
export function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
export function setToken(token) { token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY); }

export async function api(path, { method = 'GET', body, auth = true, silent = false } = {}) {
  const headers = { 'Accept': 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (auth && token) headers['Authorization'] = `Bearer ${token}`;
  let response;
  try {
    response = await fetch(apiUrl(path), { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch (err) {
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
