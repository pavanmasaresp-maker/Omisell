import { useCallback, useEffect, useState } from "react";
import { RefreshControl, Text, View } from "react-native";
import { getDashboard } from "../api";
import { Card, Empty, ErrorBanner, Header, Page, Row, SectionTitle } from "../components";
import { c, r, sp, type } from "../theme";

export default function DashboardScreen({ go }) {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try { setD(await getDashboard()); } catch (e) { setErr(e.message); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  const avail = d ? Math.max(d.total_on_hand - d.total_reserved, 0) : 0;
  const share = d && d.total_on_hand > 0 ? d.total_reserved / d.total_on_hand : 0;

  return (
    <Page refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor={c.primary} />}>
      <Header title="Home" subtitle="Aapki dukaan ka aaj ka haal" />
      <ErrorBanner text={err} onRetry={load} />
      {d && (
        <>
          <View style={{ backgroundColor: c.primary, borderRadius: r.card, padding: sp.lg, marginBottom: sp.md }}>
            <Text style={{ color: "#B8C0E0", fontSize: 13, fontWeight: "600" }}>Sellable stock</Text>
            <Text style={[type.display, type.num, { color: "#fff", fontSize: 40, marginTop: 2 }]}>{avail}</Text>
            <View style={{ height: 8, borderRadius: 4, backgroundColor: "#3A4585", marginTop: sp.md, flexDirection: "row", overflow: "hidden" }}>
              <View style={{ flex: Math.max(1 - share, 0.001), backgroundColor: c.accent }} />
              <View style={{ flex: Math.max(share, 0.001) }} />
            </View>
            <Row style={{ justifyContent: "space-between", marginTop: sp.sm }}>
              <Text style={{ color: "#B8C0E0", fontSize: 13 }}>On hand {d.total_on_hand}</Text>
              <Text style={{ color: "#B8C0E0", fontSize: 13 }}>Reserved for orders {d.total_reserved}</Text>
            </Row>
          </View>

          <Row style={{ gap: sp.md }}>
            <Card style={{ flex: 1 }} onPress={() => go && go("products")}>
              <Text style={type.label}>Products</Text>
              <Text style={[type.title, type.num]}>{d.products}</Text>
            </Card>
            <Card style={{ flex: 1 }} onPress={() => go && go("stock")}>
              <Text style={type.label}>SKUs</Text>
              <Text style={[type.title, type.num]}>{d.skus}</Text>
            </Card>
          </Row>

          <SectionTitle>Running low (≤ {d.low_stock_threshold})</SectionTitle>
          {d.low_stock.length === 0 ? (
            <Empty title="Stock theek hai" hint="Koi SKU kam nahi pada." />
          ) : d.low_stock.map((i) => (
            <Card key={i.sku} accent={i.available <= 0 ? c.danger : c.accent} style={{ paddingVertical: sp.md }}>
              <Row style={{ justifyContent: "space-between" }}>
                <View style={{ flex: 1 }}>
                  <Text style={type.heading}>{i.sku_code}</Text>
                  <Text style={type.small}>{i.product}</Text>
                </View>
                <Text style={[type.title, type.num, { color: i.available <= 0 ? c.danger : c.warn }]}>{i.available}</Text>
              </Row>
            </Card>
          ))}

          <SectionTitle>Recent stock changes</SectionTitle>
          {d.recent.length === 0 ? (
            <Empty title="Abhi koi hisaab nahi" hint="Stock add karoge to yahan dikhega." />
          ) : (
            <Card style={{ paddingVertical: sp.xs }}>
              {d.recent.map((e, i) => (
                <Row key={i} style={{
                  justifyContent: "space-between", paddingVertical: sp.md,
                  borderTopWidth: i ? 1 : 0, borderTopColor: c.line,
                }}>
                  <View>
                    <Text style={type.body}>{e.sku_code}</Text>
                    <Text style={type.small}>{e.entry_type.toLowerCase()} · {new Date(e.created_at).toLocaleString()}</Text>
                  </View>
                  <Text style={[type.heading, type.num, { color: e.quantity_delta > 0 ? c.ok : c.danger }]}>
                    {e.quantity_delta > 0 ? "+" : ""}{e.quantity_delta}
                  </Text>
                </Row>
              ))}
            </Card>
          )}
        </>
      )}
    </Page>
  );
}
