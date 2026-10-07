"use client";

import { Liquidacion } from "@/lib/api";

export function eur(valor: string | number) {
  return `${Number(valor).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
}

export function fechaEs(iso: string) {
  const [a, m, d] = iso.split("-");
  return `${d}/${m}/${a}`;
}

export default function ResultadoLiquidacion({ resultado, notas }: { resultado: Liquidacion; notas?: string | null }) {
  return (
    <div className="space-y-3">
      <div>
        <h2 className="font-medium">
          {resultado.trabajador_nombre} ({resultado.trabajador_nif})
        </h2>
        <p className="text-sm text-slate-500">
          {resultado.categoria} · {resultado.motivo_texto}
        </p>
        <p className="text-sm text-slate-500">
          Ingreso {fechaEs(resultado.fecha_ingreso)} · Baja {fechaEs(resultado.fecha_baja)} · Antigüedad:{" "}
          {resultado.antiguedad_texto}
        </p>
      </div>

      <table className="w-full text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-1.5">Concepto</th>
            <th className="text-center p-1.5 w-12" title="Cotiza a la Seguridad Social">SS</th>
            <th className="text-center p-1.5 w-12" title="Tributa por IRPF">IRPF</th>
            <th className="text-right p-1.5">Importe</th>
          </tr>
        </thead>
        <tbody>
          {resultado.lineas.map((l, i) => {
            const resta = l.bloque === "descuento" || l.bloque === "deduccion";
            return (
              <tr key={i} className="border-t align-top">
                <td className="p-1.5">
                  <div>{l.concepto}</div>
                  {l.detalle && <div className="text-xs text-slate-500">{l.detalle}</div>}
                  {l.referencia_legal && <div className="text-xs text-slate-400">{l.referencia_legal}</div>}
                </td>
                <td className="p-1.5 text-center text-xs">{l.bloque === "deduccion" ? "" : l.cotiza ? "Sí" : "No"}</td>
                <td className="p-1.5 text-center text-xs">{l.bloque === "deduccion" ? "" : l.tributa ? "Sí" : "No"}</td>
                <td className={`p-1.5 text-right whitespace-nowrap ${resta ? "text-red-700" : ""}`}>
                  {resta ? "−" : ""}
                  {eur(l.importe)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className="border-t pt-3 grid sm:grid-cols-3 gap-2">
        <div className="bg-slate-50 border rounded p-3">
          <div className="text-xs text-slate-500">Total bruto</div>
          <div className="text-lg font-semibold">{eur(resultado.total_ingresos)}</div>
        </div>
        <div className="bg-slate-50 border rounded p-3">
          <div className="text-xs text-slate-500">Total deducciones</div>
          <div className="text-lg font-semibold">{eur(resultado.total_deducciones)}</div>
        </div>
        <div className="bg-slate-900 text-white rounded p-3">
          <div className="text-xs opacity-80">Líquido a percibir</div>
          <div className="text-xl font-semibold">{eur(resultado.liquido_a_percibir)}</div>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-2 text-sm bg-slate-50 border rounded p-3">
        <div>Cotización SS empresa: <strong>{eur(resultado.cuota_empresa_ss)}</strong></div>
        <div>Coste total para la empresa: <strong>{eur(resultado.coste_empresa_total)}</strong></div>
        {Number(resultado.indemnizacion_legal) > 0 && (
          <div className="sm:col-span-2">
            Indemnización legal: <strong>{eur(resultado.indemnizacion_legal)}</strong> (exenta de IRPF y cotización)
          </div>
        )}
      </div>

      {notas && (
        <div className="text-sm">
          <h3 className="text-sm font-semibold text-slate-600 mb-1">Notas</h3>
          <p className="text-slate-600 whitespace-pre-wrap">{notas}</p>
        </div>
      )}

      {resultado.avisos.length > 0 && (
        <ul className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-3 space-y-1 list-disc list-inside">
          {resultado.avisos.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
