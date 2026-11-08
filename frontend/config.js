// Public runtime configuration for the static Vercel frontend.
// Set this to the real HTTPS base URL of the separately hosted FastAPI service.
// Empty means same-origin API (useful when FastAPI itself serves the frontend).
// Never place Firebase service-account credentials or other secrets here.
window.CYBERLIFE_API_BASE = window.CYBERLIFE_API_BASE || '';
