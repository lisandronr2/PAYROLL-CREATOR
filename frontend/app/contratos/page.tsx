"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CategoriaProfesional, Contrato, Convenio, Trabajador } from "@/lib/api";

const initialForm = {
  trabajador_id: "",
  convenio_id: "",
  categoria_id: "",
  tipo_contrato: "indefinido",
  jornada_porcentaje: "100",
  fecha_inicio: "",
  puesto_trabajo: "",
  seccion: "",
  salario_pactado_mensual: "",
  complemento_mensual: "0",
  pagas_extra_prorrateadas: false,
};

export default function ContratosPage() {
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([]);
  const [convenios, setConvenios] = useState<Convenio[]>([]);
  const [categorias, setCategorias] = useState<CategoriaProfesional[]>([]);
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [analizando, setAnalizando] = useState(false);
  const [avisoPdf, setAvisoPdf] = useState<string | null>(null);

  async function cargar() {
    const [trab, conv, cont] = await Promise.all([
      api.trabajadores.listar(),
      api.convenios.listar(),
      api.contratos.listar(),
    ]);
    setTrabajadores(trab);
    setConvenios(conv);
    setContratos(cont);
  }

  useEffect(() => {
    cargar().catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!form.convenio_id) {
      setCategorias([]);
      return;
    }
    api.convenios.categorias(Number(form.convenio_id)).then(setCategorias);
  }, [form.convenio_id]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await api.contratos.crear({
        ...form,
        trabajador_id: Number(form.trabajador_id),
        convenio_id: Number(form.convenio_id),
        categoria_id: Number(form.categoria_id),
        jornada_porcentaje: form.jornada_porcentaje as unknown as string,
        salario_pactado_mensual: form.salario_pactado_mensual
          ? (form.salario_pactado_mensual as unknown as string)
          : null,
      });
      setForm(initialForm);
      setAvisoPdf(null);
      await cargar();
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  async function onSubirPdf(e: React.ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0];
    e.target.value = "";
    if (!archivo) return;
    setError(null);
    setAvisoPdf(null);
    setAnalizando(true);
    try {
      const detectado = await api.contratos.extraerPdf(archivo);
      setForm((prev) => ({
        ...prev,
        fecha_inicio: detectado.fecha_inicio ?? prev.fecha_inicio,
        tipo_contrato: detectado.tipo_contrato ?? prev.tipo_contrato,
        jornada_porcentaje: detectado.jornada_porcentaje ?? prev.jornada_porcentaje,
        salario_pactado_mensual: detectado.salario_pactado_mensual ?? prev.salario_pactado_mensual,
        puesto_trabajo: detectado.puesto_trabajo ?? prev.puesto_trabajo,
      }));
      const camposDetectados = [
        detectado.fecha_inicio && "fecha de inicio",
        detectado.tipo_contrato && "tipo de contrato",
        detectado.jornada_porcentaje && "jornada",
        detectado.salario_pactado_mensual && "salario",
        detectado.puesto_trabajo && "puesto de trabajo",
      ].filter(Boolean);
      setAvisoPdf(
        camposDetectados.length
          ? `Detectado automáticamente: ${camposDetectados.join(", ")}. Revisa los datos antes de guardar — la lectura del PDF es orientativa.`
          : "No se ha podido detectar ningún dato con confianza en ese PDF. Rellena el formulario manualmente."
      );
    } catch (err) {
      setError(String(err));
    } finally {
      setAnalizando(false);
    }
  }

  function nombreTrabajador(id: number) {
    const t = trabajadores.find((x) => x.id === id);
    return t ? `${t.nombre} ${t.apellidos}` : id;
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Contratos</h1>

      <div className="bg-white border rounded-lg p-4 mb-4 flex items-center gap-3">
        <label className="text-sm bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded cursor-pointer">
          {analizando ? "Analizando PDF..." : "Subir contrato en PDF"}
          <input
            type="file"
            accept="application/pdf"
            className="hidden"
            disabled={analizando}
            onChange={onSubirPdf}
          />
        </label>
        <p className="text-xs text-slate-500">
          Sube un contrato ya firmado y se intentarán detectar automáticamente la fecha de inicio, el
          tipo de contrato, la jornada, el salario y el puesto para rellenar el formulario de abajo.
        </p>
      </div>
      {avisoPdf && (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 mb-4">{avisoPdf}</p>
      )}

      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 mb-6 grid sm:grid-cols-2 gap-3">
        <select
          required
          className="border rounded px-3 py-2"
          value={form.trabajador_id}
          onChange={(e) => setForm({ ...form, trabajador_id: e.target.value })}
        >
          <option value="">Trabajador...</option>
          {trabajadores.map((t) => (
            <option key={t.id} value={t.id}>
              {t.nombre} {t.apellidos}
            </option>
          ))}
        </select>
        <select
          required
          className="border rounded px-3 py-2"
          value={form.convenio_id}
          onChange={(e) => setForm({ ...form, convenio_id: e.target.value, categoria_id: "" })}
        >
          <option value="">Convenio...</option>
          {convenios.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
        <select
          required
          className="border rounded px-3 py-2"
          value={form.categoria_id}
          onChange={(e) => setForm({ ...form, categoria_id: e.target.value })}
        >
          <option value="">Categoría...</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>
              {c.grupo} — {c.nombre}
            </option>
          ))}
        </select>
        <select
          className="border rounded px-3 py-2"
          value={form.tipo_contrato}
          onChange={(e) => setForm({ ...form, tipo_contrato: e.target.value })}
        >
          <option value="indefinido">Indefinido</option>
          <option value="temporal">Temporal</option>
          <option value="formacion">Formación</option>
          <option value="practicas">Prácticas</option>
        </select>
        <input
          type="number"
          min={1}
          max={100}
          placeholder="Jornada %"
          className="border rounded px-3 py-2"
          value={form.jornada_porcentaje}
          onChange={(e) => setForm({ ...form, jornada_porcentaje: e.target.value })}
        />
        <input
          required
          type="date"
          className="border rounded px-3 py-2"
          value={form.fecha_inicio}
          onChange={(e) => setForm({ ...form, fecha_inicio: e.target.value })}
        />
        <input
          placeholder="Puesto de trabajo (ej. Instalador)"
          className="border rounded px-3 py-2"
          value={form.puesto_trabajo}
          onChange={(e) => setForm({ ...form, puesto_trabajo: e.target.value })}
        />
        <input
          placeholder="Sección"
          className="border rounded px-3 py-2"
          value={form.seccion}
          onChange={(e) => setForm({ ...form, seccion: e.target.value })}
        />
        <label className="text-xs text-slate-500 flex flex-col gap-1 sm:col-span-2">
          Salario pactado mensual (€, opcional — solo si sustituye al de la tabla de convenio)
          <input
            type="number"
            step="0.01"
            className="border rounded px-3 py-2"
            value={form.salario_pactado_mensual}
            onChange={(e) => setForm({ ...form, salario_pactado_mensual: e.target.value })}
          />
        </label>
        <label className="text-xs text-slate-500 flex flex-col gap-1 sm:col-span-2">
          Mejora voluntaria mensual (€, adicional al salario de convenio)
          <input
            type="number"
            step="0.01"
            className="border rounded px-3 py-2"
            value={form.complemento_mensual}
            onChange={(e) => setForm({ ...form, complemento_mensual: e.target.value })}
          />
        </label>
        <label className="flex items-center gap-2 text-sm sm:col-span-2">
          <input
            type="checkbox"
            checked={form.pagas_extra_prorrateadas}
            onChange={(e) => setForm({ ...form, pagas_extra_prorrateadas: e.target.checked })}
          />
          Pagas extra prorrateadas mensualmente
        </label>
        <button
          disabled={cargando}
          className="sm:col-span-2 bg-slate-900 text-white rounded py-2 disabled:opacity-50"
        >
          {cargando ? "Guardando..." : "Crear contrato"}
        </button>
      </form>

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2">Trabajador</th>
            <th className="text-left p-2">Puesto</th>
            <th className="text-left p-2">Tipo</th>
            <th className="text-left p-2">Jornada</th>
            <th className="text-left p-2">Inicio</th>
            <th className="text-right p-2"></th>
          </tr>
        </thead>
        <tbody>
          {contratos.map((c) => (
            <tr key={c.id} className="border-t">
              <td className="p-2">{nombreTrabajador(c.trabajador_id)}</td>
              <td className="p-2">{c.puesto_trabajo}</td>
              <td className="p-2">{c.tipo_contrato}</td>
              <td className="p-2">{c.jornada_porcentaje}%</td>
              <td className="p-2">{c.fecha_inicio}</td>
              <td className="p-2 text-right">
                <Link href={`/contratos/${c.id}`} className="text-blue-600 underline">
                  Ver / imprimir
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
