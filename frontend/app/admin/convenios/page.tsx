"use client";

import { useEffect, useState } from "react";
import RequireAuth from "@/components/RequireAuth";
import { api, CategoriaProfesional, Convenio } from "@/lib/api";

export default function AdminConveniosPage() {
  return (
    <RequireAuth soloAdmin>
      <Contenido />
    </RequireAuth>
  );
}

const initialConvenio = {
  nombre: "",
  ambito: "",
  provincia: "",
  codigo_convenio: "",
  fuente: "",
  numero_pagas: "14",
  jornada_anual_horas: "1800",
  notas: "",
};

const initialCategoria = { convenio_id: "", grupo: "", nombre: "", grupo_cotizacion: "" };

const initialTabla = {
  categoria_id: "",
  anio: String(new Date().getFullYear()),
  salario_convenio_anual: "",
  salario_convenio_mensual: "",
  valor_quinquenio_o_trienio: "",
  plus_convenio_mensual: "0",
  vigente_desde: "",
};

function Contenido() {
  const [convenios, setConvenios] = useState<Convenio[]>([]);
  const [categorias, setCategorias] = useState<CategoriaProfesional[]>([]);
  const [formConvenio, setFormConvenio] = useState(initialConvenio);
  const [formCategoria, setFormCategoria] = useState(initialCategoria);
  const [formTabla, setFormTabla] = useState(initialTabla);
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    const lista = await api.convenios.listar();
    setConvenios(lista);
    const todas = await Promise.all(lista.map((c) => api.convenios.categorias(c.id)));
    setCategorias(todas.flat());
  }

  useEffect(() => {
    cargar().catch((e) => setError(String(e)));
  }, []);

  async function crearConvenio(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.admin.convenios.crear({
        ...formConvenio,
        numero_pagas: Number(formConvenio.numero_pagas) as unknown as number,
        jornada_anual_horas: formConvenio.jornada_anual_horas as unknown as string,
      });
      setFormConvenio(initialConvenio);
      await cargar();
    } catch (err) {
      setError(String(err));
    }
  }

  async function crearCategoria(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.admin.convenios.crearCategoria({
        convenio_id: Number(formCategoria.convenio_id) as unknown as number,
        grupo: formCategoria.grupo,
        nombre: formCategoria.nombre,
        grupo_cotizacion: Number(formCategoria.grupo_cotizacion) as unknown as number,
      });
      setFormCategoria(initialCategoria);
      await cargar();
    } catch (err) {
      setError(String(err));
    }
  }

  async function crearTabla(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.admin.convenios.crearTablaSalarial({
        categoria_id: Number(formTabla.categoria_id),
        anio: Number(formTabla.anio),
        salario_convenio_anual: formTabla.salario_convenio_anual,
        salario_convenio_mensual: formTabla.salario_convenio_mensual,
        valor_quinquenio_o_trienio: formTabla.valor_quinquenio_o_trienio || undefined,
        plus_convenio_mensual: formTabla.plus_convenio_mensual,
        vigente_desde: formTabla.vigente_desde,
      });
      setFormTabla(initialTabla);
      alert("Tabla salarial creada.");
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold mb-2">Convenios (administración)</h1>
        <p className="text-sm text-slate-500 mb-4">
          Alta de convenios, categorías profesionales y nuevas vigencias de tablas salariales.
        </p>
        {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}
      </div>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-medium mb-3">Nuevo convenio</h2>
        <form onSubmit={crearConvenio} className="grid sm:grid-cols-2 gap-3">
          <input required placeholder="Nombre" className="border rounded px-3 py-2 sm:col-span-2"
            value={formConvenio.nombre} onChange={(e) => setFormConvenio({ ...formConvenio, nombre: e.target.value })} />
          <input placeholder="Ámbito" className="border rounded px-3 py-2"
            value={formConvenio.ambito} onChange={(e) => setFormConvenio({ ...formConvenio, ambito: e.target.value })} />
          <input placeholder="Provincia" className="border rounded px-3 py-2"
            value={formConvenio.provincia} onChange={(e) => setFormConvenio({ ...formConvenio, provincia: e.target.value })} />
          <input placeholder="Código convenio" className="border rounded px-3 py-2"
            value={formConvenio.codigo_convenio} onChange={(e) => setFormConvenio({ ...formConvenio, codigo_convenio: e.target.value })} />
          <input placeholder="Fuente (BOE/BOCM...)" className="border rounded px-3 py-2"
            value={formConvenio.fuente} onChange={(e) => setFormConvenio({ ...formConvenio, fuente: e.target.value })} />
          <input type="number" placeholder="Nº pagas" className="border rounded px-3 py-2"
            value={formConvenio.numero_pagas} onChange={(e) => setFormConvenio({ ...formConvenio, numero_pagas: e.target.value })} />
          <input type="number" placeholder="Jornada anual (horas)" className="border rounded px-3 py-2"
            value={formConvenio.jornada_anual_horas} onChange={(e) => setFormConvenio({ ...formConvenio, jornada_anual_horas: e.target.value })} />
          <textarea placeholder="Notas / avisos de vigencia" className="border rounded px-3 py-2 sm:col-span-2"
            value={formConvenio.notas} onChange={(e) => setFormConvenio({ ...formConvenio, notas: e.target.value })} />
          <button className="sm:col-span-2 bg-slate-900 text-white rounded py-2">Crear convenio</button>
        </form>
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-medium mb-3">Nueva categoría profesional</h2>
        <form onSubmit={crearCategoria} className="grid sm:grid-cols-2 gap-3">
          <select required className="border rounded px-3 py-2 sm:col-span-2"
            value={formCategoria.convenio_id} onChange={(e) => setFormCategoria({ ...formCategoria, convenio_id: e.target.value })}>
            <option value="">Convenio...</option>
            {convenios.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <input required placeholder="Grupo (ej. 5)" className="border rounded px-3 py-2"
            value={formCategoria.grupo} onChange={(e) => setFormCategoria({ ...formCategoria, grupo: e.target.value })} />
          <input required placeholder="Nombre categoría" className="border rounded px-3 py-2"
            value={formCategoria.nombre} onChange={(e) => setFormCategoria({ ...formCategoria, nombre: e.target.value })} />
          <input required type="number" placeholder="Grupo cotización SS (1-11)" className="border rounded px-3 py-2"
            value={formCategoria.grupo_cotizacion} onChange={(e) => setFormCategoria({ ...formCategoria, grupo_cotizacion: e.target.value })} />
          <button className="sm:col-span-2 bg-slate-900 text-white rounded py-2">Crear categoría</button>
        </form>
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-medium mb-3">Nueva tabla salarial (vigencia)</h2>
        <form onSubmit={crearTabla} className="grid sm:grid-cols-2 gap-3">
          <select required className="border rounded px-3 py-2 sm:col-span-2"
            value={formTabla.categoria_id} onChange={(e) => setFormTabla({ ...formTabla, categoria_id: e.target.value })}>
            <option value="">Categoría...</option>
            {categorias.map((c) => <option key={c.id} value={c.id}>{c.grupo} — {c.nombre}</option>)}
          </select>
          <input required type="number" placeholder="Año" className="border rounded px-3 py-2"
            value={formTabla.anio} onChange={(e) => setFormTabla({ ...formTabla, anio: e.target.value })} />
          <input required type="date" className="border rounded px-3 py-2"
            value={formTabla.vigente_desde} onChange={(e) => setFormTabla({ ...formTabla, vigente_desde: e.target.value })} />
          <input required type="number" step="0.01" placeholder="Salario convenio anual (€)" className="border rounded px-3 py-2"
            value={formTabla.salario_convenio_anual} onChange={(e) => setFormTabla({ ...formTabla, salario_convenio_anual: e.target.value })} />
          <input required type="number" step="0.01" placeholder="Salario convenio mensual (€)" className="border rounded px-3 py-2"
            value={formTabla.salario_convenio_mensual} onChange={(e) => setFormTabla({ ...formTabla, salario_convenio_mensual: e.target.value })} />
          <input type="number" step="0.01" placeholder="Valor quinquenio/trienio (€, opcional)" className="border rounded px-3 py-2"
            value={formTabla.valor_quinquenio_o_trienio} onChange={(e) => setFormTabla({ ...formTabla, valor_quinquenio_o_trienio: e.target.value })} />
          <input type="number" step="0.01" placeholder="Plus convenio mensual (€)" className="border rounded px-3 py-2"
            value={formTabla.plus_convenio_mensual} onChange={(e) => setFormTabla({ ...formTabla, plus_convenio_mensual: e.target.value })} />
          <button className="sm:col-span-2 bg-slate-900 text-white rounded py-2">Crear tabla salarial</button>
        </form>
      </section>
    </div>
  );
}
