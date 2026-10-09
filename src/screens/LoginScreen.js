import { useState } from "react";
import { Text, TextInput, TouchableOpacity, View, ActivityIndicator } from "react-native";
import { login } from "../api";
import { saveToken } from "../storage";
import { s } from "../ui";

export default function LoginScreen({ onLoggedIn }) {
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true); setErr("");
    try {
      const { token } = await login(username.trim(), password);
      await saveToken(token);
      onLoggedIn();
    } catch (e) { setErr(e.message); }
    setBusy(false);
  }
  return (
    <View style={[s.screen, { justifyContent: "center" }]}>
      <Text style={s.title}>OmniSell</Text>
      <TextInput style={s.input} placeholder="Username" placeholderTextColor="#777"
        autoCapitalize="none" value={username} onChangeText={setU} />
      <TextInput style={s.input} placeholder="Password" placeholderTextColor="#777"
        secureTextEntry value={password} onChangeText={setP} />
      {!!err && <Text style={s.err}>{err}</Text>}
      <TouchableOpacity style={s.btn} onPress={submit} disabled={busy}>
        {busy ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Login</Text>}
      </TouchableOpacity>
    </View>
  );
}
