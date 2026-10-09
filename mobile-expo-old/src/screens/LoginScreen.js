import { useState } from "react";
import { Text, View } from "react-native";
import { login } from "../api";
import { saveToken } from "../storage";
import { Btn, ErrorBanner, Field } from "../components";
import { c, sp, type } from "../theme";

export default function LoginScreen({ onLoggedIn }) {
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!username.trim() || !password) { setErr("Username aur password dono daalo."); return; }
    setBusy(true); setErr("");
    try {
      const { token } = await login(username.trim(), password);
      await saveToken(token);
      onLoggedIn();
    } catch (e) { setErr(e.message); }
    setBusy(false);
  }

  return (
    <View style={{ flex: 1, backgroundColor: c.primary }}>
      <View style={{ flex: 1, justifyContent: "flex-end", padding: sp.xl }}>
        <View style={{ width: 44, height: 6, backgroundColor: c.accent, borderRadius: 3, marginBottom: sp.lg }} />
        <Text style={[type.display, { color: "#fff", fontSize: 38 }]}>OmniSell</Text>
        <Text style={{ color: "#B8C0E0", fontSize: 16, marginTop: 6 }}>Ek baar likho. Har jagah bechho.</Text>
      </View>
      <View style={{ backgroundColor: c.bg, borderTopLeftRadius: 28, borderTopRightRadius: 28, padding: sp.xl, paddingBottom: sp.xl * 1.5 }}>
        <Text style={[type.heading, { marginBottom: sp.lg }]}>Sign in</Text>
        <ErrorBanner text={err} />
        <Field label="Username" autoCapitalize="none" autoCorrect={false} value={username} onChangeText={setU} />
        <Field label="Password" secureTextEntry value={password} onChangeText={setP} onSubmitEditing={submit} />
        <Btn label="Sign in" onPress={submit} busy={busy} />
      </View>
    </View>
  );
}
