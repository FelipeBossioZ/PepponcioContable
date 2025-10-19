import axios from "axios";
const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const api = axios.create({ baseURL: BASE, withCredentials: false });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;
let pending = [];
const processQueue = (err, token = null) => { pending.forEach(p => err ? p.reject(err) : p.resolve(token)); pending = []; };

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      const refresh = localStorage.getItem("refresh");
      if (!refresh) { localStorage.removeItem("access"); localStorage.removeItem("refresh"); return Promise.reject(err); }
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pending.push({ resolve: (token)=>{ original.headers.Authorization = `Bearer ${token}`; resolve(api.request(original)); }, reject });
        });
      }
      original._retry = true; isRefreshing = true;
      try {
        const { data } = await axios.post(`${BASE}/api/token/refresh/`, { refresh });
        const newAccess = data.access; localStorage.setItem("access", newAccess);
        isRefreshing = false; processQueue(null, newAccess);
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api.request(original);
      } catch (e) {
        isRefreshing = false; processQueue(e, null);
        localStorage.removeItem("access"); localStorage.removeItem("refresh");
        return Promise.reject(e);
      }
    }
    return Promise.reject(err);
  }
);

export const login = async ({ username, password }) => {
  const { data } = await api.post("/api/token/", { username, password });
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
  return data;
};
export const logout = () => { localStorage.removeItem("access"); localStorage.removeItem("refresh"); };

// --- FACTURAS (CRUD) ---
export const getInvoices = (params = {}) =>
  api.get("/api/facturacion/facturas/", { params }).then(r => r.data);

export const createInvoice = (payload) =>
  api.post("/api/facturacion/facturas/", payload).then(r => r.data);

export const updateInvoice = ({ id, ...payload }) =>
  api.put(`/api/facturacion/facturas/${id}/`, payload).then(r => r.data);

export const deleteInvoice = (id) =>
  api.delete(`/api/facturacion/facturas/${id}/`).then(r => r.data);

/* =======================
   TERCEROS
   Base: /api/terceros/terceros/
======================= */
export const getTerceros = (params = {}) =>
  api.get("/api/terceros/terceros/", { params }).then(r => r.data);

export const createTercero = (payload) =>
  api.post("/api/terceros/terceros/", payload).then(r => r.data);

export const updateTercero = ({ id, ...payload }) =>
  api.put(`/api/terceros/terceros/${id}/`, payload).then(r => r.data);

export const deleteTercero = (id) =>
  api.delete(`/api/terceros/terceros/${id}/`).then(r => r.data);


/* =======================
   CONTABILIDAD
   Cuentas y Asientos + reportes
   Base: /api/contabilidad/
======================= */
// Cuentas (lista/búsqueda)
export const getCuentas = (params = {}) =>
  api.get("/api/contabilidad/cuentas/", { params }).then(r => r.data);

// Asientos (lista y crear)
export const getAsientos = (params = {}) =>
  api.get("/api/contabilidad/asientos/", { params }).then(r => r.data);

export const createAsiento = (payload) =>
  api.post("/api/contabilidad/asientos/", payload).then(r => r.data);

// Reportes
export const getLibroDiario = (params = {}) =>
  api.get("/api/contabilidad/libro-diario/", { params }).then(r => r.data);

export const getBalancePruebas = (params = {}) =>
  api.get("/api/contabilidad/balance-pruebas/", { params }).then(r => r.data);

// Libro mayor por código de cuenta (string)
export const getLibroMayor = (codigoCuenta, params = {}) =>
  api.get(`/api/contabilidad/libro-mayor/${codigoCuenta}/`, { params }).then(r => r.data);

// Estado de Resultados (requiere ?fecha_fin=YYYY-MM-DD)
export const getEstadoResultados = (params = {}) =>
  api.get("/api/contabilidad/estado-resultados/", { params }).then(r => r.data);

// Balance General (requiere ?fecha_fin=YYYY-MM-DD)
export const getBalanceGeneral = (params = {}) =>
  api.get("/api/contabilidad/balance-general/", { params }).then(r => r.data);

// Anular asiento (con motivo + PINs opcionales enero–marzo)
export const annulAsiento = ({ id, motivo, contador_pin, gerente_pin }) =>
  api.post(`/api/contabilidad/asientos/${id}/anular/`, { motivo, contador_pin, gerente_pin }).then(r => r.data);

