// OmniSell design tokens. Indigo ink + marigold: kirana ledger ki syahi aur haldi.
export const c = {
  bg: "#F1F3F7",
  surface: "#FFFFFF",
  ink: "#161E3F",
  inkSoft: "#5B6485",
  inkFaint: "#8A92AE",
  line: "#E1E5EE",
  primary: "#1B2559",
  onPrimary: "#FFFFFF",
  accent: "#F2A900",
  accentSoft: "#FFF1D6",
  danger: "#B42318",
  dangerSoft: "#FDECEA",
  ok: "#12733F",
  okSoft: "#E3F4EA",
  warn: "#9A5B00",
  warnSoft: "#FFF1D6",
  info: "#27489E",
  infoSoft: "#E6ECFB",
};

export const r = { card: 16, field: 10, pill: 8, btn: 12 };
export const sp = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 };

export const type = {
  display: { fontSize: 30, fontWeight: "800", letterSpacing: -0.5, color: c.ink },
  title: { fontSize: 24, fontWeight: "800", letterSpacing: -0.3, color: c.ink },
  heading: { fontSize: 16, fontWeight: "700", color: c.ink },
  body: { fontSize: 15, color: c.ink },
  small: { fontSize: 13, color: c.inkSoft },
  label: { fontSize: 13, fontWeight: "600", color: c.inkSoft },
  num: { fontVariant: ["tabular-nums"] },
};

// Status -> rang. Har jagah (orders, jobs, listings, channels) ek hi mapping.
export const tone = {
  DRAFT: ["inkSoft", "bg"], ACTIVE: ["ok", "okSoft"], ARCHIVED: ["inkSoft", "bg"],
  IMPORTED: ["info", "infoSoft"], CONFIRMED: ["info", "infoSoft"], PACKED: ["warn", "warnSoft"],
  SHIPPED: ["warn", "warnSoft"], DELIVERED: ["ok", "okSoft"], CANCELLED: ["danger", "dangerSoft"],
  RETURNED: ["danger", "dangerSoft"],
  PENDING: ["warn", "warnSoft"], RUNNING: ["info", "infoSoft"], SUCCEEDED: ["ok", "okSoft"],
  FAILED: ["danger", "dangerSoft"], NEEDS_ACTION: ["warn", "warnSoft"], CONNECTED: ["ok", "okSoft"],
  ERROR: ["danger", "dangerSoft"],
};
