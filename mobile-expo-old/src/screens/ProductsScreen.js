import { useCallback, useEffect, useState } from "react";
import { Alert, RefreshControl, Text, View } from "react-native";
import { createProductWithSku, deleteProduct, getProducts, updateProduct, updateSku } from "../api";
import { Btn, Card, Chips, Empty, ErrorBanner, Field, Header, Page, Pill, Row, money } from "../components";
import { c, sp, type } from "../theme";

const STATUSES = ["DRAFT", "ACTIVE", "ARCHIVED"];
const allSkus = (p) => p.variants.flatMap((v) => v.skus);

export default function ProductsScreen() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [search, setSearch] = useState("");
  const [show, setShow] = useState(false);
  const [title, setTitle] = useState("");
  const [skuCode, setSku] = useState("");
  const [price, setPrice] = useState("");
  const [saving, setSaving] = useState(false);
  const [openId, setOpenId] = useState(null);
  const [edit, setEdit] = useState(null);

  const load = useCallback(async (q = "") => {
    setLoading(true); setErr("");
    try { setItems(await getProducts(q)); } catch (e) { setErr(e.message); }
    setLoading(false);
  }, []);
  useEffect(() => { load(""); }, [load]);

  async function add() {
    if (!title.trim() || !skuCode.trim() || !price) { setErr("Title, SKU code aur price teeno chahiye."); return; }
    setSaving(true); setErr("");
    try {
      await createProductWithSku({ title: title.trim(), skuCode: skuCode.trim(), price });
      setTitle(""); setSku(""); setPrice(""); setShow(false); load(search);
    } catch (e) { setErr(e.message); }
    setSaving(false);
  }

  function toggle(p) {
    if (openId === p.id) { setOpenId(null); return; }
    setOpenId(p.id);
    setEdit({ title: p.title, status: p.status,
      prices: Object.fromEntries(allSkus(p).map((k) => [k.id, String(k.price)])) });
  }

  async function save(p) {
    setErr("");
    try {
      await updateProduct(p.id, { title: edit.title.trim(), status: edit.status });
      for (const k of allSkus(p)) {
        if (edit.prices[k.id] !== String(k.price)) await updateSku(k.id, { price: edit.prices[k.id] });
      }
      setOpenId(null); load(search);
    } catch (e) { setErr(e.message); }
  }

  function remove(p) {
    Alert.alert("Product delete karna hai?", p.title, [
      { text: "Rehne do", style: "cancel" },
      { text: "Delete", style: "destructive", onPress: async () => {
        try { await deleteProduct(p.id); setOpenId(null); load(search); }
        catch (e) { setErr(e.message); }
      } },
    ]);
  }

  return (
    <Page refreshControl={<RefreshControl refreshing={loading} onRefresh={() => load(search)} tintColor={c.primary} />}>
      <Header title="Products" subtitle={`${items.length} products`} />
      <Field placeholder="Naam ya SKU se dhundo" value={search} onChangeText={setSearch}
        returnKeyType="search" onSubmitEditing={() => load(search)} style={{ marginBottom: sp.sm }} />
      <ErrorBanner text={err} />
      <Btn kind={show ? "quiet" : "primary"} label={show ? "Close" : "Add product"} onPress={() => setShow(!show)} style={{ marginBottom: sp.md }} />
      {show && (
        <Card>
          <Field label="Product name" value={title} onChangeText={setTitle} placeholder="Cotton shirt" />
          <Field label="SKU code" value={skuCode} onChangeText={setSku} autoCapitalize="characters" placeholder="SHIRT-BLU-M" hint="Har SKU ka code alag hona chahiye." />
          <Field label="Price (₹)" value={price} onChangeText={setPrice} keyboardType="decimal-pad" placeholder="499" />
          <Btn label="Save product" onPress={add} busy={saving} />
        </Card>
      )}
      {items.length === 0 && !loading && (
        <Empty title={search ? "Kuch nahi mila" : "Abhi koi product nahi"}
          hint={search ? "Dusra naam ya SKU try karo." : "Pehla product add karke shuru karo."} />
      )}
      {items.map((p) => {
        const skus = allSkus(p);
        const open = openId === p.id && edit;
        return (
          <Card key={p.id} onPress={() => toggle(p)}>
            <Row style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
              <View style={{ flex: 1, paddingRight: sp.md }}>
                <Text style={type.heading}>{p.title}</Text>
                <Text style={[type.small, { marginTop: 2 }]}>{skus.map((k) => k.sku_code).join(", ") || "No SKU"}</Text>
              </View>
              <View style={{ alignItems: "flex-end" }}>
                <Pill status={p.status} />
                {skus[0] && <Text style={[type.heading, type.num, { marginTop: 6 }]}>{money(skus[0].price)}</Text>}
              </View>
            </Row>
            {open && (
              <View style={{ marginTop: sp.lg, paddingTop: sp.lg, borderTopWidth: 1, borderTopColor: c.line }}>
                <Field label="Product name" value={edit.title} onChangeText={(t) => setEdit({ ...edit, title: t })} />
                <Text style={[type.label, { marginBottom: 6 }]}>Status</Text>
                <Chips options={STATUSES} value={edit.status} onChange={(st) => setEdit({ ...edit, status: st })} />
                {skus.map((k) => (
                  <Field key={k.id} label={`${k.sku_code} price (₹)`} keyboardType="decimal-pad"
                    value={edit.prices[k.id]} onChangeText={(t) => setEdit({ ...edit, prices: { ...edit.prices, [k.id]: t } })} />
                ))}
                <Row style={{ gap: sp.md }}>
                  <Btn label="Save changes" onPress={() => save(p)} style={{ flex: 2 }} />
                  <Btn label="Delete" kind="danger" onPress={() => remove(p)} style={{ flex: 1 }} />
                </Row>
              </View>
            )}
          </Card>
        );
      })}
    </Page>
  );
}
