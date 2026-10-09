import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

const KEY = "omnisell_token";

// expo-secure-store has no web implementation — it throws "Unavailable"
// on web for every call, including inside a catch block, which silently
// stops App.js's check() before it ever sets ready=true (stuck blue screen).
// Use localStorage on web, SecureStore on native.
const isWeb = Platform.OS === "web";

async function webGet(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
async function webSet(key, val) {
  try { localStorage.setItem(key, val); } catch {}
}
async function webDel(key) {
  try { localStorage.removeItem(key); } catch {}
}

export const getToken = () => (isWeb ? webGet(KEY) : SecureStore.getItemAsync(KEY));
export const saveToken = (t) => (isWeb ? webSet(KEY, t) : SecureStore.setItemAsync(KEY, t));
export const clearToken = () => (isWeb ? webDel(KEY) : SecureStore.deleteItemAsync(KEY));
