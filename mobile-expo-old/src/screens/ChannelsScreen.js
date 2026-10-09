import { useCallback, useEffect, useState } from "react";
import { Alert, RefreshControl, Text, View } from "react-native";
import { checkConnection, createConnection, deleteConnection, getConnections } from "../api";
import { Btn, Card, Chips, Empty, ErrorBanner, Field, Header, Page, Pill, Row } from "../components";
import { c, sp, type } from "../theme";

export default function ChannelsScreen({ onBack }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [show, setShow] = useState(false);
  const [channel, setChannel] = useState("DEMO");
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [token, setToken] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try { setItems(await getConnections()); } catch (e) { setErr(e.message); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  async function connect() {
    if (!name.trim() || !token.trim()) { setErr("Naam aur token dono daalo."); return; }
    setSaving(true); setErr("");
    try {
      await createConnection({ channel, name: name.trim(), shop_domain: domain.trim(), access_token: token.trim() });
      setName(""); setDomain(""); setToken(""); setShow(false); load();
    } catch (e) { setErr(e.message); }
    setSaving(false);
  }

  async function recheck(id) {
    try { await checkConnection(id); load(); } catch (e) { setErr(e.message); }
  }

  function remove(item) {
    Alert.alert("Channel hataana hai?", item.name, [
      { text: "Rehne do", style: "cancel" },
      { text: "Hatao", style: "destructive", onPress: async () => {
        try { await deleteConnection(item.id); load(); } catch (e) { setErr(e.message); }
      } },
    ]);
  }

  return (
    <Page refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor={c.primary} />}>
      <Header title="Channels" subtitle="Jahan aap bechte ho" onBack={onBack} />
      <ErrorBanner text={err} />
      <Btn kind={show ? "quiet" : "primary"} label={show ? "Close" : "Connect a channel"} onPress={() => setShow(!show)} style={{ marginBottom: sp.md }} />
      {show && (
        <Card>
          <Text style={[type.label, { marginBottom: 6 }]}>Channel</Text>
          <Chips options={[{ value: "DEMO", label: "Demo (test)" }, { value: "SHOPIFY", label: "Shopify" }]} value={channel} onChange={setChannel} />
          <Field label="Name" value={name} onChangeText={setName} placeholder="My Shopify store" />
          {channel === "SHOPIFY" && (
            <Field label="Store address" value={domain} onChangeText={setDomain} autoCapitalize="none" placeholder="mystore.myshopify.com" />
          )}
          <Field label={channel === "DEMO" ? "Token" : "Access token"} value={token} onChangeText={setToken} autoCapitalize="none" secureTextEntry
            hint={channel === "DEMO" ? "Test ke liye 'demo' likho." : "Token encrypted save hota hai, wapas nahi dikhta."} />
          <Btn label="Connect" onPress={connect} busy={saving} />
        </Card>
      )}
      {items.length === 0 && !loading && <Empty title="Koi channel connected nahi" hint="Pehle Demo channel connect karke poora flow try kar sakte ho." />}
      {items.map((i) => (
        <Card key={i.id}>
          <Row style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
            <View style={{ flex: 1 }}>
              <Text style={type.heading}>{i.name}</Text>
              <Text style={type.small}>{i.channel === "DEMO" ? "Demo" : i.shop_domain}</Text>
            </View>
            <Pill status={i.status} />
          </Row>
          {!!i.last_error && <Text style={[type.small, { color: c.danger, marginTop: sp.sm }]}>{i.last_error}</Text>}
          <Row style={{ gap: sp.md, marginTop: sp.md }}>
            <Btn small kind="quiet" label="Check again" onPress={() => recheck(i.id)} style={{ flex: 1 }} />
            <Btn small kind="danger" label="Remove" onPress={() => remove(i)} style={{ flex: 1 }} />
          </Row>
        </Card>
      ))}
    </Page>
  );
}
