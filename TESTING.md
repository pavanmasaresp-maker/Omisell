# Nakli marketplace order se poora flow test

1. Channels > Connect a channel > Demo (token: demo). Naam do, Connect.
2. Products mein ek product + SKU banao, Stock mein 50 add karo.
3. Sync tab: Demo channel + product chuno > Publish. Worker chalta ho to listing ACTIVE ho jayegi
   (Render par worker service ke andar chalta hai; free plan so jaye to pehli request ke baad thodi der ruko).
4. Channels > Demo card > "Test order" dabao. Nakli order marketplace se aaya.
5. Orders mein order dikhega: "via <channel naam>", stock reserved hoga.
6. Sync > Activity mein "Stock update" job dikhegi: channel ka stock apne aap kam hua.
7. Order ko Confirm > Pack > Ship karo. Stock aur reserved badalte dekho.
