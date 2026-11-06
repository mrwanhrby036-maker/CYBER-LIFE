#!/usr/bin/env bash
# ارفع المشروع إلى GitHub بعد إنشاء repo فارغ باسم CYBER-LIFE
# الاستخدام: bash scripts/push_to_github.sh <اسم-المستخدم-على-GitHub>
set -euo pipefail
cd "$(dirname "$0")/.."
USER="${1:-}"
if [ -z "$USER" ]; then
  echo "الاستخدام: bash scripts/push_to_github.sh <اسم-المستخدم-على-GitHub>"
  exit 1
fi

echo "=== فحص أخير قبل الرفع: لا أسرار ==="
if git ls-files | grep -E "\.env$|service-account|\.data/|credentials|signing-key"; then
  echo "!!! توقف — يوجد ملف سرّي متتبع. لا ترفع."
  exit 1
fi
echo "نظيف ✓"

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$USER/CYBER-LIFE.git"
git branch -M main
git push -u origin main

echo
echo "تم الرفع ✓"
echo "الخطوة التالية: افتح https://vercel.com/new واختر CYBER-LIFE"
