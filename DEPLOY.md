# OmniSell: Render deploy

1. GitHub pe push karo (render.yaml repo root mein hai).
2. Render > New > Blueprint > Omisell repo chuno. Ye `omnisell-api` web service banata hai.
3. Database: Render > New > PostgreSQL (ya Neon/Supabase). Internal/connection URL copy karo.
4. omnisell-api > Environment mein ye daalo:
   - DATABASE_URL = postgres://...
   - ADMIN_USERNAME = tumhara username
   - ADMIN_PASSWORD = strong password
5. Deploy ke baad URL milega: https://omnisell-api.onrender.com
   Check: https://omnisell-api.onrender.com/healthz  -> "ok"
6. App mein mobile/www/config.js: const API_URL = "https://omnisell-api.onrender.com";
   phir: cd mobile && npx cap sync android && APK dobara banao.

Dhyan:
- SECRET_KEY kabhi mat badlo (channel tokens usi se encrypt hote hain).
- Free plan 15 min idle ke baad so jata hai; pehli request ~50 sec leti hai.
- Free Postgres kuch din baad expire hota hai: asli use ke liye paid DB ya Neon lo.
