import { useEffect, useState } from "react";
import { SafeAreaView, StatusBar, Text, TouchableOpacity, View } from "react-native";
import { me } from "./src/api";
import { clearToken, getToken } from "./src/storage";
import LoginScreen from "./src/screens/LoginScreen";
import ProductsScreen from "./src/screens/ProductsScreen";
import InventoryScreen from "./src/screens/InventoryScreen";

export default function App() {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [tab, setTab] = useState("products");

  async function check() {
    try { if (await getToken()) { await me(); setAuthed(true); } } catch { await clearToken(); }
    setReady(true);
  }
  useEffect(() => { check(); }, []);

  async function logout() { await clearToken(); setAuthed(false); }

  if (!ready) return <View style={{ flex: 1, backgroundColor: "#0f1115" }} />;
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: "#0f1115" }}>
      <StatusBar barStyle="light-content" />
      {!authed ? <LoginScreen onLoggedIn={() => setAuthed(true)} /> : (
        <>
          <View style={{ flex: 1 }}>
            {tab === "products" ? <ProductsScreen /> : <InventoryScreen />}
          </View>
          <View style={{ flexDirection: "row", backgroundColor: "#1b1e26", paddingVertical: 12 }}>
            {[["products", "Products"], ["inventory", "Inventory"]].map(([k, label]) => (
              <TouchableOpacity key={k} style={{ flex: 1, alignItems: "center" }} onPress={() => setTab(k)}>
                <Text style={{ color: tab === k ? "#4f7cff" : "#9aa3b2", fontWeight: "700" }}>{label}</Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity style={{ flex: 1, alignItems: "center" }} onPress={logout}>
              <Text style={{ color: "#9aa3b2", fontWeight: "700" }}>Logout</Text>
            </TouchableOpacity>
          </View>
        </>
      )}
    </SafeAreaView>
  );
}
