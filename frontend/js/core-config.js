// Public runtime configuration. Keep secrets out of browser JavaScript.
const configuredBase = typeof window.CYBERLIFE_API_BASE === 'string'
  ? window.CYBERLIFE_API_BASE.trim()
  : '';

let apiConfigError = '';
let API_BASE = '';
if (configuredBase) {
  try {
    const url = new URL(configuredBase);
    const localHosts = new Set(['localhost', '127.0.0.1', '::1']);
    const pageHost = window.location.hostname.toLowerCase().replace(/^\[|\]$/g, '');
    const apiHost = url.hostname.toLowerCase().replace(/^\[|\]$/g, '');
    const remotePage = !localHosts.has(pageHost);
    const loopbackApi = localHosts.has(apiHost);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password
        || url.search || url.hash || !['', '/'].includes(url.pathname)
        || (window.location.protocol === 'https:' && url.protocol !== 'https:')
        || (remotePage && loopbackApi)) {
      throw new Error('عنوان API يجب أن يكون جذر HTTPS صالحًا، ولا يجوز أن يشير إلى localhost في الإنتاج.');
    }
    API_BASE = url.origin;
  } catch (error) {
    apiConfigError = error.message || 'عنوان API غير صالح.';
  }
}

export { API_BASE };
export const API_CONFIG_ERROR = apiConfigError;
export const APP_NAME = 'CYBER LIFE';
export const TOKEN_KEY = 'cyberlife_token';
export const USER_KEY = 'cyberlife_user';
export function apiUrl(path) {
  if (API_CONFIG_ERROR) {
    const error = new Error(API_CONFIG_ERROR);
    error.code = 'api_config_error';
    throw error;
  }
  const route = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${route}`;
}
