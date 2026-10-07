"use client";

import { useEffect, useState } from "react";
import { api, Contrato, Liquidacion, SugerenciasLiquidacion, Trabajador } from "@/lib/api";

const MOTIVOS: { valor: string; texto: string }[] = [
  { valor: "dimision", texto: "Dimisión (baja voluntaria)" },
  { valor: "despido_disciplinario", texto: "Despido disciplinario procedente" },
  { valor: "despido_improcedente", texto: "Despido improcedente" },
  { valor: "despido_objetivo", texto: "Despido objetivo" },
  { valor: "fin_contrato_temporal", texto: "Fin de contrato temporal" },
  { valor: "mutuo_acuerdo", texto: "Mutuo acuerdo" },
  { valor: "fin_periodo_prueba", texto: "Fin del periodo de prueba" },
];

function eur(valor: string | number) {
  return `${Number(valor).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
}

function fechaEs(iso: string) {
  const [a, m, d] = iso.split("-");
  return `${d}/${m}/${a}`;
}

export default function LiquidacionPage() {
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([]);
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [trabajadorId, setTrabajadorId] = useState("");
  const [contratoId, setContratoId] = useState("");

  const [motivo, setMotivo] = useState("dimision");
  const [fechaIngreso, setFechaIngreso] = useState("");
  const [fechaBaja, setFechaBaja] = useState("");

  const [vacacionesDisfrutadas, setVacacionesDisfrutadas] = useState("0");
  const [unidadVacaciones, setUnidadVacaciones] = useState<"laborables" | "naturales">("naturales");
  const [vacacionesAnteriores, setVacacionesAnteriores] = useState("0");

  const [preavisoExigido, setPreavisoExigido] = useState("0");
  const [preavisoTrabajado, setPreavisoTrabajado] = useState("0");

  const [otrasCantidades, setOtrasCantidades] = useState("0");
  const [indemnizacionPactada, setIndemnizacionPactada] = useState("0");
  const [descuentos, setDescuentos] = useState("0");

  const [sugerencias, setSugerencias] = useState<SugerenciasLiquidacion | null>(null);
  const [resultado, setResultado] = useState<Liquidacion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    api.trabajadores.listar().then(setTrabajadores).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    setContratoId("");
    setSugerencias(null);
    setResultado(null);
    if (!trabajadorId) {
      setContratos([]);
      return;
    }
    api.contratos
      .listar(Number(trabajadorId))
      .then((lista) => {
        setContratos(lista);
        if (lista.length === 1) setContratoId(String(lista[0].id));
      })
      .catch((e) => setError(String(e)));
  }, [trabajadorId]);

  // Al elegir contrato se rellenan fecha de ingreso y unidad de vacaciones con los datos del convenio.
  useEffect(() => {
    setResultado(null);
    if (!contratoId) {
      setSugerencias(null);
      return;
    }
    api.liquidaciones
      .sugerencias(Number(contratoId), motivo, fechaBaja || undefined)
      .then((s) => {
        setSugerencias(s);
        setFechaIngreso(s.fecha_ingreso);
        setUnidadVacaciones(s.unidad_vacaciones_defecto);
        setPreavisoExigido(String(s.dias_preaviso_exigidos));
      })
      .catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contratoId]);

  // El preaviso exigido depende del motivo (y de la duración del contrato en los temporales).
  useEffect(() => {
    if (!contratoId) return;
    api.liquidaciones
      .sugerencias(Number(contratoId), motivo, fechaBaja || undefined)
      .then((s) => {
        setSugerencias(s);
        setPreavisoExigido(String(s.dias_preaviso_exigidos));
      })
      .catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [motivo, fechaBaja]);

  async function calcular(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    setResultado(null);
    try {
      const r = await api.liquidaciones.calcular({
        contrato_id: Number(contratoId),
        fecha_ingreso: fechaIngreso || null,
        fecha_baja: fechaBaja,
        motivo,
        vacaciones_disfrutadas: vacacionesDisfrutadas || "0",
        unidad_vacaciones: unidadVacaciones,
        vacaciones_pendientes_anteriores: vacacionesAnteriores || "0",
        dias_preaviso_exigidos: Number(preavisoExigido) || 0,
        dias_preaviso_trabajados: Number(preavisoTrabajado) || 0,
        otras_cantidades: otrasCantidades || "0",
        indemnizacion_pactada: indemnizacionPactada || "0",
        descuentos: descuentos || "0",
      });
      setResultado(r);
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  const puedeCalcular = !!contratoId && !!fechaBaja && !!fechaIngreso;

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Liquidación / finiquito</h1>
        <p className="text-sm text-slate-500 mt-1">
          Calcula la liquidación de un trabajador a partir de su contrato y del convenio: salario pendiente,
          pagas extra devengadas, vacaciones no disfrutadas, preaviso e indemnización según el motivo de la
          baja, con la cotización a la Seguridad Social, el IRPF y el coste para la empresa. Solo calcula: no
          modifica el contrato ni da de baja al trabajador.
        </p>
      </div>

      <form onSubmit={calcular} className="bg-white border rounded-lg p-4 space-y-4">
        <div className="grid sm:grid-cols-2 gap-3">
          <select required className="border rounded px-3 py-2" value={trabajadorId} onChange={(e) => setTrabajadorId(e.target.value)}>
            <option value="">Trabajador...</option>
            {trabajadores.map((t) => (
              <option key={t.id} value={t.id}>
                {t.apellidos}, {t.nombre} ({t.nif})
              </option>
            ))}
          </select>
          <select
            required
            className="border rounded px-3 py-2"
            value={contratoId}
            onChange={(e) => setContratoId(e.target.value)}
            disabled={!trabajadorId}
          >
            <option value="">Contrato...</option>
            {contratos.map((c) => (
              <option key={c.id} value={c.id}>
                {c.tipo_contrato} — desde {fechaEs(c.fecha_inicio)}
                {c.fecha_fin ? ` hasta ${fechaEs(c.fecha_fin)}` : ""}
              </option>
            ))}
          </select>
        </div>

        {sugerencias && (
          <p className="text-xs text-slate-500">
            {sugerencias.categoria} · {sugerencias.convenio_nombre}
          </p>
        )}

        <div className="grid sm:grid-cols-3 gap-3">
          <label className="flex flex-col gap-1 text-xs text-slate-500 sm:col-span-3">
            Motivo de la baja
            <select className="border rounded px-3 py-2 text-sm text-slate-900" value={motivo} onChange={(e) => setMotivo(e.target.value)}>
              {MOTIVOS.map((m) => (
                <option key={m.valor} value={m.valor}>{m.texto}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-slate-500">
            Fecha de ingreso (antigüedad)
            <input
              required
              type="date"
              className="border rounded px-3 py-2 text-sm text-slate-900"
              value={fechaIngreso}
              onChange={(e) => setFechaIngreso(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-slate-500">
            Fecha de baja (último día)
            <input
              required
              type="date"
              className="border rounded px-3 py-2 text-sm text-slate-900"
              value={fechaBaja}
              onChange={(e) => setFechaBaja(e.target.value)}
            />
          </label>
        </div>

        <div className="border-t pt-3 space-y-2">
          <h2 className="font-medium text-sm">Vacaciones</h2>
          {sugerencias && <p className="text-xs text-slate-500">Convenio: {sugerencias.texto_vacaciones}</p>}
          <div className="grid sm:grid-cols-3 gap-3">
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Días disfrutados este año
              <input
                type="number"
                min={0}
                step="0.5"
                className="border rounded px-3 py-2 text-sm text-slate-900"
                value={vacacionesDisfrutadas}
                onChange={(e) => setVacacionesDisfrutadas(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Pendientes de años anteriores
              <input
                type="number"
                min={0}
                step="0.5"
                className="border rounded px-3 py-2 text-sm text-slate-900"
                value={vacacionesAnteriores}
                onChange={(e) => setVacacionesAnteriores(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Unidad de esos días
              <select
                className="border rounded px-3 py-2 text-sm text-slate-900"
                value={unidadVacaciones}
                onChange={(e) => setUnidadVacaciones(e.target.value as "laborables" | "naturales")}
              >
                <option value="naturales">Días naturales</option>
                <option value="laborables" disabled={!sugerencias?.vacaciones_dias_laborables}>
                  Días laborables
                </option>
              </select>
            </label>
          </div>
        </div>

        <div className="border-t pt-3 space-y-2">
          <h2 className="font-medium text-sm">Preaviso</h2>
          {sugerencias && <p className="text-xs text-slate-500">{sugerencias.texto_preaviso}</p>}
          <div className="grid sm:grid-cols-2 gap-3">
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Días de preaviso que corresponden
              <input
                type="number"
                min={0}
                className="border rounded px-3 py-2 text-sm text-slate-900"
                value={preavisoExigido}
                onChange={(e) => setPreavisoExigido(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              De ellos, trabajados o cumplidos
              <input
                type="number"
                min={0}
                className="border rounded px-3 py-2 text-sm text-slate-900"
                value={preavisoTrabajado}
                onChange={(e) => setPreavisoTrabajado(e.target.value)}
              />
            </label>
          </div>
          <p className="text-xs text-slate-400">
            Los días que no se cumplan se descuentan al trabajador si dimite, o los paga la empresa si es
            despido objetivo o fin de temporal de más de un año.
          </p>
        </div>

        <div className="border-t pt-3 space-y-2">
          <h2 className="font-medium text-sm">Otros conceptos (opcional)</h2>
          <div className="grid sm:grid-cols-3 gap-3">
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Otras cantidades a abonar (€)
              <input
                type="number"
                min={0}
                step="0.01"
                className="border rounded px-3 py-2 text-sm text-slate-900"
                value={otrasCantidades}
                onChange={(e) => setOtrasCantidades(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Indemnización pactada (€)
              <input
                type="number"
                min={0}
                step="0.01"
                className="border rounded px-3 py-2 text-sm text-slate-900"
                value={indemnizacionPactada}
                onChange={(e) => setIndemnizacionPactada(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Descuentos pendientes (€)
              <input
                type="number"
                min={0}
                step="0.01"
                className="border rounded px-3 py-2 text-sm text-slate-900"
                value={descuentos}
                onChange={(e) => setDescuentos(e.target.value)}
              />
            </label>
          </div>
        </div>

        <button
          disabled={cargando || !puedeCalcular}
          className="bg-slate-900 text-white rounded py-2 px-4 text-sm disabled:opacity-50"
        >
          {cargando ? "Calculando..." : "Calcular liquidación"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {resultado && (
        <div className="bg-white border rounded-lg p-4 space-y-3">
          <div>
            <h2 className="font-medium">{resultado.trabajador_nombre} ({resultado.trabajador_nif})</h2>
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
                Indemnización legal: <strong>{eur(resultado.indemnizacion_legal)}</strong> (exenta de IRPF y
                cotización)
              </div>
            )}
          </div>

          {resultado.avisos.length > 0 && (
            <ul className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-3 space-y-1 list-disc list-inside">
              {resultado.avisos.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
