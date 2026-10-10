# Google (Firebase) login setup

## A. Firebase project (phone ke Chrome mein)
1. console.firebase.google.com > Create project (Google Analytics band kar do).
2. Build > Authentication > Get started > Sign-in method > Google > Enable (support email chuno) > Save.
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
cd android && JAVA_HOME=... ./gradlew assembleDebug

Agar error aaye "minSdkVersion 22 cannot be smaller than 23":
  mobile/android/variables.gradle mein minSdkVersion = 23 kar do.

Release build (Play Store) ki alag SHA-1 hogi: wo bhi Firebase mein add karni hogi.
