import { el } from './core-dom.js';
let region;
function ensureRegion() {
  if (!region) { region = el('div', { class: 'toast-region', 'aria-live': 'polite' }); document.body.append(region); }
  return region;
}
export function toast(message, type = 'info', timeout = 4200) {
  const node = el('div', { class: `toast ${type}`, role: 'status', text: message });
  ensureRegion().append(node);
  setTimeout(() => { node.remove(); }, timeout);
  return node;
}
