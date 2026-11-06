# ارفع المشروع إلى GitHub — نسخة Windows
# الاستخدام: افتح PowerShell داخل مجلد المشروع واكتب:
#   powershell -ExecutionPolicy Bypass -File scripts\push_to_github.ps1
# أو اضغط يمين على الملف واختر "Run with PowerShell"

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host ""
Write-Host "=== CYBER LIFE - رفع إلى GitHub ===" -ForegroundColor Cyan
Write-Host ""

# هل Git مثبّت؟
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "Git غير مثبّت على جهازك." -ForegroundColor Red
    Write-Host ""
    Write-Host "حمّله من: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "ثبّته ثم شغّل هذا الملف مرة أخرى."
    Write-Host ""
    Write-Host "أو ارفع الملفات يدويًا من موقع GitHub (الطريقة الثانية في START_HERE_AR.txt)"
    Read-Host "اضغط Enter للخروج"
    exit 1
}

# فحص الأسرار قبل الرفع
Write-Host "فحص أخير: لا توجد أسرار..." -ForegroundColor Cyan
if (-not (Test-Path ".git")) {
    git init --quiet
    git add -A
    git -c user.email="dev@cyberlife.local" -c user.name="CYBER LIFE" commit -q -m "CYBER LIFE platform"
}

$tracked = git ls-files
$leaks = $tracked | Where-Object {
    ($_ -match '\.env$') -or
    ($_ -match 'service-account') -or
    ($_ -match '\.data/') -or
    ($_ -match 'credentials') -or
    ($_ -match 'signing-key')
}
if ($leaks) {
    Write-Host "توقف - يوجد ملف سري متتبع:" -ForegroundColor Red
    $leaks | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Read-Host "اضغط Enter للخروج"
    exit 1
}
Write-Host "نظيف" -ForegroundColor Green
Write-Host ""

# الرفع
git remote remove origin 2>$null
git remote add origin "https://github.com/mrwanhrby036-maker/CYBER-LIFE.git"
git branch -M main

Write-Host "جارٍ الرفع..." -ForegroundColor Cyan
Write-Host "قد تُفتح نافذة لتسجيل الدخول إلى GitHub - سجّل الدخول وأكمل." -ForegroundColor Yellow
Write-Host ""
git push -u origin main

Write-Host ""
Write-Host "تم الرفع بنجاح" -ForegroundColor Green
Write-Host "أبلغ المساعد أن الرفع اكتمل ليُنشر الموقع على Vercel." -ForegroundColor Cyan
Write-Host ""
Read-Host "اضغط Enter للخروج"
