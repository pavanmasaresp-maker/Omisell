import { ActivityIndicator, ScrollView, Text, TextInput, TouchableOpacity, View } from "react-native";
import { c, r, sp, tone, type } from "./theme";

export const money = (v) => "₹" + Number(v || 0).toLocaleString("en-IN");

export function Header({ title, subtitle, right, onBack }) {
  return (
    <View style={{ paddingHorizontal: sp.lg, paddingTop: sp.lg, paddingBottom: sp.md }}>
      {onBack && (
        <TouchableOpacity onPress={onBack} hitSlop={{ top: 10, bottom: 10, left: 10, right: 20 }}>
          <Text style={[type.label, { color: c.primary, marginBottom: sp.sm }]}>‹ Back</Text>
        </TouchableOpacity>
      )}
      <View style={{ flexDirection: "row", alignItems: "flex-end", justifyContent: "space-between" }}>
        <View style={{ flex: 1 }}>
          <Text style={type.title}>{title}</Text>
          {!!subtitle && <Text style={[type.small, { marginTop: 2 }]}>{subtitle}</Text>}
        </View>
        {right}
      </View>
    </View>
  );
}

export function Page({ children, scroll = true, refreshControl, pad = true }) {
  const style = { flex: 1, backgroundColor: c.bg };
  if (!scroll) return <View style={style}>{children}</View>;
  return (
    <ScrollView style={style} refreshControl={refreshControl} keyboardShouldPersistTaps="handled"
      contentContainerStyle={{ paddingBottom: sp.xl * 2, paddingHorizontal: pad ? sp.lg : 0 }}>
      {children}
    </ScrollView>
  );
}

export function Card({ children, style, onPress, accent }) {
  const base = {
    backgroundColor: c.surface, borderRadius: r.card, padding: sp.lg, marginBottom: sp.md,
    borderWidth: 1, borderColor: c.line,
    ...(accent ? { borderLeftWidth: 4, borderLeftColor: accent } : null),
  };
  if (onPress) {
    return <TouchableOpacity activeOpacity={0.85} onPress={onPress} style={[base, style]}>{children}</TouchableOpacity>;
  }
  return <View style={[base, style]}>{children}</View>;
}

const BTN = {
  primary: { bg: c.primary, fg: c.onPrimary, border: c.primary },
  accent: { bg: c.accent, fg: c.ink, border: c.accent },
  quiet: { bg: c.surface, fg: c.ink, border: c.line },
  danger: { bg: c.surface, fg: c.danger, border: "#F0C4BF" },
};
export function Btn({ label, onPress, kind = "primary", busy, disabled, style, small }) {
  const k = BTN[kind];
  return (
    <TouchableOpacity activeOpacity={0.8} onPress={onPress} disabled={busy || disabled}
      style={[{
        backgroundColor: k.bg, borderColor: k.border, borderWidth: 1, borderRadius: r.btn,
        paddingVertical: small ? 10 : 14, paddingHorizontal: sp.lg, alignItems: "center",
        justifyContent: "center", opacity: disabled ? 0.45 : 1, minHeight: small ? 40 : 48,
      }, style]}>
      {busy ? <ActivityIndicator color={k.fg} /> :
        <Text style={{ color: k.fg, fontWeight: "700", fontSize: small ? 14 : 15 }}>{label}</Text>}
    </TouchableOpacity>
  );
}

export function Field({ label, hint, style, ...props }) {
  return (
    <View style={[{ marginBottom: sp.md }, style]}>
      {!!label && <Text style={[type.label, { marginBottom: 6 }]}>{label}</Text>}
      <TextInput placeholderTextColor={c.inkFaint} {...props}
        style={{
          backgroundColor: c.surface, borderWidth: 1, borderColor: c.line, borderRadius: r.field,
          paddingHorizontal: 14, paddingVertical: 12, fontSize: 16, color: c.ink,
        }} />
      {!!hint && <Text style={[type.small, { marginTop: 4 }]}>{hint}</Text>}
    </View>
  );
}

export function Chips({ options, value, onChange, scroll }) {
  const row = options.map((o) => {
    const opt = typeof o === "string" ? { value: o, label: o || "All" } : o;
    const on = value === opt.value;
    return (
      <TouchableOpacity key={String(opt.value)} onPress={() => onChange(opt.value)} activeOpacity={0.8}
        style={{
          paddingVertical: 8, paddingHorizontal: 14, borderRadius: r.pill, marginRight: 8, marginBottom: 8,
          backgroundColor: on ? c.primary : c.surface, borderWidth: 1, borderColor: on ? c.primary : c.line,
        }}>
        <Text style={{ color: on ? c.onPrimary : c.ink, fontWeight: "600", fontSize: 13 }}>{opt.label}</Text>
      </TouchableOpacity>
    );
  });
  if (scroll) {
    return (
      <ScrollView horizontal showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: sp.lg }} style={{ flexGrow: 0 }}>{row}</ScrollView>
    );
  }
  return <View style={{ flexDirection: "row", flexWrap: "wrap" }}>{row}</View>;
}

const LABEL = { NEEDS_ACTION: "Needs action", IMPORTED: "New" };
export function Pill({ status }) {
  const [fg, bg] = tone[status] || ["inkSoft", "bg"];
  const text = LABEL[status] || status.charAt(0) + status.slice(1).toLowerCase();
  return (
    <View style={{ alignSelf: "flex-start", backgroundColor: c[bg], borderRadius: r.pill, paddingVertical: 3, paddingHorizontal: 9 }}>
      <Text style={{ color: c[fg], fontWeight: "700", fontSize: 12 }}>{text}</Text>
    </View>
  );
}

export function ErrorBanner({ text, onRetry }) {
  if (!text) return null;
  return (
    <View style={{
      backgroundColor: c.dangerSoft, borderRadius: r.field, padding: sp.md, marginBottom: sp.md,
      flexDirection: "row", alignItems: "center",
    }}>
      <Text style={{ color: c.danger, flex: 1, fontSize: 14 }}>{text}</Text>
      {onRetry && (
        <TouchableOpacity onPress={onRetry} style={{ paddingLeft: sp.md }}>
          <Text style={{ color: c.danger, fontWeight: "800" }}>Retry</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

export function Notice({ text, tone: t = "info" }) {
  if (!text) return null;
  const [fg, bg] = t === "ok" ? ["ok", "okSoft"] : ["info", "infoSoft"];
  return (
    <View style={{ backgroundColor: c[bg], borderRadius: r.field, padding: sp.md, marginBottom: sp.md }}>
      <Text style={{ color: c[fg], fontSize: 14 }}>{text}</Text>
    </View>
  );
}

export function Empty({ title, hint, action }) {
  return (
    <View style={{
      alignItems: "center", padding: sp.xl, borderRadius: r.card, borderWidth: 1,
      borderColor: c.line, borderStyle: "dashed", marginBottom: sp.md,
    }}>
      <Text style={[type.heading, { textAlign: "center" }]}>{title}</Text>
      {!!hint && <Text style={[type.small, { textAlign: "center", marginTop: 4 }]}>{hint}</Text>}
      {action && <View style={{ marginTop: sp.md, alignSelf: "stretch" }}>{action}</View>}
    </View>
  );
}

export function SectionTitle({ children, right }) {
  return (
    <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: sp.md, marginBottom: sp.sm }}>
      <Text style={type.heading}>{children}</Text>
      {right}
    </View>
  );
}

export function Row({ children, style }) {
  return <View style={[{ flexDirection: "row", alignItems: "center" }, style]}>{children}</View>;
}
