"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Empresa, Trabajador } from "@/lib/api";

const initialForm = {
  empresa_id: "",
  nombre: "",
  apellidos: "",
  nif: "",
  tipo_documento: "DNI",
  numero_afiliacion_ss: "",
  fecha_alta: "",
  situacion_familiar: "soltero",
  hijos_menores_25: "0",
  grado_discapacidad: "0",
};

export default function TrabajadoresPage() {
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function cargar() {
    const [emp, trab] = await Promise.all([api.empresas.listar(), api.trabajadores.listar()]);
    setEmpresas(emp);
    setTrabajadores(trab);
  }

  useEffect(() => {
    cargar().catch((e) => setError(String(e)));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await api.trabajadores.crear({
        ...form,
        empresa_id: Number(form.empresa_id),
        hijos_menores_25: Number(form.hijos_menores_25),
        grado_discapacidad: Number(form.grado_discapacidad),
      });
      setForm(initialForm);
      await cargar();
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  function nombreEmpresa(id: number) {
    return empresas.find((e) => e.id === id)?.razon_social ?? id;
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Trabajadores</h1>

      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 mb-6 grid sm:grid-cols-2 gap-3">
        <select
          required
          className="border rounded px-3 py-2"
          value={form.empresa_id}
          onChange={(e) => setForm({ ...form, empresa_id: e.target.value })}
        >
          <option value="">Empresa...</option>
          {empresas.map((e) => (
            <option key={e.id} value={e.id}>
              {e.razon_social}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          <select
            className="border rounded px-3 py-2 w-28 shrink-0"
            value={form.tipo_documento}
            onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })}
          >
            <option value="DNI">DNI</option>
            <option value="NIE">NIE</option>
          </select>
          <input
            required
            placeholder={form.tipo_documento === "NIE" ? "NIE (ej. X1234567L)" : "DNI (ej. 12345678A)"}
            className="border rounded px-3 py-2 flex-1"
            value={form.nif}
            onChange={(e) => setForm({ ...form, nif: e.target.value })}
          />
        </div>
        <input
          required
          placeholder="Nombre"
          className="border rounded px-3 py-2"
          value={form.nombre}
          onChange={(e) => setForm({ ...form, nombre: e.target.value })}
        />
        <input
          required
          placeholder="Apellidos"
          className="border rounded px-3 py-2"
          value={form.apellidos}
          onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
        />
        <input
          placeholder="Nº afiliación SS"
          className="border rounded px-3 py-2"
          value={form.numero_afiliacion_ss}
          onChange={(e) => setForm({ ...form, numero_afiliacion_ss: e.target.value })}
        />
        <input
          required
          type="date"
          className="border rounded px-3 py-2"
          value={form.fecha_alta}
          onChange={(e) => setForm({ ...form, fecha_alta: e.target.value })}
        />
        <select
          className="border rounded px-3 py-2"
          value={form.situacion_familiar}
          onChange={(e) => setForm({ ...form, situacion_familiar: e.target.value })}
        >
          <option value="soltero">Soltero/a</option>
          <option value="casado">Casado/a</option>
        </select>
        <input
          type="number"
          min={0}
          placeholder="Hijos menores de 25"
          className="border rounded px-3 py-2"
          value={form.hijos_menores_25}
          onChange={(e) => setForm({ ...form, hijos_menores_25: e.target.value })}
        />
        <input
          type="number"
          min={0}
          placeholder="Grado discapacidad (%)"
          className="border rounded px-3 py-2"
          value={form.grado_discapacidad}
          onChange={(e) => setForm({ ...form, grado_discapacidad: e.target.value })}
        />
        <button
          disabled={cargando}
          className="sm:col-span-2 bg-slate-900 text-white rounded py-2 disabled:opacity-50"
        >
          {cargando ? "Guardando..." : "Crear trabajador"}
        </button>
      </form>

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2">Nombre</th>
            <th className="text-left p-2">Tipo</th>
            <th className="text-left p-2">NIF</th>
            <th className="text-left p-2">Empresa</th>
            <th className="text-left p-2">Alta</th>
            <th className="text-right p-2"></th>
          </tr>
        </thead>
        <tbody>
          {trabajadores.map((t) => (
            <tr key={t.id} className="border-t">
              <td className="p-2">
                {t.nombre} {t.apellidos}
              </td>
              <td className="p-2">{t.tipo_documento}</td>
              <td className="p-2">{t.nif}</td>
              <td className="p-2">{nombreEmpresa(t.empresa_id)}</td>
              <td className="p-2">{t.fecha_alta}</td>
              <td className="p-2 text-right">
                <Link href={`/trabajadores/${t.id}`} className="text-blue-600 underline">
                  Editar
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
