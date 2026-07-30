"use client";

import { useEffect, useState } from "react";
import { api, Convenio, ConvenioDietaRef, ParametroLegal } from "@/lib/api";

function valorDe(parametros: ParametroLegal[], clave: string, grupo?: number | null): string | null {
  const p = parametros.find(
    (x) => x.clave === clave && (grupo == null ? x.grupo_cotizacion == null : x.grupo_cotizacion === grupo)
  );
  return p ? p.valor : null;
}

function fmtPct(valor: string | null): string {
  return valor != null ? `${Number(valor).toFixed(2)}%` : "-";
}

function fmtEur(valor: string | null): string {
  return valor != null ? `${Number(valor).toFixed(2)} €` : "-";
}

export default function ParametrosPage() {
  const [parametros, setParametros] = useState<ParametroLegal[]>([]);
  const [convenios, setConvenios] = useState<Convenio[]>([]);
  const [convenioId, setConvenioId] = useState<string>("");
  const [dietas, setDietas] = useState<ConvenioDietaRef[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cargandoDietas, setCargandoDietas] = useState(false);

  useEffect(() => {
    Promise.all([api.referencia.parametrosLegales(), api.convenios.listar()])
      .then(([p, c]) => {
        setParametros(p);
        setConvenios(c);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!convenioId) {
      setDietas([]);
      return;
    }
    setCargandoDietas(true);
    api.referencia
      .dietasConvenio(Number(convenioId))
      .then(setDietas)
      .catch((e) => setError(String(e)))
      .finally(() => setCargandoDietas(false));
  }, [convenioId]);

  const gruposMinimo = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    .map((g) => ({ grupo: g, valor: valorDe(parametros, "tope_min_cotizacion", g) }))
    .filter((x) => x.valor != null);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Parámetros aplicados en las nóminas</h1>
        <p className="text-sm text-slate-500 mt-1">
          Referencia de solo lectura de los valores vigentes que el motor usa al calcular una nómina.
          Para editarlos, un administrador puede hacerlo desde Admin → Parámetros legales / Convenios.
        </p>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-medium mb-3">Salario mínimo y topes de cotización</h2>
        <div className="grid sm:grid-cols-2 gap-2 text-sm mb-3">
          <div>SMI mensual: <strong>{fmtEur(valorDe(parametros, "smi_mensual"))}</strong></div>
          <div>Tope máximo de cotización: <strong>{fmtEur(valorDe(parametros, "tope_max_cotizacion"))}</strong></div>
        </div>
        {gruposMinimo.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left p-1.5">Grupo de cotización</th>
                <th className="text-right p-1.5">Base mínima mensual</th>
              </tr>
            </thead>
            <tbody>
              {gruposMinimo.map((g) => (
                <tr key={g.grupo} className="border-t">
                  <td className="p-1.5">{g.grupo}</td>
                  <td className="p-1.5 text-right">{fmtEur(g.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-medium mb-3">Tipos de cotización a la Seguridad Social</h2>
        <table className="w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-1.5">Concepto</th>
              <th className="text-right p-1.5">Empresa</th>
              <th className="text-right p-1.5">Trabajador</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t">
              <td className="p-1.5">Contingencias comunes</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_cc_empresa"))}</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_cc_trabajador"))}</td>
            </tr>
            <tr className="border-t">
              <td className="p-1.5">Desempleo (contrato indefinido)</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_desempleo_indefinido_empresa"))}</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_desempleo_indefinido_trabajador"))}</td>
            </tr>
            <tr className="border-t">
              <td className="p-1.5">Desempleo (contrato temporal)</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_desempleo_temporal_empresa"))}</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_desempleo_temporal_trabajador"))}</td>
            </tr>
            <tr className="border-t">
              <td className="p-1.5">Formación profesional</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_fp_empresa"))}</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_fp_trabajador"))}</td>
            </tr>
            <tr className="border-t">
              <td className="p-1.5">MEI (Mecanismo de Equidad Intergeneracional)</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_mei_empresa"))}</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_mei_trabajador"))}</td>
            </tr>
            <tr className="border-t">
              <td className="p-1.5">FOGASA</td>
              <td className="p-1.5 text-right">{fmtPct(valorDe(parametros, "tipo_fogasa_empresa"))}</td>
              <td className="p-1.5 text-right">-</td>
            </tr>
          </tbody>
        </table>
        <p className="text-xs text-slate-400 mt-2">
          Las contingencias profesionales (AT y EP) no aparecen aquí porque dependen del CNAE de cada
          empresa — se configuran en la ficha de cada empresa.
        </p>
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-medium mb-3">Horas extra y nocturnidad</h2>
        <div className="grid sm:grid-cols-3 gap-2 text-sm">
          <div>Recargo hora extra: <strong>{fmtPct(valorDe(parametros, "recargo_hora_extra_pct"))}</strong></div>
          <div>Recargo hora extra nocturna: <strong>{fmtPct(valorDe(parametros, "recargo_hora_extra_nocturna_pct"))}</strong></div>
          <div>Plus de nocturnidad: <strong>{fmtPct(valorDe(parametros, "plus_nocturnidad_pct"))}</strong></div>
        </div>
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-medium mb-3">Dietas por convenio</h2>
        <select
          className="border rounded px-3 py-2 mb-3 w-full sm:w-auto"
          value={convenioId}
          onChange={(e) => setConvenioId(e.target.value)}
        >
          <option value="">Elige un convenio...</option>
          {convenios.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>

        {cargandoDietas && <p className="text-sm text-slate-500">Cargando...</p>}

        {!cargandoDietas && convenioId && dietas.length === 0 && (
          <p className="text-sm text-slate-500">Este convenio no tiene dietas configuradas.</p>
        )}

        {dietas.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left p-1.5">Concepto</th>
                <th className="text-right p-1.5">Importe</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t">
                <td className="p-1.5">Media dieta</td>
                <td className="p-1.5 text-right">{fmtEur(dietas[0].media_dieta)}</td>
              </tr>
              <tr className="border-t">
                <td className="p-1.5">Dieta completa, viaje &lt; 7 días</td>
                <td className="p-1.5 text-right">{fmtEur(dietas[0].dieta_completa_corta)}</td>
              </tr>
              <tr className="border-t">
                <td className="p-1.5">Dieta completa, viaje ≥ 7 días</td>
                <td className="p-1.5 text-right">{fmtEur(dietas[0].dieta_completa_larga)}</td>
              </tr>
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
