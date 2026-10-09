import { useCallback, useEffect, useState } from "react";
import { Alert, RefreshControl, Text, View } from "react-native";
import { cancelOrder, confirmOrder, createOrder, deliverOrder, getOrders, getSkus, packOrder, shipOrder } from "../api";
import { Btn, Card, Chips, Empty, ErrorBanner, Field, Header, Page, Pill, Row, money } from "../components";
import { c, sp, type } from "../theme";

const NEXT_ACTION = {
  IMPORTED: { label: "Confirm order", fn: confirmOrder },
  CONFIRMED: { label: "Mark packed", fn: packOrder },
  PACKED: { label: "Mark shipped", fn: (id) => shipOrder(id, {}) },
  SHIPPED: { label: "Mark delivered", fn: deliverOrder },
};
const CANCELLABLE = new Set(["IMPORTED", "CONFIRMED", "PACKED"]);
const FILTERS = [{ value: "", label: "All" }, ...["IMPORTED", "CONFIRMED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"]
  .map((v) => ({ value: v, label: v === "IMPORTED" ? "New" : v.charAt(0) + v.slice(1).toLowerCase() }))];

export default function OrdersScreen() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [filter, setFilter] = useState("");
  const [show, setShow] = useState(false);
  const [skus, setSkus] = useState([]);
  const [customerName, setCustomerName] = useState("");
  const [skuCode, setSkuCode] = useState("");
  const [qty, setQty] = useState("1");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async (st = "") => {
    setLoading(true); setErr("");
    try { setItems(await getOrders(st)); } catch (e) { setErr(e.message); }
    setLoading(false);
  }, []);
  useEffect(() => { load(filter); }, [load, filter]);
  useEffect(() => { getSkus().then(setSkus).catch(() => {}); }, []);

  async function add() {
    const sku = skus.find((k) => k.sku_code.toLowerCase() === skuCode.trim().toLowerCase());
    if (!sku) { setErr(`SKU "${skuCode}" nahi mila. Neeche se chuno.`); return; }
    setSaving(true); setErr("");
    try {
      await createOrder({ customer_name: customerName.trim(), items: [{ sku: sku.id, quantity: parseInt(qty, 10) || 1 }] });
      setCustomerName(""); setSkuCode(""); setQty("1"); setShow(false); load(filter);
    } catch (e) { setErr(e.message); }
    setSaving(false);
  }

  async function act(order, fn) {
    setErr("");
    try { await fn(order.id); load(filter); } catch (e) { setErr(e.message); }
  }

  function cancel(order) {
    Alert.alert("Order cancel karni hai?", order.order_number, [
      { text: "Nahi", style: "cancel" },
      { text: "Cancel order", style: "destructive", onPress: async () => {
        try { await cancelOrder(order.id, "customer/seller request"); load(filter); }
        catch (e) { setErr(e.message); }
      } },
    ]);
  }

  const suggestions = skus.filter((k) => !skuCode || k.sku_code.toLowerCase().includes(skuCode.trim().toLowerCase())).slice(0, 6);

  return (
    <Page pad={false} refreshControl={<RefreshControl refreshing={loading} onRefresh={() => load(filter)} tintColor={c.primary} />}>
      <Header title="Orders" subtitle="Order aane se delivery tak" />
      <Chips scroll options={FILTERS} value={filter} onChange={setFilter} />
      <View style={{ paddingHorizontal: sp.lg, marginTop: sp.sm }}>
        <ErrorBanner text={err} />
        <Btn kind={show ? "quiet" : "primary"} label={show ? "Close" : "New order"} onPress={() => setShow(!show)} style={{ marginBottom: sp.md }} />
        {show && (
          <Card>
            <Field label="Customer name" value={customerName} onChangeText={setCustomerName} placeholder="Ramesh Traders" />
            <Field label="SKU code" value={skuCode} onChangeText={setSkuCode} autoCapitalize="characters" />
            {suggestions.length > 0 && (
              <View style={{ marginTop: -sp.sm, marginBottom: sp.sm }}>
                <Chips options={suggestions.map((k) => ({ value: k.sku_code, label: k.sku_code }))} value={skuCode} onChange={setSkuCode} />
              </View>
            )}
            <Field label="Quantity" value={qty} onChangeText={setQty} keyboardType="number-pad" />
            <Btn label="Create order" onPress={add} busy={saving} />
          </Card>
        )}
        {items.length === 0 && !loading && (
          <Empty title="Koi order nahi" hint={filter ? "Is status mein koi order nahi hai." : "Pehla order banao ya channel se import hone do."} />
        )}
        {items.map((o) => {
          const next = NEXT_ACTION[o.status];
          return (
            <Card key={o.id}>
              <Row style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1 }}>
                  <Text style={type.heading}>{o.order_number}</Text>
                  <Text style={type.small}>{o.customer_name || "Customer ka naam nahi"}</Text>
                </View>
                <Pill status={o.status} />
              </Row>
              <View style={{ marginTop: sp.md, paddingTop: sp.md, borderTopWidth: 1, borderTopColor: c.line }}>
                {o.items.map((li) => (
                  <Row key={li.id} style={{ justifyContent: "space-between", paddingVertical: 2 }}>
                    <Text style={type.body}>{li.sku_code} × {li.quantity}</Text>
                    <Text style={[type.small, type.num]}>{money(li.unit_price)}</Text>
                  </Row>
                ))}
                <Row style={{ justifyContent: "space-between", marginTop: sp.sm }}>
                  <Text style={type.label}>Total</Text>
                  <Text style={[type.heading, type.num]}>{money(o.total_amount)}</Text>
                </Row>
              </View>
              {(next || CANCELLABLE.has(o.status)) && (
                <Row style={{ gap: sp.md, marginTop: sp.md }}>
                  {next && <Btn label={next.label} onPress={() => act(o, next.fn)} style={{ flex: 2 }} small />}
                  {CANCELLABLE.has(o.status) && <Btn label="Cancel" kind="danger" onPress={() => cancel(o)} style={{ flex: 1 }} small />}
                </Row>
              )}
            </Card>
          );
        })}
      </View>
    </Page>
  );
}
