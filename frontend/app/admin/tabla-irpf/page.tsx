"use client";

import { useEffect, useState } from "react";
import RequireAuth from "@/components/RequireAuth";
import { api, TramoIRPF } from "@/lib/api";

const initialForm = {
  anio: String(new Date().getFullYear()),
  base_desde_anual: "",
  base_hasta_anual: "",
  tipo_aplicable_pct: "",
  vigente_desde: "",
};

export default function TablaIRPFPage() {
  return (
    <RequireAuth soloAdmin>
      <Contenido />
    </RequireAuth>
  );
}

function Contenido() {
  const [tramos, setTramos] = useState<TramoIRPF[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function cargar() {
    setTramos(await api.admin.tablaIrpf.listar());
  }

  useEffect(() => {
    cargar().catch((e) => setError(String(e)));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await api.admin.tablaIrpf.crear({
        anio: Number(form.anio) as unknown as number,
        base_desde_anual: form.base_desde_anual as unknown as string,
        base_hasta_anual: form.base_hasta_anual ? (form.base_hasta_anual as unknown as string) : undefined,
        tipo_aplicable_pct: form.tipo_aplicable_pct as unknown as string,
        vigente_desde: form.vigente_desde as unknown as string,
      });
      setForm(initialForm);
      await cargar();
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  async function eliminar(t: TramoIRPF) {
    if (!window.confirm(`¿Eliminar el tramo ${t.base_desde_anual}€ - ${t.base_hasta_anual ?? "∞"}€ (${t.anio})?`)) return;
    await api.admin.tablaIrpf.eliminar(t.id);
    await cargar();
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">Tabla de tramos IRPF</h1>
      <p className="text-sm text-slate-500 mb-4">
        Procedimiento general simplificado de retención. Verifica los tramos oficiales AEAT antes de
        editar — ver docs/LEGAL_DISCLAIMER.md.
      </p>

      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 mb-6 grid sm:grid-cols-3 gap-3">
        <input
          required
          type="number"
          placeholder="Año"
          className="border rounded px-3 py-2"
          value={form.anio}
          onChange={(e) => setForm({ ...form, anio: e.target.value })}
        />
        <input
          required
          type="number"
          step="0.01"
          placeholder="Base desde (€/año)"
          className="border rounded px-3 py-2"
          value={form.base_desde_anual}
          onChange={(e) => setForm({ ...form, base_desde_anual: e.target.value })}
        />
        <input
          type="number"
          step="0.01"
          placeholder="Base hasta (€/año, vacío = sin límite)"
          className="border rounded px-3 py-2"
          value={form.base_hasta_anual}
          onChange={(e) => setForm({ ...form, base_hasta_anual: e.target.value })}
        />
        <input
          required
          type="number"
          step="0.01"
          placeholder="Tipo aplicable %"
          className="border rounded px-3 py-2"
          value={form.tipo_aplicable_pct}
          onChange={(e) => setForm({ ...form, tipo_aplicable_pct: e.target.value })}
        />
        <input
          required
          type="date"
          className="border rounded px-3 py-2"
          value={form.vigente_desde}
          onChange={(e) => setForm({ ...form, vigente_desde: e.target.value })}
        />
        <button disabled={cargando} className="bg-slate-900 text-white rounded py-2 disabled:opacity-50">
          {cargando ? "Guardando..." : "Añadir tramo"}
        </button>
      </form>

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2">Año</th>
            <th className="text-left p-2">Desde (€)</th>
            <th className="text-left p-2">Hasta (€)</th>
            <th className="text-left p-2">Tipo %</th>
            <th className="text-right p-2">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {tramos.map((t) => (
            <tr key={t.id} className="border-t">
              <td className="p-2">{t.anio}</td>
              <td className="p-2">{t.base_desde_anual}</td>
              <td className="p-2">{t.base_hasta_anual ?? "∞"}</td>
              <td className="p-2">{t.tipo_aplicable_pct}%</td>
              <td className="p-2 text-right">
                <button onClick={() => eliminar(t)} className="text-red-600 underline">
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
