"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  api,
  CategoriaProfesional,
  Contrato,
  Convenio,
  Empresa,
  Trabajador,
} from "@/lib/api";

const TIPO_CONTRATO_LABEL: Record<string, string> = {
  indefinido: "Indefinido",
  temporal: "Temporal",
  formacion: "Formación",
  practicas: "Prácticas",
};

function fmtFecha(f?: string | null) {
  if (!f) return "-";
  const [anio, mes, dia] = f.split("-");
  return `${dia}-${mes}-${anio}`;
}

export default function ContratoDetallePage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [contrato, setContrato] = useState<Contrato | null>(null);
  const [trabajador, setTrabajador] = useState<Trabajador | null>(null);
  const [empresa, setEmpresa] = useState<Empresa | null>(null);
  const [convenio, setConvenio] = useState<Convenio | null>(null);
  const [categoria, setCategoria] = useState<CategoriaProfesional | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const c = await api.contratos.obtener(id);
        setContrato(c);
        const [t, convenios] = await Promise.all([
          api.trabajadores.obtener(c.trabajador_id),
          api.convenios.listar(),
        ]);
        setTrabajador(t);
        const conv = convenios.find((x) => x.id === c.convenio_id) ?? null;
        setConvenio(conv);
        const [e, categorias] = await Promise.all([
          api.empresas.obtener(t.empresa_id),
          conv ? api.convenios.categorias(conv.id) : Promise.resolve([]),
        ]);
        setEmpresa(e);
        setCategoria(categorias.find((cat) => cat.id === c.categoria_id) ?? null);
      } catch (err) {
        setError(String(err));
      }
    })();
  }, [id]);

  if (error) return <p className="text-red-600 text-sm">{error}</p>;
  if (!contrato || !trabajador) return <p className="text-sm text-slate-500">Cargando...</p>;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-4 print:hidden">
        <button onClick={() => router.push("/contratos")} className="text-sm text-slate-500 hover:underline">
          ← Volver a contratos
        </button>
        <button
          onClick={() => window.print()}
          className="bg-slate-900 text-white text-sm px-3 py-1.5 rounded"
        >
          Imprimir
        </button>
      </div>

      <div className="bg-white border rounded-lg p-6 space-y-4 print:border-none print:shadow-none">
        <h1 className="text-xl font-semibold">Contrato de trabajo</h1>

        <section>
          <h2 className="text-sm font-semibold text-slate-500 uppercase mb-1">Empresa</h2>
          <div className="text-sm grid grid-cols-2 gap-x-4 gap-y-1">
            <div>Razón social: {empresa?.razon_social ?? "-"}</div>
            <div>CIF: {empresa?.cif ?? "-"}</div>
            <div>Dirección: {empresa?.direccion ?? "-"}</div>
            <div>Población: {empresa?.poblacion ?? "-"}</div>
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold text-slate-500 uppercase mb-1">Trabajador</h2>
          <div className="text-sm grid grid-cols-2 gap-x-4 gap-y-1">
            <div>Nombre: {trabajador.nombre} {trabajador.apellidos}</div>
            <div>NIF: {trabajador.nif}</div>
            <div>Nº afiliación SS: {trabajador.numero_afiliacion_ss ?? "-"}</div>
            <div>Fecha de alta: {fmtFecha(trabajador.fecha_alta)}</div>
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold text-slate-500 uppercase mb-1">Datos del contrato</h2>
          <div className="text-sm grid grid-cols-2 gap-x-4 gap-y-1">
            <div>Convenio: {convenio?.nombre ?? "-"}</div>
            <div>Categoría: {categoria ? `${categoria.grupo} — ${categoria.nombre}` : "-"}</div>
            <div>Tipo de contrato: {TIPO_CONTRATO_LABEL[contrato.tipo_contrato] ?? contrato.tipo_contrato}</div>
            <div>Jornada: {contrato.jornada_porcentaje}%</div>
            <div>Puesto de trabajo: {contrato.puesto_trabajo ?? "-"}</div>
            <div>Sección: {contrato.seccion ?? "-"}</div>
            <div>Fecha de inicio: {fmtFecha(contrato.fecha_inicio)}</div>
            <div>Fecha de fin: {fmtFecha(contrato.fecha_fin)}</div>
            <div>Antigüedad: {fmtFecha(contrato.fecha_antiguedad ?? contrato.fecha_inicio)}</div>
            <div>Pagas extra prorrateadas: {contrato.pagas_extra_prorrateadas ? "Sí" : "No"}</div>
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold text-slate-500 uppercase mb-1">Retribución</h2>
          <div className="text-sm grid grid-cols-2 gap-x-4 gap-y-1">
            <div>
              Salario pactado:{" "}
              {contrato.salario_pactado_mensual
                ? `${Number(contrato.salario_pactado_mensual).toFixed(2)} € (sustituye al de convenio)`
                : "Según tabla salarial del convenio"}
            </div>
            <div>Mejora voluntaria mensual: {Number(contrato.complemento_mensual).toFixed(2)} €</div>
          </div>
        </section>

        <p className="text-xs text-slate-400 pt-4 border-t">
          Documento generado por PAYROLL CREATOR. Los datos aquí mostrados reflejan lo dado de alta en el
          sistema; verifica que coincidan con el contrato firmado en papel antes de usarlo como referencia legal.
        </p>
      </div>

      <div className="print:hidden mt-4">
        <Link href="/nominas/generar" className="text-sm text-blue-600 hover:underline">
          Generar nómina para este contrato →
        </Link>
      </div>
    </div>
  );
}
