import { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, Text, TextInput, TouchableOpacity, View } from "react-native";
import { createProductWithSku, getProducts } from "../api";
import { s } from "../ui";

export default function ProductsScreen() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [show, setShow] = useState(false);
  const [title, setTitle] = useState("");
  const [skuCode, setSku] = useState("");
  const [price, setPrice] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try { setItems(await getProducts()); } catch (e) { setErr(e.message); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  async function add() {
    try {
      await createProductWithSku({ title: title.trim(), skuCode: skuCode.trim(), price });
      setTitle(""); setSku(""); setPrice(""); setShow(false); load();
    } catch (e) { setErr(e.message); }
  }

  return (
    <View style={s.screen}>
      <Text style={s.title}>Products</Text>
      {!!err && <Text style={s.err}>{err}</Text>}
      <TouchableOpacity style={s.btn} onPress={() => setShow(!show)}>
        <Text style={s.btnText}>{show ? "Cancel" : "+ Add product"}</Text>
      </TouchableOpacity>
      {show && (
        <View>
          <TextInput style={s.input} placeholder="Title" placeholderTextColor="#777" value={title} onChangeText={setTitle} />
          <TextInput style={s.input} placeholder="SKU code" placeholderTextColor="#777" autoCapitalize="characters" value={skuCode} onChangeText={setSku} />
          <TextInput style={s.input} placeholder="Price" placeholderTextColor="#777" keyboardType="decimal-pad" value={price} onChangeText={setPrice} />
          <TouchableOpacity style={s.btn} onPress={add}><Text style={s.btnText}>Save</Text></TouchableOpacity>
        </View>
      )}
      <FlatList data={items} keyExtractor={(i) => i.id}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor="#fff" />}
        ListEmptyComponent={<Text style={s.sub}>Koi product nahi. Upar se add karo.</Text>}
        renderItem={({ item }) => (
          <View style={s.card}>
            <Text style={s.name}>{item.title}</Text>
            <Text style={s.sub}>{item.status} • {item.variants.reduce((n, v) => n + v.skus.length, 0)} SKU</Text>
          </View>
        )} />
    </View>
  );
}
