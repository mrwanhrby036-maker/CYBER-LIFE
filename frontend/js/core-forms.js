import { qsa } from './core-dom.js';
export function validateForm(form) {
  let valid = true;
  qsa('[data-validate]', form).forEach(input => {
    const field = input.closest('.field');
    const error = field?.querySelector('.error');
    let message = '';
    const value = input.value.trim();
    const rules = (input.dataset.validate || '').split('|');
    for (const rule of rules) {
      if (rule === 'required' && !value) message = 'هذا الحقل مطلوب';
      if (rule.startsWith('min:')) { const n = Number(rule.split(':')[1]); if (value.length < n) message = `الحد الأدنى ${n} حرفاً`; }
      if (rule.startsWith('max:')) { const n = Number(rule.split(':')[1]); if (value.length > n) message = `الحد الأقصى ${n} حرفاً`; }
      if (rule === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) message = 'بريد إلكتروني غير صالح';
      if (rule === 'json' && value) { try { JSON.parse(value); } catch { message = 'JSON غير صالح'; } }
    }
    if (field) field.classList.toggle('invalid', Boolean(message));
    if (error) error.textContent = message;
    if (message) valid = false;
  });
  return valid;
}
export function formData(form) {
  const data = {};
  new FormData(form).forEach((value, key) => { data[key] = value; });
  return data;
}
export function setBusy(button, busy, label) {
  if (!button) return;
  if (busy) { button.dataset.label = button.textContent; button.disabled = true; button.textContent = label || 'جارٍ التنفيذ…'; }
  else { button.disabled = false; button.textContent = button.dataset.label || button.textContent; }
}
