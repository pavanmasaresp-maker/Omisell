# Permanent database (Neon, free) — Render ke 30 din wale Postgres ki jagah

Code mein kuch badalna nahi: backend `DATABASE_URL` se hi DB lega.

1. neon.com par Gmail se sign up. Create project (Region: Singapore ya Mumbai ke paas wala, Postgres 16/17).
2. Dashboard > "Connect" > Connection string copy karo (`postgresql://...neon.tech/...?sslmode=require`).
   Ye string SECRET hai: chat/GitHub mein mat daalo.
3. Render > omnisell-api > Environment > DATABASE_URL ko is string se replace karo > Save.
   (SECRET_KEY kabhi mat badalna.)
4. Render apne aap redeploy karega. start.sh migrate chalata hai, naye DB mein saari tables ban jati hain.
5. Naya DB khali hota hai, to pehle wala test data nahi aayega. App mein dobara login karo (naya tenant ban jayega).
   ADMIN_EMAIL wala user pehle se jud jayega.
6. Test: app mein ek product banao, Render ko "Manual Deploy" karke dekho ki product bacha rehta hai.

Limits (free): 1 GB, 5 min idle par suspend (pehli request 1-2 sec dheeri), 6 ghante ki history.
Backup: Neon > Branches / Restore se. Paid users aane par Neon Launch plan lo.
Purana Render DB 30 din baad apne aap delete hoga, usse bhi hata do.
