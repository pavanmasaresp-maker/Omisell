// Pehli baar login ke baad dikhne wala guide. Text teeno bhasha mein yahin likha hai (data-no-i18n: i18n.js ise nahi chhuta).
(function () {
  const KEY = "omnisell_tour_v1";
  const IC = {
    home: "M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
    box: "M3 7l9-4 9 4-9 4zM3 7v10l9 4V11M21 7v10l-9 4",
    bars: "M4 20V10M10 20V4M16 20v-7M22 20H2",
    list: "M6 3h12l2 4v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7zM4 7h16M9 11h6",
    link: "M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1",
    down: "M12 3v12m0 0l-4-4m4 4l4-4M4 20h16",
  };
  const S = [
    { ic: "home",
      hinglish: ["OmniSell mein swagat hai", "Ek hi app se apne saare marketplaces ke products, stock aur orders sambhalo. Ye 1 minute ka guide hai."],
      english: ["Welcome to OmniSell", "Manage products, stock and orders of all your marketplaces from one app. This is a 1-minute guide."],
      hindi: ["OmniSell में स्वागत है", "एक ही ऐप से अपने सारे मार्केटप्लेस के प्रोडक्ट, स्टॉक और ऑर्डर संभालो। यह 1 मिनट की गाइड है।"] },
    { ic: "box",
      hinglish: ["1. Product add karo", "Products tab mein 'Add product' dabao. Naam, SKU code (har product ka alag code) aur price bharo. Bas, product ban gaya."],
      english: ["1. Add a product", "In the Products tab tap 'Add product'. Fill in the name, SKU code (a unique code per product) and price. Done, the product is created."],
      hindi: ["1. प्रोडक्ट जोड़ो", "प्रोडक्ट्स टैब में 'प्रोडक्ट जोड़ो' दबाओ। नाम, SKU कोड (हर प्रोडक्ट का अलग कोड) और कीमत भरो। बस, प्रोडक्ट बन गया।"] },
    { ic: "bars",
      hinglish: ["2. Stock daalo", "Stock tab mein SKU kholo, quantity chuno aur Add dabao. Kam karna ho to Remove. Har badlav History mein dikhta hai."],
      english: ["2. Add stock", "In the Stock tab open a SKU, choose the quantity and tap Add. Tap Remove to reduce it. Every change shows in History."],
      hindi: ["2. स्टॉक डालो", "स्टॉक टैब में SKU खोलो, मात्रा चुनो और 'जोड़ो' दबाओ। कम करना हो तो 'हटाओ'। हर बदलाव हिस्ट्री में दिखता है।"] },
    { ic: "link",
      hinglish: ["3. Channel connect karo", "More > Channels > Connect a channel. Pehle 'Demo' chuno aur token mein demo likho: bina asli store ke poora flow try kar sakte ho. Baad mein Shopify ya WooCommerce jodo."],
      english: ["3. Connect a channel", "More > Channels > Connect a channel. First pick 'Demo' and type demo as the token: you can try the whole flow without a real store. Later connect Shopify or WooCommerce."],
      hindi: ["3. चैनल जोड़ो", "और > चैनल > चैनल जोड़ो। पहले 'डेमो' चुनो और टोकन में demo लिखो: बिना असली स्टोर के पूरा फ़्लो आज़मा सकते हो। बाद में Shopify या WooCommerce जोड़ो।"] },
    { ic: "list",
      hinglish: ["4. Orders sambhalo", "Naya order aate hi stock apne aap reserve ho jata hai. Order par Confirm, Pack, Ship, Delivered dabate jao. Channel par 'Auto confirm' ya 'Auto pack' chuno to ye kaam khud ho jayega. Demo mein 'Test order' dabao."],
      english: ["4. Handle orders", "When a new order arrives its stock is reserved automatically. Tap Confirm, Pack, Ship, Delivered on the order. Pick 'Auto confirm' or 'Auto pack' on a channel and that happens by itself. In Demo tap 'Test order'."],
      hindi: ["4. ऑर्डर संभालो", "नया ऑर्डर आते ही स्टॉक अपने आप रिज़र्व हो जाता है। ऑर्डर पर कन्फर्म, पैक, भेजो, डिलीवर दबाते जाओ। चैनल पर 'ऑटो कन्फर्म' या 'ऑटो पैक' चुनो तो यह काम खुद हो जाएगा। डेमो में 'टेस्ट ऑर्डर' दबाओ।"] },
    { ic: "down",
      hinglish: ["5. Export aur data", "More mein Export orders / stock se CSV file milti hai (Sheets ya Excel ke liye). Aapka data sirf aapka hai: login yaad rehta hai aur doosre user ko aapka data nahi dikhta."],
      english: ["5. Export and your data", "In More, Export orders / stock gives a CSV file (for Sheets or Excel). Your data is only yours: the login is remembered and other users never see your data."],
      hindi: ["5. एक्सपोर्ट और आपका डेटा", "और में ऑर्डर / स्टॉक एक्सपोर्ट से CSV फ़ाइल मिलती है (Sheets या Excel के लिए)। आपका डेटा सिर्फ़ आपका है: लॉगिन याद रहता है और दूसरे यूज़र को आपका डेटा नहीं दिखता।"] },
  ];
  const UI = {
    hinglish: { skip: "Skip", next: "Aage", back: "Peeche", done: "Shuru karo", demo: "Demo try karo" },
    english: { skip: "Skip", next: "Next", back: "Back", done: "Get started", demo: "Try the demo" },
    hindi: { skip: "छोड़ो", next: "आगे", back: "पीछे", done: "शुरू करो", demo: "डेमो आज़माओ" },
  };
  let i = 0, root = null;
  const L = () => (window.I18N ? I18N.lang : "hinglish");
  const seen = () => { try { return localStorage.getItem(KEY) === "1"; } catch (_) { return false; } };
  const mark = () => { try { localStorage.setItem(KEY, "1"); } catch (_) {} };
  function close() { mark(); if (root) root.remove(); root = null; }
  function draw() {
    if (!root) return;
    const l = L(), u = UI[l], s = S[i], last = i === S.length - 1;
    root.innerHTML = `
      <div class="tour-top"><div class="tour-langs">${Object.entries(I18N.LANGS).map(([k, v]) => `<button class="chip ${k === l ? "on" : ""}" data-lang="${k}">${v}</button>`).join("")}</div>
        <button class="tour-skip" id="tour-skip">${u.skip}</button></div>
      <div class="tour-body">
        <div class="tour-ic"><svg viewBox="0 0 24 24"><path d="${IC[s.ic]}"/></svg></div>
        <h2>${s[l][0]}</h2><p>${s[l][1]}</p>
      </div>
      <div class="tour-dots">${S.map((_, k) => `<i class="${k === i ? "on" : ""}"></i>`).join("")}</div>
      <div class="tour-nav">
        ${i > 0 ? `<button class="btn quiet" id="tour-back">${u.back}</button>` : `<span></span>`}
        <button class="btn" id="tour-next">${last ? u.done : u.next}</button>
      </div>
      ${last ? `<button class="tour-demo" id="tour-demo">${u.demo}</button>` : ""}`;
    root.querySelectorAll("[data-lang]").forEach((b) => (b.onclick = () => { I18N.setLang(b.dataset.lang); }));
    root.querySelector("#tour-skip").onclick = close;
    root.querySelector("#tour-next").onclick = () => { if (last) close(); else { i++; draw(); } };
    const bk = root.querySelector("#tour-back"); if (bk) bk.onclick = () => { i--; draw(); };
    const dm = root.querySelector("#tour-demo");
    if (dm) dm.onclick = () => { close(); go("channels"); showConnect(); };
  }
  function start() {
    if (root) return;
    i = 0;
    root = document.createElement("div");
    root.className = "tour"; root.setAttribute("data-no-i18n", "");
    document.body.appendChild(root);
    draw();
  }
  window.Tour = { start, maybe() { if (!seen()) start(); }, refresh: draw };
})();
