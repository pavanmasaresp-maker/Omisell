import { useCallback, useEffect, useState } from "react";
import { RefreshControl, Text, TouchableOpacity, View } from "react-native";
import { adjustStock, getBalances, getLedger, getSkus } from "../api";
import { Btn, Card, Empty, ErrorBanner, Field, Header, Page, Row } from "../components";
import { c, r, sp, type } from "../theme";

export default function InventoryScreen() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState(null);
  const [qty, setQty] = useState("1");
  const [hist, setHist] = useState({});

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

  const n = Math.max(parseInt(qty, 10) || 0, 0);
  const step = (d) => setQty(String(Math.max(n + d, 1)));

  async function apply(sign) {
    if (!n) { setErr("Quantity 1 ya usse zyada daalo."); return; }
    setErr("");
    try {
      await adjustStock(open, sign * n);
      setQty("1"); setHist({ ...hist, [open]: undefined }); setOpen(null); load();
    } catch (e) { setErr(e.message); }
  }

  async function toggleHistory(id) {
    if (hist[id]) { setHist({ ...hist, [id]: undefined }); return; }
    try { setHist({ ...hist, [id]: await getLedger(id) }); } catch (e) { setErr(e.message); }
  }

  return (
    <Page refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor={c.primary} />}>
      <Header title="Stock" subtitle="SKU par tap karke stock badlo" />
      <ErrorBanner text={err} />
      {rows.length === 0 && !loading && (
        <Empty title="Koi SKU nahi" hint="Pehle Products mein product aur SKU add karo." />
      )}
      {rows.map((item) => {
        const isOpen = open === item.id;
        const low = item.available <= 5;
        return (
          <Card key={item.id} onPress={() => { setOpen(isOpen ? null : item.id); setQty("1"); }}
            accent={item.available <= 0 ? c.danger : low ? c.accent : null}>
            <Row style={{ justifyContent: "space-between" }}>
              <View>
                <Text style={type.heading}>{item.code}</Text>
                <Text style={[type.small, { marginTop: 2 }]}>On hand {item.on_hand} · Reserved {item.reserved}</Text>
              </View>
              <View style={{ alignItems: "flex-end" }}>
                <Text style={[type.title, type.num, { color: item.available <= 0 ? c.danger : c.ink }]}>{item.available}</Text>
                <Text style={type.small}>available</Text>
              </View>
            </Row>
            {isOpen && (
              <View style={{ marginTop: sp.lg, paddingTop: sp.lg, borderTopWidth: 1, borderTopColor: c.line }}>
                <Text style={[type.label, { marginBottom: 6 }]}>Quantity</Text>
                <Row style={{ marginBottom: sp.md }}>
                  <TouchableOpacity onPress={() => step(-1)} style={stepBtn}><Text style={stepTxt}>−</Text></TouchableOpacity>
                  <Field value={qty} onChangeText={setQty} keyboardType="number-pad" style={{ flex: 1, marginBottom: 0, marginHorizontal: sp.sm }} />
                  <TouchableOpacity onPress={() => step(1)} style={stepBtn}><Text style={stepTxt}>+</Text></TouchableOpacity>
                </Row>
                <Row style={{ gap: sp.md }}>
                  <Btn label={`Add ${n || ""}`} onPress={() => apply(1)} style={{ flex: 1 }} />
                  <Btn label={`Remove ${n || ""}`} kind="danger" onPress={() => apply(-1)} style={{ flex: 1 }} />
                </Row>
                <Btn small kind="quiet" label={hist[item.id] ? "Hide history" : "Show history"} onPress={() => toggleHistory(item.id)} style={{ marginTop: sp.md }} />
                {hist[item.id] && hist[item.id].length === 0 && <Text style={[type.small, { marginTop: sp.md }]}>Abhi koi history nahi.</Text>}
                {hist[item.id] && hist[item.id].map((e) => (
                  <Row key={e.id} style={{ justifyContent: "space-between", paddingTop: sp.md }}>
                    <Text style={type.small}>{e.entry_type.toLowerCase()} · {new Date(e.created_at).toLocaleString()}</Text>
                    <Text style={[type.body, type.num, { fontWeight: "700", color: e.quantity_delta > 0 ? c.ok : c.danger }]}>
                      {e.quantity_delta > 0 ? "+" : ""}{e.quantity_delta}
                    </Text>
                  </Row>
                ))}
              </View>
            )}
          </Card>
        );
      })}
    </Page>
  );
}

const stepBtn = { width: 48, height: 48, borderRadius: r.field, backgroundColor: c.bg, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: c.line };
const stepTxt = { fontSize: 24, color: c.ink, fontWeight: "600" };
