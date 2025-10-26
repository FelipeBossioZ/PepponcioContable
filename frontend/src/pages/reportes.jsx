// frontend/src/pages/reportes.jsx
import { useState } from "react";
import { exportBalancePrueba } from "../utils/exports";
import { toast } from "../ui/ToastHost";

// helpers de fecha
function todayISO() { const d = new Date(); return d.toISOString().slice(0,10); }
function firstDayOfMonth(d = new Date()) { return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0,10); }
function lastDayOfMonth(d = new Date())  { return new Date(d.getFullYear(), d.getMonth()+1, 0).toISOString().slice(0,10); }

export default function Reportes() {
  const [ini, setIni] = useState(firstDayOfMonth());
  const [fin, setFin] = useState(lastDayOfMonth());

  const onExportBalance = async () => {
    if (!ini && !fin) return toast("Selecciona rango de fechas", "error");
    try {
      await exportBalancePrueba({ inicio: ini, fin });
      toast("Export listo");
    } catch (e) {
      console.error(e);
      toast("No se pudo exportar", "error");
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Reportes</h1>
        <p className="text-gray-600">Exporta balances por período.</p>
      </div>

      {/* Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-sm mb-1">Fecha inicio</label>
          <input type="date" value={ini} onChange={(e)=>setIni(e.target.value)} className="border rounded px-3 py-2 w-full"/>
        </div>
        <div>
          <label className="block text-sm mb-1">Fecha fin</label>
          <input type="date" value={fin} onChange={(e)=>setFin(e.target.value)} className="border rounded px-3 py-2 w-full"/>
        </div>
        <div className="flex items-end">
          <button
            onClick={onExportBalance}
            className="inline-flex items-center px-2 py-2 rounded border-0 bg-[#fbcfe8] text-[#3b0764] hover:bg-[#e5bdfb]"
          >
            Exportar Balance Prueba
          </button>
        </div>
      </div>

      {/* Aquí más tarjetas cuando activemos Diario/Mayor */}
    </div>
  );
}
