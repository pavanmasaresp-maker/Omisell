import { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, Text, TextInput, TouchableOpacity, View } from "react-native";
import { adjustStock, getBalances, getSkus } from "../api";
import { s } from "../ui";

export default function InventoryScreen() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState(null);
  const [qty, setQty] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      const [skus, bals] = await Promise.all([getSkus(), getBalances()]);
      const byId = Object.fromEntries(bals.map((b) => [b.sku, b]));
      setRows(skus.map((k) => ({ id: k.id, code: k.sku_code,
        on_hand: byId[k.id]?.on_hand ?? 0, reserved: byId[k.id]?.reserved ?? 0,
        available: byId[k.id]?.available ?? 0 })));
    } catch (e) { setErr(e.message); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  async function apply(sign) {
    const n = parseInt(qty, 10);
    if (!n) return;
    try { await adjustStock(open, sign * n); setQty(""); setOpen(null); load(); }
    catch (e) { setErr(e.message); }
  }

  return (
    <View style={s.screen}>
      <Text style={s.title}>Inventory</Text>
      {!!err && <Text style={s.err}>{err}</Text>}
      <FlatList data={rows} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor="#fff" />}
        ListEmptyComponent={<Text style={s.sub}>Pehle Products mein SKU banao.</Text>}
        renderItem={({ item }) => (
          <TouchableOpacity style={s.card} onPress={() => setOpen(open === item.id ? null : item.id)}>
            <Text style={s.name}>{item.code}</Text>
            <Text style={s.sub}>On hand {item.on_hand} • Reserved {item.reserved} • Available {item.available}</Text>
            {open === item.id && (
              <View>
                <TextInput style={[s.input, { marginTop: 10 }]} placeholder="Quantity" placeholderTextColor="#777"
                  keyboardType="number-pad" value={qty} onChangeText={setQty} />
                <View style={s.row}>
                  <TouchableOpacity style={[s.btn, { flex: 1 }]} onPress={() => apply(1)}><Text style={s.btnText}>+ Add</Text></TouchableOpacity>
                  <TouchableOpacity style={[s.btn, { flex: 1, backgroundColor: "#c0504d" }]} onPress={() => apply(-1)}><Text style={s.btnText}>− Remove</Text></TouchableOpacity>
                </View>
              </View>
            )}
          </TouchableOpacity>
        )} />
    </View>
  );
}
