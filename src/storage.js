import * as SecureStore from "expo-secure-store";

const KEY = "omnisell_token";
export const getToken = () => SecureStore.getItemAsync(KEY);
export const saveToken = (t) => SecureStore.setItemAsync(KEY, t);
export const clearToken = () => SecureStore.deleteItemAsync(KEY);
