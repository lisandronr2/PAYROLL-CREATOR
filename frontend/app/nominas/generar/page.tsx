"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, Contrato, Nomina, Trabajador } from "@/lib/api";

const initialForm = {
  contrato_id: "",
  periodo_anio: String(new Date().getFullYear()),
  periodo_mes: String(new Date().getMonth() + 1),
  dias_naturales_periodo: "30",
  horas_extra: "0",
  dias_it: "0",
  dias_vacaciones: "0",
  anticipos: "0",
  embargo_mensual: "0",
  numero_medias_dietas: "0",
  numero_dietas_completas_cortas: "0",
  numero_dietas_completas_largas: "0",
};

const BLOQUE_LABEL: Record<string, string> = {
  devengo: "Devengos",
  cotizacion_trabajador: "Cotización (trabajador)",
  cotizacion_empresa: "Cotización (empresa)",
  deduccion: "Deducciones",
};

function GenerarNominaForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const nominaEditarId = searchParams.get("editar");

  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([]);
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [form, setForm] = useState(initialForm);
  const [resultado, setResultado] = useState<Nomina | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [cargandoEdicion, setCargandoEdicion] = useState(!!nominaEditarId);

  useEffect(() => {
    Promise.all([api.trabajadores.listar(), api.contratos.listar()]).then(([t, c]) => {
      setTrabajadores(t);
      setContratos(c);
    });
  }, []);

  useEffect(() => {
    if (!nominaEditarId) return;
    api.nominas
      .obtener(Number(nominaEditarId))
      .then((n) => {
        setForm({
          contrato_id: String(n.contrato_id),
          periodo_anio: String(n.periodo_anio),
          periodo_mes: String(n.periodo_mes),
          dias_naturales_periodo: String(n.dias_naturales_periodo),
          horas_extra: n.horas_extra,
          dias_it: String(n.dias_it),
          dias_vacaciones: String(n.dias_vacaciones),
          anticipos: n.anticipos,
          embargo_mensual: n.embargo_mensual,
          numero_medias_dietas: String(n.numero_medias_dietas),
          numero_dietas_completas_cortas: String(n.numero_dietas_completas_cortas),
          numero_dietas_completas_largas: String(n.numero_dietas_completas_largas),
        });
        setResultado(n);
      })
      .catch((err) => setError(String(err)))
      .finally(() => setCargandoEdicion(false));
  }, [nominaEditarId]);

  function nombreContrato(c: Contrato) {
    const t = trabajadores.find((x) => x.id === c.trabajador_id);
    return t ? `${t.nombre} ${t.apellidos} (${c.tipo_contrato})` : `Contrato #${c.id}`;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const payload = {
        contrato_id: Number(form.contrato_id),
        periodo_anio: Number(form.periodo_anio),
        periodo_mes: Number(form.periodo_mes),
        dias_naturales_periodo: Number(form.dias_naturales_periodo),
        horas_extra: Number(form.horas_extra),
        dias_it: Number(form.dias_it),
        dias_vacaciones: Number(form.dias_vacaciones),
        anticipos: Number(form.anticipos),
        embargo_mensual: Number(form.embargo_mensual),
        numero_medias_dietas: Number(form.numero_medias_dietas),
        numero_dietas_completas_cortas: Number(form.numero_dietas_completas_cortas),
        numero_dietas_completas_largas: Number(form.numero_dietas_completas_largas),
      };
      const nomina = nominaEditarId
        ? await api.nominas.actualizar(Number(nominaEditarId), payload)
        : await api.nominas.generar(payload);
      setResultado(nomina);
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  function agrupar(nomina: Nomina) {
    const grupos: Record<string, typeof nomina.lineas> = {};
    for (const linea of nomina.lineas) {
      grupos[linea.bloque] = grupos[linea.bloque] || [];
      grupos[linea.bloque].push(linea);
    }
    return grupos;
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">{nominaEditarId ? "Editar nómina" : "Generar nómina"}</h1>

      {cargandoEdicion ? (
        <p className="text-sm text-slate-500 mb-4">Cargando datos de la nómina...</p>
      ) : (
        <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 mb-6 grid sm:grid-cols-3 gap-3">
          <select
            required
            className="border rounded px-3 py-2 sm:col-span-3"
            value={form.contrato_id}
            onChange={(e) => setForm({ ...form, contrato_id: e.target.value })}
          >
            <option value="">Contrato...</option>
            {contratos.map((c) => (
              <option key={c.id} value={c.id}>
                {nombreContrato(c)}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Año"
            className="border rounded px-3 py-2"
            value={form.periodo_anio}
            onChange={(e) => setForm({ ...form, periodo_anio: e.target.value })}
          />
          <input
            type="number"
            min={1}
            max={12}
            placeholder="Mes (1-12)"
            className="border rounded px-3 py-2"
            value={form.periodo_mes}
            onChange={(e) => setForm({ ...form, periodo_mes: e.target.value })}
          />
          <input
            type="number"
            placeholder="Días naturales del periodo"
            className="border rounded px-3 py-2"
            value={form.dias_naturales_periodo}
            onChange={(e) => setForm({ ...form, dias_naturales_periodo: e.target.value })}
          />
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Horas extra
            <input
              type="number"
              step="0.5"
              className="border rounded px-3 py-2"
              value={form.horas_extra}
              onChange={(e) => setForm({ ...form, horas_extra: e.target.value })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Días de IT
            <input
              type="number"
              className="border rounded px-3 py-2"
              value={form.dias_it}
              onChange={(e) => setForm({ ...form, dias_it: e.target.value })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Días de vacaciones
            <input
              type="number"
              className="border rounded px-3 py-2"
              value={form.dias_vacaciones}
              onChange={(e) => setForm({ ...form, dias_vacaciones: e.target.value })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Anticipos (€)
            <input
              type="number"
              step="0.01"
              className="border rounded px-3 py-2"
              value={form.anticipos}
              onChange={(e) => setForm({ ...form, anticipos: e.target.value })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Embargo mensual (€)
            <input
              type="number"
              step="0.01"
              className="border rounded px-3 py-2"
              value={form.embargo_mensual}
              onChange={(e) => setForm({ ...form, embargo_mensual: e.target.value })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Medias dietas (nº días)
            <input
              type="number"
              className="border rounded px-3 py-2"
              value={form.numero_medias_dietas}
              onChange={(e) => setForm({ ...form, numero_medias_dietas: e.target.value })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Dietas completas, viaje &lt;7 días (nº días)
            <input
              type="number"
              className="border rounded px-3 py-2"
              value={form.numero_dietas_completas_cortas}
              onChange={(e) => setForm({ ...form, numero_dietas_completas_cortas: e.target.value })}
            />
          </label>
          <label className="text-xs text-slate-500 flex flex-col gap-1">
            Dietas completas, viaje ≥7 días (nº días)
            <input
              type="number"
              className="border rounded px-3 py-2"
              value={form.numero_dietas_completas_largas}
              onChange={(e) => setForm({ ...form, numero_dietas_completas_largas: e.target.value })}
            />
          </label>
          <div className="sm:col-span-3 flex gap-2">
            <button
              disabled={cargando}
              className="flex-1 bg-slate-900 text-white rounded py-2 disabled:opacity-50"
            >
              {cargando
                ? "Calculando..."
                : nominaEditarId
                  ? "Guardar cambios"
                  : "Calcular nómina"}
            </button>
            {nominaEditarId && (
              <button
                type="button"
                onClick={() => router.push("/nominas/historial")}
                className="px-4 rounded border text-sm"
              >
                Cancelar
              </button>
            )}
          </div>
        </form>
      )}

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      {resultado && (
        <div className="bg-white border rounded-lg p-4 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="font-medium">
              Nómina {resultado.periodo_mes}/{resultado.periodo_anio}
            </h2>
            <button
              onClick={() =>
                api.nominas.verPdf(resultado.id, `nomina_${resultado.periodo_anio}_${resultado.periodo_mes}.pdf`)
              }
              className="text-sm bg-slate-900 text-white px-3 py-1.5 rounded"
            >
              Ver PDF
            </button>
          </div>

          {Object.entries(agrupar(resultado)).map(([bloque, lineas]) => (
            <div key={bloque}>
              <h3 className="text-sm font-semibold text-slate-600 mb-1">{BLOQUE_LABEL[bloque] ?? bloque}</h3>
              <table className="w-full text-sm">
                <tbody>
                  {lineas.map((l, i) => (
                    <tr key={i} className="border-t align-top">
                      <td className="p-1.5">
                        {l.cantidad != null && bloque === "devengo" && (
                          <span className="text-slate-400">
                            {Number(l.cantidad).toFixed(2)} × {l.base ? Number(l.base).toFixed(4) : "-"} ·{" "}
                          </span>
                        )}
                        {l.concepto}
                        {bloque === "devengo" && (
                          <span className="font-semibold"> ({l.cotiza ? "1" : "2"})</span>
                        )}
                        {l.referencia_legal && (
                          <div className="text-xs text-slate-400">{l.referencia_legal}</div>
                        )}
                      </td>
                      <td className="p-1.5 text-right whitespace-nowrap">
                        {l.tipo_pct ? `${l.tipo_pct}% · ` : ""}
                        {Number(l.importe).toFixed(2)} €
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {bloque === "devengo" && (
                <p className="text-xs text-slate-400 mt-1">
                  (1) Computa en la base de cotización a la Seguridad Social. (2) Exento de cotización.
                </p>
              )}
            </div>
          ))}

          <div className="border-t pt-3 grid sm:grid-cols-2 gap-2 text-sm">
            <div>Total devengado: <strong>{Number(resultado.total_devengado).toFixed(2)} €</strong></div>
            <div>Total deducciones: <strong>{Number(resultado.total_deducciones).toFixed(2)} €</strong></div>
            <div>Base cotización común: <strong>{Number(resultado.base_cotizacion_comun).toFixed(2)} €</strong></div>
            <div>Base sujeta a IRPF: <strong>{Number(resultado.base_sujeta_irpf).toFixed(2)} €</strong></div>
            <div>Coste total empresa: <strong>{Number(resultado.coste_empresa_total).toFixed(2)} €</strong></div>
            {Number(resultado.total_dietas_exentas) > 0 && (
              <div>
                Dietas exentas (incluidas arriba): <strong>{Number(resultado.total_dietas_exentas).toFixed(2)} €</strong>
              </div>
            )}
            <div className="text-base">
              Líquido a percibir: <strong>{Number(resultado.liquido_a_percibir).toFixed(2)} €</strong>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function GenerarNominaPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Cargando...</p>}>
      <GenerarNominaForm />
    </Suspense>
  );
}
