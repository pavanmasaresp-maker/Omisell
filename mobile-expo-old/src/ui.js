import { StyleSheet } from "react-native";

export const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#0f1115", padding: 16 },
  title: { color: "#fff", fontSize: 22, fontWeight: "700", marginBottom: 12 },
  input: { backgroundColor: "#1b1e26", color: "#fff", borderRadius: 10, padding: 12, marginBottom: 10 },
  btn: { backgroundColor: "#4f7cff", borderRadius: 10, padding: 13, alignItems: "center", marginBottom: 10 },
  btnText: { color: "#fff", fontWeight: "700" },
  card: { backgroundColor: "#1b1e26", borderRadius: 12, padding: 14, marginBottom: 10 },
  name: { color: "#fff", fontSize: 16, fontWeight: "600" },
  sub: { color: "#9aa3b2", marginTop: 3 },
  err: { color: "#ff6b6b", marginBottom: 10 },
  row: { flexDirection: "row", gap: 8, marginTop: 10 },
  chip: { paddingVertical: 8, paddingHorizontal: 12, borderRadius: 20, backgroundColor: "#262a35" },
  chipOn: { backgroundColor: "#4f7cff" },
  chipText: { color: "#fff", fontWeight: "600", fontSize: 12 },
});
