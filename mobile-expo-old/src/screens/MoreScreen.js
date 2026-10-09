import { Text, TouchableOpacity, View } from "react-native";
import { Card, Header, Page, Row } from "../components";
import { c, sp, type } from "../theme";

const ITEMS = [
  ["channels", "Channels", "Shopify aur doosre marketplaces connect karo"],
  ["sync", "Sync", "Publish aur stock updates ka status"],
];

export default function MoreScreen({ onOpen, onLogout }) {
  return (
    <Page>
      <Header title="More" />
      {ITEMS.map(([k, t, d]) => (
        <Card key={k} onPress={() => onOpen(k)}>
          <Row style={{ justifyContent: "space-between" }}>
            <View style={{ flex: 1 }}>
              <Text style={type.heading}>{t}</Text>
              <Text style={type.small}>{d}</Text>
            </View>
            <Text style={{ color: c.inkFaint, fontSize: 22 }}>›</Text>
          </Row>
        </Card>
      ))}
      <TouchableOpacity onPress={onLogout} style={{ marginTop: sp.lg, padding: sp.md }}>
        <Text style={{ color: c.danger, fontWeight: "700", fontSize: 15 }}>Sign out</Text>
      </TouchableOpacity>
    </Page>
  );
}
