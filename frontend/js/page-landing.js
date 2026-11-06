import { getToken } from './api-client.js';
import { cachedUser } from './auth.js';

const loggedIn = Boolean(getToken() && cachedUser());
for (const id of ['navCta', 'heroCta']) {
  const el = document.getElementById(id);
  if (el && loggedIn) {
    el.href = 'dashboard.html';
    el.textContent = 'اذهب إلى لوحتي';
  }
}
