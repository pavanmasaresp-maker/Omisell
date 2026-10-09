import { useCallback, useEffect, useState } from "react";
import { RefreshControl, Text, View } from "react-native";
import { getConnections, getJobs, getListings, getProducts, publishProduct, retryJob } from "../api";
import { Btn, Card, Chips, Empty, ErrorBanner, Header, Notice, Page, Pill, Row, SectionTitle } from "../components";
import { c, sp, type } from "../theme";

export default function SyncScreen({ onBack }) {
  const [conns, setConns] = useState([]);
  const [products, setProducts] = useState([]);
  const [listings, setListings] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [connId, setConnId] = useState(null);
  const [productId, setProductId] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      const [cn, p, l, j] = await Promise.all([getConnections(), getProducts(), getListings(), getJobs()]);
      setConns(cn.filter((x) => x.status === "CONNECTED")); setProducts(p); setListings(l); setJobs(j);
    } catch (e) { setErr(e.message); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  async function publish() {
    setErr(""); setMsg("");
    if (!connId || !productId) { setErr("Channel aur product dono chuno."); return; }
    setBusy(true);
    try {
      await publishProduct(productId, connId);
      setMsg("Publish queue mein gaya. Worker chalte hi ho jayega. Neeche khinch kar refresh karo.");
      load();
    } catch (e) { setErr(e.message); }
    setBusy(false);
  }
  async function retry(id) {
    try { await retryJob(id); load(); } catch (e) { setErr(e.message); }
  }

  const pending = jobs.filter((j) => j.status === "PENDING").length;
  return (
    <Page refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor={c.primary} />}>
      <Header title="Sync" subtitle="Product channel par bhejo, stock apne aap update hoga" onBack={onBack} />
      <ErrorBanner text={err} />
      <Notice text={msg} tone="ok" />

      <Card>
        <Text style={[type.label, { marginBottom: 6 }]}>Channel</Text>
        {conns.length === 0
          ? <Text style={[type.small, { marginBottom: sp.md }]}>Pehle More › Channels mein koi channel connect karo.</Text>
          : <Chips options={conns.map((x) => ({ value: x.id, label: x.name }))} value={connId} onChange={setConnId} />}
        <Text style={[type.label, { marginBottom: 6, marginTop: sp.sm }]}>Product</Text>
        {products.length === 0
          ? <Text style={[type.small, { marginBottom: sp.md }]}>Abhi koi product nahi.</Text>
          : <Chips options={products.map((x) => ({ value: x.id, label: x.title }))} value={productId} onChange={setProductId} />}
        <Btn label="Publish" onPress={publish} busy={busy} disabled={!connId || !productId} style={{ marginTop: sp.sm }} />
      </Card>

      <SectionTitle>Listings</SectionTitle>
      {listings.length === 0 && <Empty title="Abhi kuch publish nahi hua" hint="Upar se channel aur product chuno." />}
      {listings.map((l) => (
        <Card key={l.id} accent={l.status === "FAILED" ? c.danger : l.status === "NEEDS_ACTION" ? c.accent : null}>
          <Row style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
            <View style={{ flex: 1 }}>
              <Text style={type.heading}>{l.product_title}</Text>
              <Text style={type.small}>{l.connection_name}</Text>
            </View>
            <Pill status={l.status} />
          </Row>
          {!!l.last_error && <Text style={[type.small, { color: c.danger, marginTop: sp.sm }]}>{l.last_error}</Text>}
        </Card>
      ))}

      <SectionTitle>Activity</SectionTitle>
      {pending > 0 && <Notice text={`${pending} job wait kar rahe hain. Worker chal raha hai? (python manage.py run_sync_worker)`} />}
      {jobs.length === 0 && <Empty title="Abhi koi activity nahi" />}
      {jobs.map((j) => (
        <Card key={j.id}>
          <Row style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
            <View style={{ flex: 1, paddingRight: sp.md }}>
              <Text style={type.body}>{j.job_type === "PUBLISH_PRODUCT" ? "Publish" : "Stock update"} · {j.product_title}{j.sku_code ? ` (${j.sku_code})` : ""}</Text>
              <Text style={type.small}>{j.connection_name} · try {j.attempts}/{j.max_attempts}</Text>
            </View>
            <Pill status={j.status} />
          </Row>
          {!!j.last_error && <Text style={[type.small, { color: c.danger, marginTop: sp.sm }]}>{j.last_error}</Text>}
          {(j.status === "FAILED" || j.status === "NEEDS_ACTION") && (
            <Btn small kind="quiet" label="Try again" onPress={() => retry(j.id)} style={{ marginTop: sp.md }} />
          )}
        </Card>
      ))}
    </Page>
  );
}
