"use client";

import { useEffect, useState } from "react";
import { api, Empresa } from "@/lib/api";

const initialForm = {
  razon_social: "",
  cif: "",
  direccion: "",
  cnae: "",
  codigo_cuenta_cotizacion: "",
  tipo_at_ep_pct: "1.50",
};

export default function EmpresasPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function cargar() {
    setEmpresas(await api.empresas.listar());
  }

  useEffect(() => {
    cargar().catch((e) => setError(String(e)));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await api.empresas.crear({ ...form, tipo_at_ep_pct: form.tipo_at_ep_pct as unknown as string });
      setForm(initialForm);
      await cargar();
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Empresas</h1>

      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 mb-6 grid sm:grid-cols-2 gap-3">
        <input
          required
          placeholder="Razón social"
          className="border rounded px-3 py-2"
          value={form.razon_social}
          onChange={(e) => setForm({ ...form, razon_social: e.target.value })}
        />
        <input
          required
          placeholder="CIF"
          className="border rounded px-3 py-2"
          value={form.cif}
          onChange={(e) => setForm({ ...form, cif: e.target.value })}
        />
        <input
          placeholder="Dirección"
          className="border rounded px-3 py-2 sm:col-span-2"
          value={form.direccion}
          onChange={(e) => setForm({ ...form, direccion: e.target.value })}
        />
        <input
          placeholder="CNAE"
          className="border rounded px-3 py-2"
          value={form.cnae}
          onChange={(e) => setForm({ ...form, cnae: e.target.value })}
        />
        <input
          placeholder="Código Cuenta Cotización (CCC)"
          className="border rounded px-3 py-2"
          value={form.codigo_cuenta_cotizacion}
          onChange={(e) => setForm({ ...form, codigo_cuenta_cotizacion: e.target.value })}
        />
        <label className="text-xs text-slate-500 flex flex-col gap-1">
          Tipo AT/EP (contingencias profesionales, % a cargo de la empresa)
          <input
            type="number"
            step="0.001"
            className="border rounded px-3 py-2"
            value={form.tipo_at_ep_pct}
            onChange={(e) => setForm({ ...form, tipo_at_ep_pct: e.target.value })}
          />
        </label>
        <button
          disabled={cargando}
          className="sm:col-span-2 bg-slate-900 text-white rounded py-2 disabled:opacity-50"
        >
          {cargando ? "Guardando..." : "Crear empresa"}
        </button>
      </form>

      <p className="text-xs text-slate-500 mb-4">
        El tipo AT/EP depende del CNAE/epígrafe de la empresa (tarifa de primas, DA 61ª LGSS) — verifica
        el valor exacto aplicable antes de usarlo en una nómina real.
      </p>

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2">Razón social</th>
            <th className="text-left p-2">CIF</th>
            <th className="text-left p-2">CNAE</th>
            <th className="text-left p-2">CCC</th>
            <th className="text-left p-2">AT/EP %</th>
          </tr>
        </thead>
        <tbody>
          {empresas.map((e) => (
            <tr key={e.id} className="border-t">
              <td className="p-2">{e.razon_social}</td>
              <td className="p-2">{e.cif}</td>
              <td className="p-2">{e.cnae}</td>
              <td className="p-2">{e.codigo_cuenta_cotizacion}</td>
              <td className="p-2">{e.tipo_at_ep_pct}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
