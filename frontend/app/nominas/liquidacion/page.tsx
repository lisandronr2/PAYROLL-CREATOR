"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api, Contrato, Liquidacion, LiquidacionGuardada, SugerenciasLiquidacion, Trabajador } from "@/lib/api";
import ResultadoLiquidacion, { eur, fechaEs } from "@/components/ResultadoLiquidacion";

const MOTIVOS: { valor: string; texto: string }[] = [
  { valor: "dimision", texto: "Dimisión (baja voluntaria)" },
  { valor: "despido_disciplinario", texto: "Despido disciplinario procedente" },
  { valor: "despido_improcedente", texto: "Despido improcedente" },
  { valor: "despido_objetivo", texto: "Despido objetivo" },
  { valor: "fin_contrato_temporal", texto: "Fin de contrato temporal" },
  { valor: "mutuo_acuerdo", texto: "Mutuo acuerdo" },
  { valor: "fin_periodo_prueba", texto: "Fin del periodo de prueba" },
];

function LiquidacionForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const editarId = searchParams.get("editar");

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
  const [notas, setNotas] = useState("");

  const [sugerencias, setSugerencias] = useState<SugerenciasLiquidacion | null>(null);
  const [resultado, setResultado] = useState<Liquidacion | null>(null);
  const [huellaCalculada, setHuellaCalculada] = useState("");
  const [guardadas, setGuardadas] = useState<LiquidacionGuardada[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [cargandoEdicion, setCargandoEdicion] = useState(!!editarId);

  // Al editar, el contrato y los valores guardados no deben sobrescribirse con las sugerencias del convenio.
  const contratoPendiente = useRef<string | null>(null);
  const omitirSugerencias = useRef(false);

  useEffect(() => {
    api.trabajadores.listar().then(setTrabajadores).catch((e) => setError(String(e)));
  }, []);

  function cargarGuardadas() {
    api.liquidaciones.listar().then(setGuardadas).catch((e) => setError(String(e)));
  }

  useEffect(() => {
    if (!editarId) cargarGuardadas();
  }, [editarId]);

  // Al editar una liquidación guardada, se precarga todo su formulario.
  useEffect(() => {
    if (!editarId) return;
    api.liquidaciones
      .obtener(Number(editarId))
      .then((l) => {
        omitirSugerencias.current = true;
        contratoPendiente.current = String(l.contrato_id);
        setMotivo(l.motivo);
        setFechaIngreso(l.fecha_ingreso);
        setFechaBaja(l.fecha_baja);
        setVacacionesDisfrutadas(l.vacaciones_disfrutadas);
        setUnidadVacaciones(l.unidad_vacaciones);
        setVacacionesAnteriores(l.vacaciones_pendientes_anteriores);
        setPreavisoExigido(String(l.dias_preaviso_exigidos));
        setPreavisoTrabajado(String(l.dias_preaviso_trabajados));
        setOtrasCantidades(l.otras_cantidades);
        setIndemnizacionPactada(l.indemnizacion_pactada);
        setDescuentos(l.descuentos);
        setNotas(l.notas ?? "");
        setTrabajadorId(String(l.trabajador_id));
      })
      .catch((e) => setError(String(e)))
      .finally(() => setCargandoEdicion(false));
  }, [editarId]);

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
        if (contratoPendiente.current && lista.some((c) => String(c.id) === contratoPendiente.current)) {
          setContratoId(contratoPendiente.current);
          contratoPendiente.current = null;
        } else if (lista.length === 1) {
          setContratoId(String(lista[0].id));
        }
      })
      .catch((e) => setError(String(e)));
  }, [trabajadorId]);

  // Al elegir contrato se rellenan fecha de ingreso, unidad de vacaciones y preaviso con los datos del convenio.
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
        if (omitirSugerencias.current) {
          omitirSugerencias.current = false;
          return;
        }
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

  function construirPayload() {
    return {
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
      notas: notas.trim() || null,
    };
  }

  async function calcular(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    setResultado(null);
    try {
      const payload = construirPayload();
      const r = await api.liquidaciones.calcular(payload);
      setResultado(r);
      setHuellaCalculada(JSON.stringify(payload));
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  async function guardar(conPdf: boolean) {
    setError(null);
    setGuardando(true);
    // La pestaña del PDF se abre ya, en el propio clic, para que el navegador no la bloquee.
    const ventana = conPdf ? window.open("", "_blank") : null;
    let guardada: LiquidacionGuardada | null = null;
    try {
      const payload = construirPayload();
      guardada = editarId
        ? await api.liquidaciones.actualizar(Number(editarId), payload)
        : await api.liquidaciones.crear(payload);
      if (conPdf) {
        await api.liquidaciones.cargarPdfEn(ventana, guardada.id, "trabajador", `liquidacion_${guardada.id}_trabajador.pdf`);
      }
    } catch (err) {
      ventana?.close();
      if (guardada) {
        window.alert("La liquidación se guardó, pero no se pudo abrir el PDF. Puedes abrirlo desde su pantalla.");
      } else {
        setError(String(err));
      }
    } finally {
      setGuardando(false);
      if (guardada) router.push(`/nominas/liquidacion/${guardada.id}`);
    }
  }

  const puedeCalcular = !!contratoId && !!fechaBaja && !!fechaIngreso;
  const vistaPreviaDesactualizada = !!resultado && huellaCalculada !== JSON.stringify(construirPayload());

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold">{editarId ? "Editar liquidación" : "Liquidación / finiquito"}</h1>
        <p className="text-sm text-slate-500 mt-1">
          Calcula la liquidación de un trabajador a partir de su contrato y del convenio: salario pendiente,
          pagas extra devengadas, vacaciones no disfrutadas, preaviso e indemnización según el motivo de la
          baja, con la cotización a la Seguridad Social, el IRPF y el coste para la empresa. Al guardarla
          puedes imprimirla en PDF y editarla después; no modifica el contrato ni da de baja al trabajador.
        </p>
      </div>

      {cargandoEdicion ? (
        <p className="text-sm text-slate-500">Cargando datos de la liquidación...</p>
      ) : (
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
            <textarea
              placeholder="Notas (opcional, salen en el PDF)"
              className="border rounded px-3 py-2 w-full text-sm"
              rows={2}
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
            />
          </div>

          <div className="flex gap-2">
            <button
              disabled={cargando || !puedeCalcular}
              className="bg-slate-900 text-white rounded py-2 px-4 text-sm disabled:opacity-50"
            >
              {cargando ? "Calculando..." : "Calcular liquidación"}
            </button>
            {editarId && (
              <button
                type="button"
                onClick={() => router.push(`/nominas/liquidacion/${editarId}`)}
                className="px-4 rounded border text-sm"
              >
                Cancelar
              </button>
            )}
          </div>
        </form>
      )}

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {resultado && (
        <div className="bg-white border rounded-lg p-4 space-y-3">
          <ResultadoLiquidacion resultado={resultado} notas={notas.trim() || null} />

          {vistaPreviaDesactualizada && (
            <p className="text-xs text-amber-700">
              Has cambiado datos desde que calculaste: este resultado es de los datos anteriores. Al guardar se
              recalcula con los datos actuales.
            </p>
          )}

          <div className="flex gap-2 flex-wrap border-t pt-3">
            <button
              onClick={() => guardar(false)}
              disabled={guardando}
              className="text-sm bg-white border px-3 py-1.5 rounded disabled:opacity-50"
            >
              {guardando ? "Guardando..." : editarId ? "Guardar cambios" : "Guardar"}
            </button>
            <button
              onClick={() => guardar(true)}
              disabled={guardando}
              className="text-sm bg-slate-900 text-white px-3 py-1.5 rounded disabled:opacity-50"
            >
              {editarId ? "Guardar cambios y ver PDF" : "Guardar y ver PDF"}
            </button>
          </div>
        </div>
      )}

      {!editarId && guardadas.length > 0 && (
        <section>
          <h2 className="font-medium text-sm mb-2">Liquidaciones guardadas</h2>
          <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left p-2">Trabajador</th>
                <th className="text-left p-2">Motivo</th>
                <th className="text-left p-2">Baja</th>
                <th className="text-right p-2">Líquido</th>
                <th className="text-right p-2"></th>
              </tr>
            </thead>
            <tbody>
              {guardadas.map((l) => (
                <tr key={l.id} className="border-t">
                  <td className="p-2">{l.trabajador_nombre}</td>
                  <td className="p-2">{l.motivo_texto.split(" (")[0]}</td>
                  <td className="p-2">{fechaEs(l.fecha_baja)}</td>
                  <td className="p-2 text-right">{eur(l.liquido_a_percibir)}</td>
                  <td className="p-2 text-right">
                    <Link href={`/nominas/liquidacion/${l.id}`} className="text-blue-600 underline">
                      Ver
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

export default function LiquidacionPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Cargando...</p>}>
      <LiquidacionForm />
    </Suspense>
  );
}
