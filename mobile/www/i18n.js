// Bhasha: hinglish (default, app jaisi likhi hai), english, hindi.
// App ke text jaise likhe hain waise hi rehte hain; ye file DOM mein dikhne wale text ko chuni hui bhasha mein badalti hai.
// Naya text add karna ho to D (phrases) ya R (patterns) mein ek line jodo: [asli text, english, hindi]. null = badlao mat.
(function () {
  const D = [
    // ---- login ----
    ["Ek baar likho. Har jagah bechho.", "Write once. Sell everywhere.", "एक बार लिखो। हर जगह बेचो।"],
    ["Welcome", null, "स्वागत है"],
    ["Google se ya email se sign in karo. Naya account apne aap ban jata hai.", "Sign in with Google or email. A new account is created automatically.", "Google या ईमेल से साइन इन करो। नया अकाउंट अपने आप बन जाता है।"],
    ["Continue with Google", null, "Google से जारी रखो"],
    ["ya email se", "or with email", "या ईमेल से"],
    ["Email", null, "ईमेल"],
    ["Password (kam se kam 6 akshar)", "Password (at least 6 characters)", "पासवर्ड (कम से कम 6 अक्षर)"],
    ["Password", null, "पासवर्ड"],
    ["Username", null, "यूज़रनेम"],
    ["Sign in", null, "साइन इन"],
    ["Create account", null, "अकाउंट बनाओ"],
    ["Password bhool gaye?", "Forgot password?", "पासवर्ड भूल गए?"],
    ["Admin login (username aur password)", "Admin login (username and password)", "एडमिन लॉगिन (यूज़रनेम और पासवर्ड)"],
    ["Ye option sirf phone ki app mein chalta hai.", "This option works only in the phone app.", "यह विकल्प सिर्फ़ फ़ोन के ऐप में चलता है।"],
    ["Email daalo.", "Enter your email.", "ईमेल डालो।"],
    ["Password kam se kam 6 akshar ka hona chahiye.", "Password must be at least 6 characters.", "पासवर्ड कम से कम 6 अक्षर का होना चाहिए।"],
    ["Password reset ka link email par bhej diya. Inbox / spam dekho.", "Password reset link sent to your email. Check inbox / spam.", "पासवर्ड रीसेट का लिंक ईमेल पर भेज दिया। इनबॉक्स / स्पैम देखो।"],
    ["Account ban gaya. Email par verify link bheja hai: use khol kar verify karo, phir Sign in dabao.", "Account created. A verify link was emailed: open it to verify, then tap Sign in.", "अकाउंट बन गया। ईमेल पर वेरिफ़ाई लिंक भेजा है: उसे खोलकर वेरिफ़ाई करो, फिर साइन इन दबाओ।"],
    ["Email abhi verify nahi hui. Naya verify link bheja hai: inbox / spam dekho, verify karke dobara Sign in karo.", "Email not verified yet. A new verify link was sent: check inbox / spam, verify, then sign in again.", "ईमेल अभी वेरिफ़ाई नहीं हुई। नया लिंक भेजा है: इनबॉक्स / स्पैम देखो, वेरिफ़ाई करके दोबारा साइन इन करो।"],
    ["Is email se account pehle se hai. Sign in karo.", "An account with this email already exists. Please sign in.", "इस ईमेल से अकाउंट पहले से है। साइन इन करो।"],
    ["Email ya password galat hai. Email ki spelling check karo (jaise gmail.com). Naya ho to pehle Create account dabao.", "Wrong email or password. Check the email spelling (like gmail.com). If you are new, tap Create account first.", "ईमेल या पासवर्ड गलत है। ईमेल की स्पेलिंग जाँचो (जैसे gmail.com)। नए हो तो पहले अकाउंट बनाओ दबाओ।"],
    ["Email sahi format mein nahi hai.", "Email is not in a valid format.", "ईमेल सही फ़ॉर्मैट में नहीं है।"],
    ["Internet nahi chal raha. Check karke dobara try karo.", "No internet. Check and try again.", "इंटरनेट नहीं चल रहा। जाँचकर दोबारा कोशिश करो।"],
    ["Ye account band kar diya gaya hai.", "This account has been disabled.", "यह अकाउंट बंद कर दिया गया है।"],
    ["Password kamzor hai, kam se kam 6 akshar rakho.", "Password is weak. Use at least 6 characters.", "पासवर्ड कमज़ोर है, कम से कम 6 अक्षर रखो।"],
    ["Bahut koshish ho gayi. Thodi der baad try karo.", "Too many attempts. Try again after a while.", "बहुत कोशिशें हो गईं। थोड़ी देर बाद कोशिश करो।"],
    ["Nahi ho paya:", "Could not do it:", "नहीं हो पाया:"],
    ["Google login nahi ho paya:", "Google login failed:", "Google लॉगिन नहीं हो पाया:"],
    ["Username aur password dono daalo.", "Enter both username and password.", "यूज़रनेम और पासवर्ड दोनों डालो।"],
    ["Session khatam. Dobara sign in karo.", "Session ended. Please sign in again.", "सेशन खत्म हो गया। दोबारा साइन इन करो।"],
    ["Server tak nahi pahunch paye. Internet check karo, aur backend chal raha hai ya nahi dekho.", "Could not reach the server. Check your internet and whether the backend is running.", "सर्वर तक नहीं पहुँच पाए। इंटरनेट जाँचो और देखो कि बैकएंड चल रहा है या नहीं।"],
    // ---- tabs / titles ----
    ["Home", null, "होम"],
    ["Products", null, "प्रोडक्ट्स"],
    ["Stock", null, "स्टॉक"],
    ["Orders", null, "ऑर्डर्स"],
    ["More", null, "और"],
    ["Back", null, "वापस"],
    ["Aapki dukaan ka aaj ka haal", "Your shop today", "आपकी दुकान का आज का हाल"],
    ["Kitna maal hai", "How much stock you have", "कितना माल है"],
    ["Jahan aap bechte ho", "Where you sell", "जहाँ आप बेचते हो"],
    ["Product channel par bhejo", "Send products to a channel", "प्रोडक्ट चैनल पर भेजो"],
    ["Loading…", null, "लोड हो रहा है…"],
    ["Please wait…", null, "रुको…"],
    ["Try again", null, "फिर कोशिश करो"],
    // ---- dashboard ----
    ["7 din", "7 days", "7 दिन"], ["30 din", "30 days", "30 दिन"], ["Sab", "All", "सब"],
    ["Total sale", null, "कुल बिक्री"],
    ["Pieces", null, "पीस"], ["live", null, "लाइव"],
    ["Delivery ka haal", "Delivery status", "डिलीवरी का हाल"],
    ["Naya", "New", "नया"], ["Raste mein", "In transit", "रास्ते में"], ["Cancel", null, "कैंसिल"], ["Return", null, "रिटर्न"],
    ["Channels", null, "चैनल"], ["Stock", null, "स्टॉक"],
    ["Sale", null, "बिक्री"],
    ["Charges", null, "चार्जेस"],
    ["Aapko bacha", "You keep", "आपको बचा"],
    ["Bhejna baaki", "To ship", "भेजना बाकी"],
    ["Kisi channel par nahi", "Not on any channel", "किसी चैनल पर नहीं"],
    ["Sabse zyada bika", "Best sellers", "सबसे ज़्यादा बिका"],
    ["Kaunsa product kahan hai", "Which product is where", "कौन सा प्रोडक्ट कहाँ है"],
    ["Bechne layak stock", "Sellable stock", "बिकने लायक स्टॉक"],
    ["Kam bacha", "Running low", "कम बचा"],
    ["Koi channel nahi", "No channels yet", "कोई चैनल नहीं"],
    ["Channels mein jaake apna store ya CSV channel connect karo.", "Go to Channels and connect your store or a CSV channel.", "चैनल में जाकर अपना स्टोर या CSV चैनल जोड़ो।"],
    ["Commission (% of sale)", null, "कमीशन (बिक्री का %)"],
    ["Har order par fixed charge (₹)", "Fixed charge per order (₹)", "हर ऑर्डर पर तय चार्ज (₹)"],
    ["Charges save ho gaye", "Charges saved", "चार्जेस सेव हो गए"],
    ["badlo", "change", "बदलो"],
    ["Marketplace jo commission/charge leta hai wo yahan daalo (seller panel ya invoice se dekh lo). Dashboard isi se \"aapko bacha\" nikalta hai. Ye sirf hisaab ke liye hai, marketplace par kuch nahi badalta.",
     "Enter the commission/charges the marketplace takes (see your seller panel or invoice). The dashboard uses this to work out what you keep. Only for your records; nothing changes on the marketplace.",
     "मार्केटप्लेस जो कमीशन/चार्ज लेता है वो यहाँ डालो (सेलर पैनल या इनवॉइस से देखो)। डैशबोर्ड इसी से \"आपको बचा\" निकालता है। यह सिर्फ़ हिसाब के लिए है, मार्केटप्लेस पर कुछ नहीं बदलता।"],
    // ---- home ----
    ["Sellable stock", null, "बिकने लायक स्टॉक"],
    ["On hand", null, "हाथ में"],
    ["Reserved for orders", null, "ऑर्डर के लिए रिज़र्व"],
    ["Reserved", null, "रिज़र्व"],
    ["SKUs", null, "SKU"],
    ["Stock theek hai", "Stock is fine", "स्टॉक ठीक है"],
    ["Koi SKU kam nahi pada.", "No SKU is running low.", "कोई SKU कम नहीं पड़ा।"],
    ["Recent stock changes", null, "हाल के स्टॉक बदलाव"],
    ["Abhi koi hisaab nahi", "No records yet", "अभी कोई हिसाब नहीं"],
    ["Stock add karoge to yahan dikhega.", "It will show here once you add stock.", "स्टॉक जोड़ोगे तो यहाँ दिखेगा।"],
    // ---- products ----
    ["Naam ya SKU se dhundo", "Search by name or SKU", "नाम या SKU से खोजो"],
    ["Add product", null, "प्रोडक्ट जोड़ो"],
    ["Kuch nahi mila", "Nothing found", "कुछ नहीं मिला"],
    ["Abhi koi product nahi", "No products yet", "अभी कोई प्रोडक्ट नहीं"],
    ["Abhi koi product nahi.", "No products yet.", "अभी कोई प्रोडक्ट नहीं।"],
    ["Dusra naam ya SKU try karo.", "Try another name or SKU.", "दूसरा नाम या SKU आज़माओ।"],
    ["Pehla product add karke shuru karo.", "Start by adding your first product.", "पहला प्रोडक्ट जोड़कर शुरू करो।"],
    ["No SKU", null, "कोई SKU नहीं"],
    ["Product name", null, "प्रोडक्ट का नाम"],
    ["Status", null, "स्टेटस"],
    ["price (₹)", null, "कीमत (₹)"],
    ["Price (₹)", null, "कीमत (₹)"],
    ["Save changes", null, "बदलाव सेव करो"],
    ["Delete", null, "डिलीट करो"],
    ["Saved", null, "सेव हो गया"],
    ["Deleted", null, "डिलीट हो गया"],
    ["Iski stock history bhi hat jayegi. Jis marketplace par ye laga hai wahan se use khud hatana hoga.", "Its stock history will be removed too. You must remove it yourself from any marketplace where it is listed.", "इसकी स्टॉक हिस्ट्री भी हट जाएगी। जिस मार्केटप्लेस पर यह लगा है वहाँ से इसे खुद हटाना होगा।"],
    ["Is product ke orders hain, isliye delete nahi ho sakta. Product ko ARCHIVED kar do.", "This product has orders, so it cannot be deleted. Set it to ARCHIVED instead.", "इस प्रोडक्ट के ऑर्डर हैं, इसलिए डिलीट नहीं हो सकता। प्रोडक्ट को ARCHIVED कर दो।"],
    ["Archive karo", "Archive it", "आर्काइव करो"],
    ["Archive ho gaya", "Archived", "आर्काइव हो गया"],
    ["Product ka naam khaali nahi ho sakta.", "Product name cannot be empty.", "प्रोडक्ट का नाम खाली नहीं हो सकता।"],
    ["Product delete karna hai?", "Delete this product?", "प्रोडक्ट डिलीट करना है?"],
    ["Rehne do", "Keep it", "रहने दो"],
    ["New product", null, "नया प्रोडक्ट"],
    ["SKU code", null, "SKU कोड"],
    ["Har SKU ka code alag hona chahiye.", "Every SKU needs a different code.", "हर SKU का कोड अलग होना चाहिए।"],
    ["Cancel", null, "रद्द करो"],
    ["Save product", null, "प्रोडक्ट सेव करो"],
    ["Title, SKU code aur price teeno chahiye.", "Title, SKU code and price are all required.", "नाम, SKU कोड और कीमत तीनों चाहिए।"],
    ["Product add ho gaya", "Product added", "प्रोडक्ट जुड़ गया"],
    // ---- stock ----
    ["Available", null, "उपलब्ध"],
    ["Quantity", null, "मात्रा"],
    ["Add", null, "जोड़ो"],
    ["Remove", null, "हटाओ"],
    ["History", null, "हिस्ट्री"],
    ["adjustment", null, "सुधार"], ["sale", null, "बिक्री"], ["reservation", null, "रिज़र्वेशन"], ["release", null, "रिलीज़"], ["return", null, "वापसी"],
    ["Abhi koi history nahi.", "No history yet.", "अभी कोई हिस्ट्री नहीं।"],
    ["Abhi koi stock record nahi", "No stock records yet", "अभी कोई स्टॉक रिकॉर्ड नहीं"],
    ["Product add karo, phir yahan stock daal sakte ho.", "Add a product first, then you can add stock here.", "पहले प्रोडक्ट जोड़ो, फिर यहाँ स्टॉक डाल सकते हो।"],
    ["Quantity 1 ya usse zyada daalo.", "Enter a quantity of 1 or more.", "मात्रा 1 या उससे ज़्यादा डालो।"],
    ["add kiye", "added", "जोड़े गए"],
    ["hata diye", "removed", "हटाए गए"],
    ["OUT OF STOCK", null, "स्टॉक खत्म"],
    // ---- orders ----
    ["All", null, "सभी"],
    ["New order", null, "नया ऑर्डर"],
    ["Walk-in", null, "वॉक-इन"],
    ["Koi order nahi", "No orders", "कोई ऑर्डर नहीं"],
    ["Is status mein abhi koi order nahi.", "No orders in this status yet.", "इस स्टेटस में अभी कोई ऑर्डर नहीं।"],
    ["Pehla order banake dekho.", "Try creating your first order.", "पहला ऑर्डर बनाकर देखो।"],
    ["Confirm", null, "कन्फर्म करो"],
    ["Pack", null, "पैक करो"],
    ["Ship", null, "भेजो"],
    ["Mark delivered", null, "डिलीवर हुआ"],
    ["Order update ho gaya", "Order updated", "ऑर्डर अपडेट हो गया"],
    ["Order cancel karni hai?", "Cancel this order?", "ऑर्डर रद्द करना है?"],
    ["Reserved stock wapas available ho jayega.", "Reserved stock will become available again.", "रिज़र्व स्टॉक वापस उपलब्ध हो जाएगा।"],
    ["Cancel order", null, "ऑर्डर रद्द करो"],
    ["Order cancel ho gaya", "Order cancelled", "ऑर्डर रद्द हो गया"],
    ["Customer name", null, "ग्राहक का नाम"],
    ["Create order", null, "ऑर्डर बनाओ"],
    ["Order ban gaya", "Order created", "ऑर्डर बन गया"],
    // ---- status words ----
    ["DRAFT", null, "ड्राफ्ट"], ["ACTIVE", null, "चालू"], ["ARCHIVED", null, "आर्काइव"],
    ["IMPORTED", null, "नया"], ["CONFIRMED", null, "कन्फर्म"], ["PACKED", null, "पैक"], ["SHIPPED", null, "भेजा गया"],
    ["DELIVERED", null, "डिलीवर"], ["CANCELLED", null, "रद्द"], ["RETURNED", null, "वापस"],
    ["PENDING", null, "बाकी"], ["RUNNING", null, "चल रहा"], ["SUCCEEDED", null, "पूरा"], ["FAILED", null, "फेल"],
    ["NEEDS ACTION", null, "ध्यान दें"], ["CONNECTED", null, "जुड़ा"], ["ERROR", null, "एरर"],
    // ---- more ----
    ["Shopify, WooCommerce ya Demo store connect karo", "Connect Shopify, WooCommerce or a Demo store", "Shopify, WooCommerce या डेमो स्टोर जोड़ो"],
    ["Channels", null, "चैनल"],
    ["Sync", null, "सिंक"],
    ["Product publish karo, jobs dekho", "Publish products, see jobs", "प्रोडक्ट पब्लिश करो, जॉब देखो"],
    ["Export orders (CSV)", null, "ऑर्डर एक्सपोर्ट (CSV)"],
    ["Saare channels ke orders ek file mein", "Orders from all channels in one file", "सारे चैनल के ऑर्डर एक फ़ाइल में"],
    ["Export stock (CSV)", null, "स्टॉक एक्सपोर्ट (CSV)"],
    ["SKU wise stock", "Stock by SKU", "SKU के हिसाब से स्टॉक"],
    ["Settings", null, "सेटिंग्स"],
    ["Language, App guide, Delete account", "Language, App guide, Delete account", "भाषा, ऐप गाइड, अकाउंट डिलीट"],
    ["Bhasha, guide, account", "Language, guide, account", "भाषा, गाइड, अकाउंट"],
    ["Language", null, "भाषा"],
    ["Hindi, English ya Hinglish chuno", "Choose Hindi, English or Hinglish", "हिन्दी, English या Hinglish चुनो"],
    ["App guide", null, "ऐप गाइड"],
    ["App kaise use karni hai, dobara dekho", "See again how to use the app", "ऐप कैसे चलानी है, फिर से देखो"],
    ["Log out", null, "लॉग आउट"],
    ["Delete account", null, "अकाउंट डिलीट करो"],
    ["Account delete karna hai?", "Delete your account?", "अकाउंट डिलीट करना है?"],
    ["Aapka poora store hat jayega: products, stock, orders, channels aur saare users. Ye wapas nahi aayega.", "Your whole store will be removed: products, stock, orders, channels and all users. This cannot be undone.", "आपका पूरा स्टोर हट जाएगा: प्रोडक्ट, स्टॉक, ऑर्डर, चैनल और सारे यूज़र। यह वापस नहीं आएगा।"],
    ["Aapka login hat jayega. Store ka data rahega.", "Your login will be removed. The store data will stay.", "आपका लॉगिन हट जाएगा। स्टोर का डेटा रहेगा।"],
    ["Confirm ke liye DELETE likho", "Type DELETE to confirm", "पक्का करने के लिए DELETE लिखो"],
    ["DELETE likhna zaroori hai.", "You must type DELETE.", "DELETE लिखना ज़रूरी है।"],
    ["Account delete ho gaya", "Account deleted", "अकाउंट डिलीट हो गया"],
    // ---- channels ----
    ["Connect a channel", null, "चैनल जोड़ो"],
    ["Koi channel connected nahi", "No channel connected", "कोई चैनल जुड़ा नहीं"],
    ["Pehle Demo channel connect karke poora flow try kar sakte ho.", "You can first connect a Demo channel and try the whole flow.", "पहले डेमो चैनल जोड़कर पूरा फ़्लो आज़मा सकते हो।"],
    ["Manual", null, "मैन्युअल"],
    ["Auto confirm", null, "ऑटो कन्फर्म"],
    ["Auto pack", null, "ऑटो पैक"],
    ["Naya order aate hi:", "When a new order arrives:", "नया ऑर्डर आते ही:"],
    ["aap khud confirm/pack karoge", "you confirm/pack it yourself", "आप खुद कन्फर्म/पैक करोगे"],
    ["apne aap confirm hoga", "it is confirmed automatically", "अपने आप कन्फर्म होगा"],
    ["apne aap confirm + pack hoga (ship aap karoge)", "it is confirmed + packed automatically (you ship it)", "अपने आप कन्फर्म + पैक होगा (भेजोगे आप)"],
    ["CSV file", null, "CSV फ़ाइल"],
    ["Import CSV", null, "CSV इम्पोर्ट"],
    ["Meesho, Nykaa, Flipkart, Amazon: seller panel se order file (CSV) download karo aur yahan import karo. Channel ka naam wahi rakho (jaise Meesho).", "Meesho, Nykaa, Flipkart, Amazon: download the order file (CSV) from the seller panel and import it here. Use the marketplace name as the channel name (like Meesho).", "Meesho, Nykaa, Flipkart, Amazon: सेलर पैनल से ऑर्डर फ़ाइल (CSV) डाउनलोड करो और यहाँ इम्पोर्ट करो। चैनल का नाम वही रखो (जैसे Meesho)।"],
    ["Channel ka naam daalo.", "Enter a channel name.", "चैनल का नाम डालो।"],
    ["Excel file nahi chalti. Excel mein Save as > CSV karke daalo.", "Excel files do not work. In Excel use Save as > CSV and upload that.", "Excel फ़ाइल नहीं चलती। Excel में Save as > CSV करके डालो।"],
    ["File padh nahi paye.", "Could not read the file.", "फ़ाइल पढ़ नहीं पाए।"],
    ["File mein koi order row nahi mili.", "No order rows found in the file.", "फ़ाइल में कोई ऑर्डर पंक्ति नहीं मिली।"],
    ["Columns match karo", "Match the columns", "कॉलम मिलाओ"],
    ["Har cheez file ke kaunse column mein hai, ye chuno. * zaroori hai.", "Choose which column of the file holds each item. * is required.", "हर चीज़ फ़ाइल के किस कॉलम में है, यह चुनो। * ज़रूरी है।"],
    ["— skip —", "— skip —", "— छोड़ो —"],
    ["Order ID", null, "ऑर्डर ID"], ["SKU code", null, "SKU कोड"], ["Price (per piece)", null, "कीमत (प्रति पीस)"],
    ["Customer name", null, "ग्राहक का नाम"], ["Phone", null, "फ़ोन"], ["City", null, "शहर"],
    ["Import", null, "इम्पोर्ट"],
    ["Zaroori column chuno:", "Pick the required columns:", "ज़रूरी कॉलम चुनो:"],
    ["lines import honge", "lines will be imported", "लाइनें इम्पोर्ट होंगी"],
    ["rows chhoot gayi (khaali ya galat)", "rows skipped (empty or invalid)", "पंक्तियाँ छूट गईं (खाली या गलत)"],
    ["orders aa chuke the", "orders had already arrived", "ऑर्डर आ चुके थे"],
    ["Aksar wajah: SKU catalog mein nahi hai. Wahi SKU code se product banao, phir dobara Import / Fetch karo.", "Usual reason: the SKU is not in your catalog. Create a product with that same SKU code, then Import / Fetch again.", "अक्सर वजह: SKU कैटलॉग में नहीं है। वही SKU कोड से प्रोडक्ट बनाओ, फिर दोबारा इम्पोर्ट / मँगाओ।"],
    ["CSV channel par 'Import CSV' use karo.", "On a CSV channel use 'Import CSV'.", "CSV चैनल पर 'CSV इम्पोर्ट' इस्तेमाल करो।"],
    ["Auto publish ON", null, "ऑटो पब्लिश चालू"],
    ["Auto publish OFF", null, "ऑटो पब्लिश बंद"],
    ["Publish all products", null, "सारे प्रोडक्ट पब्लिश करो"],
    ["Naya product ya badlav apne aap is channel par jayega.", "A new product or change will go to this channel automatically.", "नया प्रोडक्ट या बदलाव अपने आप इस चैनल पर जाएगा।"],
    ["Product aap Sync se khud bhejoge.", "You send products yourself from Sync.", "प्रोडक्ट आप सिंक से खुद भेजोगे।"],
    ["products bhejne ke liye lage", "products queued to send", "प्रोडक्ट भेजने के लिए कतार में लगे"],
    ["bina SKU ke chhoote", "skipped (no SKU)", "बिना SKU के छूटे"],
    ["Test order", null, "टेस्ट ऑर्डर"],
    ["Fetch orders", null, "ऑर्डर मँगाओ"],
    ["Check again", null, "फिर जाँचो"],
    ["Demo (test)", null, "डेमो (टेस्ट)"],
    ["Name", null, "नाम"],
    ["Store address", null, "स्टोर का पता"],
    ["Access token", null, "एक्सेस टोकन"],
    ['Test ke liye "demo" likho.', 'Type "demo" for testing.', 'टेस्ट के लिए "demo" लिखो।'],
    ["Token encrypted save hota hai, wapas nahi dikhta.", "The token is saved encrypted and is not shown again.", "टोकन एन्क्रिप्टेड सेव होता है, दोबारा नहीं दिखता।"],
    ["API keys (key:secret)", null, "API कीज़ (key:secret)"],
    ["Format: consumer_key:consumer_secret. WooCommerce > Settings > Advanced > REST API se Read/Write key banao.", "Format: consumer_key:consumer_secret. Create a Read/Write key in WooCommerce > Settings > Advanced > REST API.", "फ़ॉर्मैट: consumer_key:consumer_secret। WooCommerce > Settings > Advanced > REST API से Read/Write की बनाओ।"],
    ["Sirf https wali site, bina https:// ke.", "Only https sites, without https://.", "सिर्फ़ https वाली साइट, https:// के बिना।"],
    ["Connect", null, "जोड़ो"],
    ["Naam aur token dono daalo.", "Enter both name and token.", "नाम और टोकन दोनों डालो।"],
    ["Channel connect ho gaya", "Channel connected", "चैनल जुड़ गया"],
    ["Setting save ho gayi", "Setting saved", "सेटिंग सेव हो गई"],
    ["Channel hataana hai?", "Remove this channel?", "चैनल हटाना है?"],
    ["Iske listings aur jobs bhi hat sakte hain.", "Its listings and jobs may be removed too.", "इसकी लिस्टिंग और जॉब भी हट सकती हैं।"],
    ["Hatao", "Remove", "हटाओ"],
    ["Nakli order aaya:", "Test order arrived:", "नकली ऑर्डर आया:"],
    ["Orders tab mein dekho.", "See it in the Orders tab.", "ऑर्डर्स टैब में देखो।"],
    ["Ye orders nahi aa paye", "These orders could not be imported", "ये ऑर्डर नहीं आ पाए"],
    ["Aksar wajah: SKU catalog mein nahi hai. Wahi SKU code se product banao, phir dobara Fetch karo.", "Usual reason: the SKU is not in your catalog. Create a product with that same SKU code, then Fetch again.", "अक्सर वजह: SKU कैटलॉग में नहीं है। वही SKU कोड से प्रोडक्ट बनाओ, फिर दोबारा मँगाओ।"],
    ["naye order aaye", "new orders arrived", "नए ऑर्डर आए"],
    ["pehle se the", "already existed", "पहले से थे"],
    ["nahi aa paye", "could not be imported", "नहीं आ पाए"],
    // ---- sync ----
    ["Channel", null, "चैनल"],
    ["Product", null, "प्रोडक्ट"],
    ["Pehle More › Channels mein koi channel connect karo.", "First connect a channel in More › Channels.", "पहले और › चैनल में कोई चैनल जोड़ो।"],
    ["Publish", null, "पब्लिश करो"],
    ["Listings", null, "लिस्टिंग"],
    ["Activity", null, "गतिविधि"],
    ["Stock update", null, "स्टॉक अपडेट"],
    ["Abhi kuch publish nahi hua", "Nothing published yet", "अभी कुछ पब्लिश नहीं हुआ"],
    ["Upar se channel aur product chuno.", "Pick a channel and a product above.", "ऊपर से चैनल और प्रोडक्ट चुनो।"],
    ["Abhi koi activity nahi", "No activity yet", "अभी कोई गतिविधि नहीं"],
    ["Publish queue mein gaya. Worker chalte hi ho jayega.", "Publish queued. It will happen as soon as the worker runs.", "पब्लिश कतार में गया। वर्कर चलते ही हो जाएगा।"],
    ["job wait kar rahe hain.", "job(s) waiting.", "जॉब इंतज़ार कर रहे हैं।"],
    ["Worker chal raha hai?", "Is the worker running?", "वर्कर चल रहा है?"],
    // ---- export ----
    ["Copy CSV", null, "CSV कॉपी करो"],
    ["Share file", null, "फ़ाइल शेयर करो"],
    ["Abhi kuch nahi hai", "Nothing here yet", "अभी कुछ नहीं है"],
    ["Order aane par yahan dikhega.", "Orders will show here once they arrive.", "ऑर्डर आने पर यहाँ दिखेगा।"],
    ["Stock add karne par yahan dikhega.", "Stock will show here once you add it.", "स्टॉक जोड़ने पर यहाँ दिखेगा।"],
    ["Copy ho gaya. Sheets / Excel mein paste karo.", "Copied. Paste it into Sheets / Excel.", "कॉपी हो गया। Sheets / Excel में पेस्ट करो।"],
    ["Copy nahi hua. Share file use karo.", "Copy failed. Use Share file.", "कॉपी नहीं हुआ। फ़ाइल शेयर करो।"],
    ["Share nahi hua. Copy use karo.", "Share failed. Use Copy.", "शेयर नहीं हुआ। कॉपी करो।"],
    ["Export nahi ho paya (HTTP", "Export failed (HTTP", "एक्सपोर्ट नहीं हो पाया (HTTP"],
    // ---- server messages (common) ----
    ["Channel connected nahi hai. Channels mein Re-check karo.", "Channel is not connected. Re-check it in Channels.", "चैनल जुड़ा नहीं है। चैनल में फिर जाँचो।"],
    ["Channel connected nahi hai. Pehle Check again karo.", "Channel is not connected. Tap Check again first.", "चैनल जुड़ा नहीं है। पहले फिर जाँचो दबाओ।"],
    ["Demo channel par 'Test order' use karo.", "On the Demo channel use 'Test order'.", "डेमो चैनल पर 'टेस्ट ऑर्डर' इस्तेमाल करो।"],
    ["Pehle koi product add karo, tabhi nakli order ban sakta hai.", "Add a product first, then a test order can be made.", "पहले कोई प्रोडक्ट जोड़ो, तभी टेस्ट ऑर्डर बन सकता है।"],
  ];
  const R = [
    [/^Charges: (.+)$/, null, "चार्जेस: $1"],
    [/^(\d+) order · (\d+) piece bika$/, "$1 orders · $2 pieces sold", "$1 ऑर्डर · $2 पीस बिके"],
    [/^(\d+) bika$/, "$1 sold", "$1 बिके"],
    [/^Delivered (\d+)$/, null, "डिलीवर $1"],
    [/^Raste mein (\d+)$/, "In transit $1", "रास्ते में $1"],
    [/^Bhejna baaki (\d+)$/, "To ship $1", "भेजना बाकी $1"],
    [/^Return (\d+)$/, null, "रिटर्न $1"],
    [/^Cancel (\d+)$/, null, "कैंसिल $1"],
    [/^Pending (\d+)$/, null, "पेंडिंग $1"],
    [/^Fail (\d+)$/, null, "फेल $1"],
    [/^Listed:$/, null, "लिस्टेड:"],
    [/^(.+) · Live$/, "$1 · Live", "$1 · लाइव"],
    [/^(.+) · Pending$/, "$1 · Pending", "$1 · पेंडिंग"],
    [/^(.+) · Fail$/, "$1 · Failed", "$1 · फेल"],
    [/^Kam bacha \(≤ ?(.*)\)$/, "Running low (≤ $1)", "कम बचा (≤ $1)"],
    [/^Charges −(.+)$/, "Charges −$1", "चार्जेस −$1"],
    [/^Aapko bacha (.+)$/, "You keep $1", "आपको बचा $1"],
    [/^(\d+) live$/, null, "$1 लाइव"],
    [/^(\d+) products?$/, null, "$1 प्रोडक्ट"],
    [/^(\d+) SKUs?$/, null, "$1 SKU"],
    [/^(\d+) orders?$/, null, "$1 ऑर्डर"],
    [/^(\d+) orders · (\d+) lines import honge(.*)$/, "$1 orders · $2 lines will be imported$3", "$1 ऑर्डर · $2 लाइनें इम्पोर्ट होंगी$3"],
    [/^(\d+) orders · kul (.+)$/, "$1 orders · total $2", "$1 ऑर्डर · कुल $2"],
    [/^(\d+) SKU · kul available (\d+)$/, "$1 SKU · $2 available in total", "$1 SKU · कुल उपलब्ध $2"],
    [/^(.+) haath mein · (.+) reserved$/, "$1 in hand · $2 reserved", "$1 हाथ में · $2 रिज़र्व"],
    [/^Running low \(≤ ?(.*)\)$/, null, "कम स्टॉक (≤ $1)"],
    [/^SKU "(.*)" nahi mila\. Upar se ek chuno\.$/, 'SKU "$1" not found. Pick one from above.', 'SKU "$1" नहीं मिला। ऊपर से एक चुनो।'],
    [/^(.*) · via (.+)$/, "$1 · via $2", "$1 · $2 के ज़रिए"],
    [/^(\d+) job wait kar rahe hain\.(.*)$/, "$1 job(s) waiting.$2", "$1 जॉब इंतज़ार कर रहे हैं।$2"],
  ];

  const KEY = "omnisell_lang";
  const LANGS = { hinglish: "Hinglish", english: "English", hindi: "हिन्दी" };
  let lang = "hinglish";
  try { const s = localStorage.getItem(KEY); if (LANGS[s]) lang = s; } catch (_) {}

  const idx = { english: 1, hindi: 2 };
  let maps = {}, regs = {};
  function build(l) {
    const i = idx[l], m = new Map();
    D.forEach((d) => { if (d[i] != null) m.set(d[0], d[i]); });
    const keys = [...m.keys()].sort((a, b) => b.length - a.length).map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    maps[l] = m;
    regs[l] = keys.length ? new RegExp("(?<![A-Za-z0-9\\u0900-\\u097F])(?:" + keys.join("|") + ")(?![A-Za-z0-9\\u0900-\\u097F])", "g") : null;
  }
  const phrase = (s, l) => (regs[l] ? s.replace(regs[l], (k) => maps[l].get(k)) : s);
  function xlate(s) {
    if (lang === "hinglish" || !s) return s;
    if (!maps[lang]) build(lang);
    const t = s.trim();
    if (!t) return s;
    const i = idx[lang];
    for (const r of R) {
      const m = r[0].exec(t);
      if (m && r[i] != null) {
        const out = phrase(t.replace(r[0], r[i]), lang);
        return s.replace(t, out);
      }
    }
    return phrase(s, lang);
  }

  const orig = new WeakMap();
  const skip = (n) => { const p = n.parentElement; return !p || /^(SCRIPT|STYLE|TEXTAREA|NOSCRIPT)$/.test(p.tagName) || !!p.closest("[data-no-i18n]"); };
  function doText(n) {
    if (skip(n)) return;
    const rec = orig.get(n);
    if (rec && n.data === rec.t) return;
    const base = n.data, t = xlate(base);
    if (t !== base) { orig.set(n, { o: base, t }); n.data = t; } else if (rec) orig.delete(n);
  }
  function doAttrs(el) {
    if (!el.getAttribute || el.closest("[data-no-i18n]")) return;
    ["placeholder", "aria-label"].forEach((a) => {
      if (!el.hasAttribute(a)) return;
      const k = "data-i18n-" + a;
      const base = el.hasAttribute(k) && el.getAttribute(a) === (el.__i18nT || null) ? el.getAttribute(k) : el.getAttribute(a);
      const t = xlate(base);
      if (t !== base) { el.setAttribute(k, base); el.__i18nT = t; el.setAttribute(a, t); }
      else if (el.hasAttribute(k)) { el.removeAttribute(k); }
    });
  }
  function walk(root) {
    if (root.nodeType === 3) return doText(root);
    if (root.nodeType !== 1) return;
    doAttrs(root);
    const w = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) (n.nodeType === 3 ? doText(n) : doAttrs(n));
  }
  function restoreAll() {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) { const rec = orig.get(n); if (rec && n.data === rec.t) { n.data = rec.o; orig.delete(n); } }
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.setAttribute("placeholder", el.getAttribute("data-i18n-placeholder")); el.removeAttribute("data-i18n-placeholder"); });
  }

  let busy = false;
  const mo = new MutationObserver((muts) => {
    if (busy || lang === "hinglish") return;
    busy = true;
    try {
      for (const m of muts) {
        if (m.type === "characterData") doText(m.target);
        else m.addedNodes.forEach((x) => walk(x));
      }
    } finally { busy = false; }
    mo.takeRecords();
  });

  function markLangChips() {
    document.querySelectorAll("[data-lang]").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
  }
  function setLang(l) {
    if (!LANGS[l]) return;
    lang = l;
    try { localStorage.setItem(KEY, l); } catch (_) {}
    document.documentElement.lang = l === "hindi" ? "hi" : "en";
    busy = true;
    try { restoreAll(); if (l !== "hinglish") walk(document.body); } finally { busy = false; }
    mo.takeRecords();
    markLangChips();
    // jo screen khuli hai use dobara banao taaki dynamic text bhi naye sire se aaye
    try { if (typeof go === "function" && typeof view !== "undefined" && !$("app-screen").classList.contains("hidden")) go(view); } catch (_) {}
    if (window.Tour && Tour.refresh) Tour.refresh();
  }
  function langSheet() {
    const o = sheet(`<h3 data-no-i18n>Language / भाषा</h3>
      <div class="langlist">${Object.entries(LANGS).map(([k, v]) => `<button class="lang-row ${k === lang ? "on" : ""}" data-lang="${k}" data-no-i18n><span>${v}</span><i>${k === lang ? "✓" : ""}</i></button>`).join("")}</div>`);
    o.querySelectorAll("[data-lang]").forEach((b) => (b.onclick = () => { setLang(b.dataset.lang); o.remove(); }));
  }
  window.I18N = { setLang, langSheet, get lang() { return lang; }, LANGS, tr: (s) => xlate(s) };
  window.t = (s) => xlate(s);

  function start() {
    mo.observe(document.body, { childList: true, subtree: true, characterData: true });
    document.documentElement.lang = lang === "hindi" ? "hi" : "en";
    if (lang !== "hinglish") walk(document.body);
    markLangChips();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
