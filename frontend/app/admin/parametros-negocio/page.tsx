"use client";

import { useEffect, useState } from "react";
import RequireAuth from "@/components/RequireAuth";
import { api, ParametroNegocio } from "@/lib/api";

export default function ParametrosNegocioPage() {
  return (
    <RequireAuth soloAdmin>
      <Contenido />
    </RequireAuth>
  );
}

function Contenido() {
  const [parametros, setParametros] = useState<ParametroNegocio[]>([]);
  const [valores, setValores] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [guardandoId, setGuardandoId] = useState<number | null>(null);
  const [guardadoId, setGuardadoId] = useState<number | null>(null);

  async function cargar() {
    const datos = await api.admin.parametrosNegocio.listar();
    setParametros(datos);
    setValores(Object.fromEntries(datos.map((p) => [p.id, p.valor])));
  }

  useEffect(() => {
    cargar().catch((e) => setError(String(e)));
  }, []);

  async function guardar(p: ParametroNegocio) {
    setError(null);
    setGuardandoId(p.id);
    setGuardadoId(null);
    try {
      await api.admin.parametrosNegocio.actualizar(p.id, valores[p.id]);
      await cargar();
      setGuardadoId(p.id);
    } catch (err) {
      setError(String(err));
    } finally {
      setGuardandoId(null);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold mb-2">Parámetros de negocio</h1>
      <p className="text-sm text-slate-500 mb-4">
        Valores por defecto para nuevos presupuestos: margen de beneficio, gastos generales de estructura e
        IVA. No son datos legales — son decisiones de tu empresa. Cada presupuesto puede además ajustarlos
        individualmente si un proyecto concreto lo requiere.
      </p>

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      <div className="space-y-3">
        {parametros.map((p) => (
          <div key={p.id} className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3 mb-1">
              <label className="font-medium text-sm flex-1">{p.clave.replace(/_/g, " ")}</label>
              <input
                type="number"
                step="0.001"
                className="border rounded px-3 py-1.5 w-28 text-right"
                value={valores[p.id] ?? ""}
                onChange={(e) => setValores({ ...valores, [p.id]: e.target.value })}
              />
              <span className="text-sm text-slate-500">%</span>
              <button
                onClick={() => guardar(p)}
                disabled={guardandoId === p.id}
                className="bg-slate-900 text-white text-sm px-3 py-1.5 rounded disabled:opacity-50"
              >
                {guardandoId === p.id ? "Guardando..." : "Guardar"}
              </button>
            </div>
            {guardadoId === p.id && <p className="text-xs text-green-700">Guardado correctamente.</p>}
            {p.descripcion && <p className="text-xs text-slate-400">{p.descripcion}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
