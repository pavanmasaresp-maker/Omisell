# Google (Firebase) login setup

## A. Firebase project (phone ke Chrome mein)
1. console.firebase.google.com > Create project (Google Analytics band kar do).
2. Build > Authentication > Get started > Sign-in method > Google > Enable (support email chuno) > Save.
   Phir wahin "Add new provider" > Email/Password > Enable > Save (email se login ke liye).
3. Project settings (gear) > General > "Project ID" copy karo -> Render mein FIREBASE_PROJECT_ID.
4. Project settings > Add app > Android:
   - Package name: com.omnisell.app
   - SHA-1: Codespace mein ye chalao:
     keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android | grep SHA1
5. google-services.json download karo, GitHub repo mein mobile/google-services.json naam se upload karo.
   (Ye secret nahi hai, public identifiers hain.)

## B. Render > Environment
- FIREBASE_PROJECT_ID = <Project ID>
- ADMIN_EMAIL = tumhara gmail (purana admin user isi email se jud jayega)
- Optional: GOOGLE_SIGNUP=0 (naye accounts band), FIREBASE_ALLOWED_EMAILS=a@gmail.com,b@gmail.com

## C. Codespace build
cd /workspaces/Omisell/mobile && npm install        (agar peer error aaye: npm install --legacy-peer-deps)
npx cap sync android
cp google-services.json android/app/google-services.json

mobile/android/variables.gradle mein ye do cheezein zaroor rakho:
  minSdkVersion = 23
  rgcfaIncludeGoogle = true        (iske bina Google login par app crash hoti hai: NoClassDefFoundError GoogleSignIn)

Gradle 8.2 ko JDK 17 chahiye:
  cd android && JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew assembleDebug

Note: app plain JS hai, plugin `Capacitor.Plugins.FirebaseAuthentication` se milta hai (registerPlugin nahi).
Note: mobile/android/ gitignored hai, isliye ye gradle changes git mein save nahi hote; naya Codespace ho to dobara karo.

Release build (Play Store) ki alag SHA-1 hogi: wo bhi Firebase mein add karni hogi.

## D. Phase 6 (orders pull, export, Play Store pages)
- Shopify token ko ab `read_orders` scope bhi chahiye (orders kheenchne ke liye).
- Render env (optional): ORDER_PULL_SECONDS=300 (har kitne second mein marketplace se naye orders; 0 = band), SUPPORT_EMAIL.
- Public pages (Play Store ke liye URL): https://<tumhara-render-url>/privacy aur /account-delete
