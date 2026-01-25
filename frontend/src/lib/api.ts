export const API_BASE = import.meta.env.VITE_API_BASE;

if (!API_BASE) {
  throw new Error("VITE_API_BASE is not defined");
}

export const api = (path: string) =>
  `${API_BASE}/api/v1${path}`;
