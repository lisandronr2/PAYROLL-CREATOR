"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, Empresa, Trabajador } from "@/lib/api";

export default function EditarTrabajadorPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [form, setForm] = useState<Partial<Trabajador> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [guardado, setGuardado] = useState(false);

  useEffect(() => {
    if (!id) return;
    Promise.all([api.trabajadores.obtener(id), api.empresas.listar()])
      .then(([t, emp]) => {
        setForm(t);
        setEmpresas(emp);
      })
      .catch((e) => setError(String(e)));
  }, [id]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    setError(null);
    setGuardado(false);
    setGuardando(true);
    try {
      const actualizado = await api.trabajadores.actualizar(id, {
        empresa_id: Number(form.empresa_id),
        nombre: form.nombre,
        apellidos: form.apellidos,
        nif: form.nif,
        tipo_documento: form.tipo_documento,
        numero_afiliacion_ss: form.numero_afiliacion_ss || null,
        fecha_nacimiento: form.fecha_nacimiento || null,
        fecha_alta: form.fecha_alta,
        fecha_baja: form.fecha_baja || null,
        situacion_familiar: form.situacion_familiar,
        hijos_menores_25: Number(form.hijos_menores_25 ?? 0),
        grado_discapacidad: Number(form.grado_discapacidad ?? 0),
        iban: form.iban || null,
        activo: form.activo,
      });
      setForm(actualizado);
      setGuardado(true);
    } catch (err) {
      setError(String(err));
    } finally {
      setGuardando(false);
    }
  }

  if (error && !form) return <p className="text-red-600 text-sm">{error}</p>;
  if (!form) return <p className="text-sm text-slate-500">Cargando...</p>;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <button onClick={() => router.push("/trabajadores")} className="text-sm text-slate-500 hover:underline">
          ← Volver a trabajadores
        </button>
      </div>

      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 space-y-3">
        <h1 className="text-xl font-semibold mb-2">Editar trabajador</h1>

        <select
          required
          className="border rounded px-3 py-2 w-full"
          value={form.empresa_id ?? ""}
          onChange={(e) => setForm({ ...form, empresa_id: Number(e.target.value) })}
        >
          <option value="">Empresa...</option>
          {empresas.map((e) => (
            <option key={e.id} value={e.id}>
              {e.razon_social}
            </option>
          ))}
        </select>

        <div className="grid sm:grid-cols-2 gap-3">
          <input
            required
            placeholder="Nombre"
            className="border rounded px-3 py-2"
            value={form.nombre ?? ""}
            onChange={(e) => setForm({ ...form, nombre: e.target.value })}
          />
          <input
            required
            placeholder="Apellidos"
            className="border rounded px-3 py-2"
            value={form.apellidos ?? ""}
            onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
          />
        </div>

        <div className="flex gap-2">
          <select
            className="border rounded px-3 py-2 w-28 shrink-0"
            value={form.tipo_documento ?? "DNI"}
            onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })}
          >
            <option value="DNI">DNI</option>
            <option value="NIE">NIE</option>
          </select>
          <input
            required
            placeholder={form.tipo_documento === "NIE" ? "NIE (ej. X1234567L)" : "DNI (ej. 12345678A)"}
            className="border rounded px-3 py-2 flex-1"
            value={form.nif ?? ""}
            onChange={(e) => setForm({ ...form, nif: e.target.value })}
          />
        </div>

        <label className="text-xs text-slate-500 flex flex-col gap-1">
          Nº afiliación SS
          <input
            className="border rounded px-3 py-2"
            value={form.numero_afiliacion_ss ?? ""}
            onChange={(e) => setForm({ ...form, numero_afiliacion_ss: e.target.value })}
          />
        </label>

        <div className="grid sm:grid-cols-2 gap-3">
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Fecha de nacimiento
            <input
              type="date"
              className="border rounded px-3 py-2"
              value={form.fecha_nacimiento ?? ""}
              onChange={(e) => setForm({ ...form, fecha_nacimiento: e.target.value })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Fecha de alta
            <input
              required
              type="date"
              className="border rounded px-3 py-2"
              value={form.fecha_alta ?? ""}
              onChange={(e) => setForm({ ...form, fecha_alta: e.target.value })}
            />
          </label>
        </div>

        <label className="text-xs text-slate-500 flex flex-col gap-1">
          Fecha de baja (dejar vacío si sigue de alta)
          <input
            type="date"
            className="border rounded px-3 py-2"
            value={form.fecha_baja ?? ""}
            onChange={(e) => setForm({ ...form, fecha_baja: e.target.value })}
          />
        </label>

        <div className="grid sm:grid-cols-3 gap-3">
          <select
            className="border rounded px-3 py-2"
            value={form.situacion_familiar ?? "soltero"}
            onChange={(e) => setForm({ ...form, situacion_familiar: e.target.value })}
          >
            <option value="soltero">Soltero/a</option>
            <option value="casado">Casado/a</option>
          </select>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Hijos menores de 25
            <input
              type="number"
              min={0}
              className="border rounded px-3 py-2"
              value={form.hijos_menores_25 ?? 0}
              onChange={(e) => setForm({ ...form, hijos_menores_25: Number(e.target.value) })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Grado discapacidad (%)
            <input
              type="number"
              min={0}
              className="border rounded px-3 py-2"
              value={form.grado_discapacidad ?? 0}
              onChange={(e) => setForm({ ...form, grado_discapacidad: Number(e.target.value) })}
            />
          </label>
        </div>

        <label className="text-xs text-slate-500 flex flex-col gap-1">
          IBAN
          <input
            className="border rounded px-3 py-2"
            value={form.iban ?? ""}
            onChange={(e) => setForm({ ...form, iban: e.target.value })}
          />
        </label>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.activo ?? true}
            onChange={(e) => setForm({ ...form, activo: e.target.checked })}
          />
          Activo
        </label>

        {error && <p className="text-red-600 text-sm">{error}</p>}
        {guardado && <p className="text-green-700 text-sm">Guardado correctamente.</p>}

        <button disabled={guardando} className="bg-slate-900 text-white rounded py-2 px-4 disabled:opacity-50">
          {guardando ? "Guardando..." : "Guardar cambios"}
        </button>
      </form>
    </div>
  );
}
