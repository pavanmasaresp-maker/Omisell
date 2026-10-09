import { useEffect, useState } from "react";
import { Platform, StatusBar, Text, TouchableOpacity, View } from "react-native";
import { me } from "./src/api";
import { clearToken, getToken } from "./src/storage";
import { c, sp } from "./src/theme";
import LoginScreen from "./src/screens/LoginScreen";
import DashboardScreen from "./src/screens/DashboardScreen";
import ProductsScreen from "./src/screens/ProductsScreen";
import InventoryScreen from "./src/screens/InventoryScreen";
import OrdersScreen from "./src/screens/OrdersScreen";
import MoreScreen from "./src/screens/MoreScreen";
import ChannelsScreen from "./src/screens/ChannelsScreen";
import SyncScreen from "./src/screens/SyncScreen";

const TABS = [["home", "Home"], ["products", "Products"], ["stock", "Stock"], ["orders", "Orders"], ["more", "More"]];
const TOP = Platform.OS === "android" ? StatusBar.currentHeight || 0 : 44;

export default function App() {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [tab, setTab] = useState("home");
  const [sub, setSub] = useState(null); // More ke andar: channels | sync

  async function check() {
    try { if (await getToken()) { await me(); setAuthed(true); } } catch { await clearToken(); }
    setReady(true);
  }
  useEffect(() => { check(); }, []);

  async function logout() { await clearToken(); setSub(null); setTab("home"); setAuthed(false); }
  const go = (t) => { setSub(null); setTab(t); };

  if (!ready) return <View style={{ flex: 1, backgroundColor: c.primary }} />;

  if (!authed) {
    return (
      <View style={{ flex: 1, backgroundColor: c.primary }}>
        <StatusBar barStyle="light-content" backgroundColor={c.primary} />
        <LoginScreen onLoggedIn={() => setAuthed(true)} />
      </View>
    );
  }

  let body;
  if (tab === "home") body = <DashboardScreen go={go} />;
  else if (tab === "products") body = <ProductsScreen />;
  else if (tab === "stock") body = <InventoryScreen />;
  else if (tab === "orders") body = <OrdersScreen />;
  else if (sub === "channels") body = <ChannelsScreen onBack={() => setSub(null)} />;
  else if (sub === "sync") body = <SyncScreen onBack={() => setSub(null)} />;
  else body = <MoreScreen onOpen={setSub} onLogout={logout} />;

  return (
    <View style={{ flex: 1, backgroundColor: c.bg, paddingTop: TOP }}>
      <StatusBar barStyle="dark-content" backgroundColor={c.bg} />
      <View style={{ flex: 1 }}>{body}</View>
      <View style={{ flexDirection: "row", backgroundColor: c.surface, borderTopWidth: 1, borderTopColor: c.line, paddingBottom: sp.sm }}>
        {TABS.map(([k, label]) => {
          const on = tab === k;
          return (
            <TouchableOpacity key={k} style={{ flex: 1, alignItems: "center", paddingTop: sp.md, paddingBottom: sp.sm }} onPress={() => go(k)}>
              <View style={{ position: "absolute", top: 0, width: 28, height: 3, borderRadius: 2, backgroundColor: on ? c.accent : "transparent" }} />
              <Text style={{ color: on ? c.primary : c.inkFaint, fontWeight: on ? "800" : "600", fontSize: 13 }}>{label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}
