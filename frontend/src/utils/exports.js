// src/utils/exports.js
const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export function exportBalancePrueba({ inicio, fin } = {}) {
  // Si no hay ningún extremo, avisamos y salimos
  if (!inicio || !fin) {
  alert("Selecciona fecha inicio y fecha fin.");
  return false;
}

  const p = new URLSearchParams();
  if (inicio) p.append("fecha_inicio", inicio);
  if (fin)    p.append("fecha_fin",   fin);
  p.append("formato", "xlsx");
  window.open(`${BASE}/api/contabilidad/reportes/balance-pruebas/?${p.toString()}`, "_blank");
  return true;
}
