"use client";

import { useEffect, useState } from "react";
import RequireAuth from "@/components/RequireAuth";
import { api, ParametroLegal } from "@/lib/api";

const initialForm = {
  clave: "",
  valor: "",
  grupo_cotizacion: "",
  vigente_desde: "",
  referencia_legal: "",
};

export default function ParametrosLegalesPage() {
  return (
    <RequireAuth soloAdmin>
      <Contenido />
    </RequireAuth>
  );
}

function Contenido() {
  const [parametros, setParametros] = useState<ParametroLegal[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function cargar() {
    setParametros(await api.admin.parametrosLegales.listar());
  }

  useEffect(() => {
    cargar().catch((e) => setError(String(e)));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await api.admin.parametrosLegales.crear({
        clave: form.clave,
        valor: form.valor as unknown as string,
        grupo_cotizacion: form.grupo_cotizacion ? (Number(form.grupo_cotizacion) as unknown as number) : undefined,
        vigente_desde: form.vigente_desde as unknown as string,
        referencia_legal: form.referencia_legal || undefined,
      });
      setForm(initialForm);
      await cargar();
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  async function actualizarValor(p: ParametroLegal) {
    const nuevoValor = window.prompt(`Nuevo valor para "${p.clave}"`, p.valor);
    if (nuevoValor === null) return;
    await api.admin.parametrosLegales.actualizar(p.id, { valor: nuevoValor as unknown as string });
    await cargar();
  }

  async function eliminar(p: ParametroLegal) {
    if (!window.confirm(`¿Eliminar el parámetro "${p.clave}" (vigente desde ${p.vigente_desde})?`)) return;
    await api.admin.parametrosLegales.eliminar(p.id);
    await cargar();
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">Parámetros legales</h1>
      <p className="text-sm text-slate-500 mb-4">
        SMI, tipos de cotización, topes, recargos, etc. Cada clave puede tener varias vigencias en el
        tiempo. Verifica los valores oficiales antes de editar — ver docs/LEGAL_DISCLAIMER.md.
      </p>

      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 mb-6 grid sm:grid-cols-3 gap-3">
        <input
          required
          placeholder="Clave (ej. tipo_cc_empresa)"
          className="border rounded px-3 py-2"
          value={form.clave}
          onChange={(e) => setForm({ ...form, clave: e.target.value })}
        />
        <input
          required
          type="number"
          step="0.0001"
          placeholder="Valor"
          className="border rounded px-3 py-2"
          value={form.valor}
          onChange={(e) => setForm({ ...form, valor: e.target.value })}
        />
        <input
          type="number"
          placeholder="Grupo cotización (opcional)"
          className="border rounded px-3 py-2"
          value={form.grupo_cotizacion}
          onChange={(e) => setForm({ ...form, grupo_cotizacion: e.target.value })}
        />
        <input
          required
          type="date"
          className="border rounded px-3 py-2"
          value={form.vigente_desde}
          onChange={(e) => setForm({ ...form, vigente_desde: e.target.value })}
        />
        <input
          placeholder="Referencia legal"
          className="border rounded px-3 py-2 sm:col-span-2"
          value={form.referencia_legal}
          onChange={(e) => setForm({ ...form, referencia_legal: e.target.value })}
        />
        <button disabled={cargando} className="sm:col-span-3 bg-slate-900 text-white rounded py-2 disabled:opacity-50">
          {cargando ? "Guardando..." : "Añadir parámetro / nueva vigencia"}
        </button>
      </form>

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2">Clave</th>
            <th className="text-left p-2">Valor</th>
            <th className="text-left p-2">Grupo</th>
            <th className="text-left p-2">Vigente desde</th>
            <th className="text-left p-2">Vigente hasta</th>
            <th className="text-right p-2">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {parametros.map((p) => (
            <tr key={p.id} className="border-t">
              <td className="p-2">{p.clave}</td>
              <td className="p-2">{p.valor}</td>
              <td className="p-2">{p.grupo_cotizacion ?? "-"}</td>
              <td className="p-2">{p.vigente_desde}</td>
              <td className="p-2">{p.vigente_hasta ?? "-"}</td>
              <td className="p-2 text-right space-x-2">
                <button onClick={() => actualizarValor(p)} className="text-blue-600 underline">
                  Editar
                </button>
                <button onClick={() => eliminar(p)} className="text-red-600 underline">
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
