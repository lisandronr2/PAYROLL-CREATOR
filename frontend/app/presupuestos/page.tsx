"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  api,
  CategoriaProfesional,
  Convenio,
  Empresa,
  ParametroNegocio,
  Presupuesto,
  PresupuestoLineaOtroCoste,
  PresupuestoLineaPersonal,
} from "@/lib/api";

const lineaPersonalVacia: PresupuestoLineaPersonal = {
  categoria_id: 0,
  cantidad_personas: 1,
  jornada_porcentaje: "100",
  dias_dedicacion: "20",
  pagas_extra_prorrateadas: true,
  complemento_mensual: "0",
  numero_medias_dietas: 0,
  numero_dietas_completas_cortas: 0,
  numero_dietas_completas_largas: 0,
};

const lineaOtroVacia: PresupuestoLineaOtroCoste = {
  concepto: "",
  cantidad: "1",
  precio_unitario: "0",
};

function valorDefecto(parametros: ParametroNegocio[], clave: string): string {
  return parametros.find((p) => p.clave === clave)?.valor ?? "";
}

function PresupuestosForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const presupuestoEditarId = searchParams.get("editar");

  const [presupuestos, setPresupuestos] = useState<Presupuesto[]>([]);
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [convenios, setConvenios] = useState<Convenio[]>([]);
  const [categorias, setCategorias] = useState<CategoriaProfesional[]>([]);
  const [parametrosNegocio, setParametrosNegocio] = useState<ParametroNegocio[]>([]);

  const [empresaId, setEmpresaId] = useState("");
  const [convenioId, setConvenioId] = useState("");
  const [nombre, setNombre] = useState("");
  const [clienteNombre, setClienteNombre] = useState("");
  const [clienteNif, setClienteNif] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [margenPct, setMargenPct] = useState("");
  const [gastosPct, setGastosPct] = useState("");
  const [ivaPct, setIvaPct] = useState("");
  const [notas, setNotas] = useState("");
  const [lineasPersonal, setLineasPersonal] = useState<PresupuestoLineaPersonal[]>([{ ...lineaPersonalVacia }]);
  const [lineasOtros, setLineasOtros] = useState<PresupuestoLineaOtroCoste[]>([]);

  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [cargandoEdicion, setCargandoEdicion] = useState(!!presupuestoEditarId);

  function cargar() {
    Promise.all([
      api.presupuestos.listar(),
      api.empresas.listar(),
      api.convenios.listar(),
      api.referencia.parametrosNegocio(),
    ])
      .then(([p, e, c, pn]) => {
        setPresupuestos(p);
        setEmpresas(e);
        setConvenios(c);
        setParametrosNegocio(pn);
        if (!presupuestoEditarId) {
          setMargenPct((prev) => prev || valorDefecto(pn, "margen_beneficio_pct_defecto"));
          setGastosPct((prev) => prev || valorDefecto(pn, "gastos_generales_pct_defecto"));
          setIvaPct((prev) => prev || valorDefecto(pn, "iva_pct_defecto"));
        }
      })
      .catch((e) => setError(String(e)));
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!convenioId) {
      setCategorias([]);
      return;
    }
    api.convenios.categorias(Number(convenioId)).then(setCategorias);
  }, [convenioId]);

  // Al editar un presupuesto existente, precargar todos sus datos en el formulario.
  useEffect(() => {
    if (!presupuestoEditarId) return;
    api.presupuestos
      .obtener(Number(presupuestoEditarId))
      .then((p) => {
        setEmpresaId(String(p.empresa_id));
        setConvenioId(String(p.convenio_id));
        setNombre(p.nombre);
        setClienteNombre(p.cliente_nombre ?? "");
        setClienteNif(p.cliente_nif ?? "");
        setFecha(p.fecha);
        setMargenPct(p.margen_beneficio_pct);
        setGastosPct(p.gastos_generales_pct);
        setIvaPct(p.iva_pct);
        setNotas(p.notas ?? "");
        setLineasPersonal(
          p.lineas_personal.length
            ? p.lineas_personal.map((l) => ({
                categoria_id: l.categoria_id,
                cantidad_personas: l.cantidad_personas,
                jornada_porcentaje: l.jornada_porcentaje,
                dias_dedicacion: l.dias_dedicacion,
                pagas_extra_prorrateadas: l.pagas_extra_prorrateadas,
                complemento_mensual: l.complemento_mensual,
                numero_medias_dietas: l.numero_medias_dietas,
                numero_dietas_completas_cortas: l.numero_dietas_completas_cortas,
                numero_dietas_completas_largas: l.numero_dietas_completas_largas,
              }))
            : [{ ...lineaPersonalVacia }]
        );
        setLineasOtros(
          p.lineas_otros.map((l) => ({
            concepto: l.concepto,
            cantidad: l.cantidad,
            precio_unitario: l.precio_unitario,
          }))
        );
      })
      .catch((e) => setError(String(e)))
      .finally(() => setCargandoEdicion(false));
  }, [presupuestoEditarId]);

  function nombreEmpresa(id: number) {
    return empresas.find((e) => e.id === id)?.razon_social ?? id;
  }

  function actualizarLineaPersonal(i: number, cambios: Partial<PresupuestoLineaPersonal>) {
    setLineasPersonal((prev) => prev.map((l, idx) => (idx === i ? { ...l, ...cambios } : l)));
  }

  function actualizarLineaOtro(i: number, cambios: Partial<PresupuestoLineaOtroCoste>) {
    setLineasOtros((prev) => prev.map((l, idx) => (idx === i ? { ...l, ...cambios } : l)));
  }

  function limpiarFormulario() {
    setNombre("");
    setClienteNombre("");
    setClienteNif("");
    setNotas("");
    setLineasPersonal([{ ...lineaPersonalVacia }]);
    setLineasOtros([]);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const payload = {
        empresa_id: Number(empresaId),
        convenio_id: Number(convenioId),
        nombre,
        cliente_nombre: clienteNombre || null,
        cliente_nif: clienteNif || null,
        fecha,
        margen_beneficio_pct: margenPct,
        gastos_generales_pct: gastosPct,
        iva_pct: ivaPct,
        notas: notas || null,
        lineas_personal: lineasPersonal
          .filter((l) => l.categoria_id)
          .map((l) => ({
            categoria_id: l.categoria_id,
            cantidad_personas: l.cantidad_personas,
            jornada_porcentaje: l.jornada_porcentaje,
            dias_dedicacion: l.dias_dedicacion,
            pagas_extra_prorrateadas: l.pagas_extra_prorrateadas,
            complemento_mensual: l.complemento_mensual,
            numero_medias_dietas: l.numero_medias_dietas,
            numero_dietas_completas_cortas: l.numero_dietas_completas_cortas,
            numero_dietas_completas_largas: l.numero_dietas_completas_largas,
          })),
        lineas_otros: lineasOtros
          .filter((l) => l.concepto)
          .map((l) => ({ concepto: l.concepto, cantidad: l.cantidad, precio_unitario: l.precio_unitario })),
      };

      if (presupuestoEditarId) {
        await api.presupuestos.actualizar(Number(presupuestoEditarId), payload);
        router.push(`/presupuestos/${presupuestoEditarId}`);
      } else {
        await api.presupuestos.crear(payload);
        limpiarFormulario();
        cargar();
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">
        {presupuestoEditarId ? "Editar presupuesto" : "Presupuestos"}
      </h1>

      {cargandoEdicion ? (
        <p className="text-sm text-slate-500 mb-4">Cargando datos del presupuesto...</p>
      ) : (
      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 mb-6 space-y-4">
        <div className="grid sm:grid-cols-2 gap-3">
          <select required className="border rounded px-3 py-2" value={empresaId} onChange={(e) => setEmpresaId(e.target.value)}>
            <option value="">Empresa que ejecuta...</option>
            {empresas.map((e) => (
              <option key={e.id} value={e.id}>{e.razon_social}</option>
            ))}
          </select>
          <select
            required
            className="border rounded px-3 py-2"
            value={convenioId}
            onChange={(e) => setConvenioId(e.target.value)}
          >
            <option value="">Convenio de referencia...</option>
            {convenios.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
          </select>
          <input
            required
            placeholder="Nombre / referencia del proyecto"
            className="border rounded px-3 py-2"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
          <input
            type="date"
            required
            className="border rounded px-3 py-2"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
          />
          <input
            placeholder="Cliente (nombre)"
            className="border rounded px-3 py-2"
            value={clienteNombre}
            onChange={(e) => setClienteNombre(e.target.value)}
          />
          <input
            placeholder="Cliente (NIF/CIF)"
            className="border rounded px-3 py-2"
            value={clienteNif}
            onChange={(e) => setClienteNif(e.target.value)}
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-medium text-sm">Personal</h2>
            <button
              type="button"
              onClick={() => setLineasPersonal((prev) => [...prev, { ...lineaPersonalVacia }])}
              className="text-sm text-blue-600 underline"
            >
              + Añadir personal
            </button>
          </div>
          {lineasPersonal.map((linea, i) => (
            <div key={i} className="border rounded p-3 mb-2 grid sm:grid-cols-4 gap-2 text-sm">
              <select
                className="border rounded px-2 py-1 sm:col-span-2"
                value={linea.categoria_id || ""}
                onChange={(e) => actualizarLineaPersonal(i, { categoria_id: Number(e.target.value) })}
              >
                <option value="">Categoría del convenio...</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>{c.grupo} — {c.nombre}</option>
                ))}
              </select>
              <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                Personas
                <input
                  type="number"
                  min={1}
                  className="border rounded px-2 py-1"
                  value={linea.cantidad_personas}
                  onChange={(e) => actualizarLineaPersonal(i, { cantidad_personas: Number(e.target.value) })}
                />
              </label>
              <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                Días laborables de dedicación
                <input
                  type="number"
                  min={0}
                  className="border rounded px-2 py-1"
                  value={linea.dias_dedicacion}
                  onChange={(e) => actualizarLineaPersonal(i, { dias_dedicacion: e.target.value })}
                />
              </label>
              <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                Jornada %
                <input
                  type="number"
                  min={1}
                  max={100}
                  className="border rounded px-2 py-1"
                  value={linea.jornada_porcentaje}
                  onChange={(e) => actualizarLineaPersonal(i, { jornada_porcentaje: e.target.value })}
                />
              </label>
              <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                Dietas medias
                <input
                  type="number"
                  min={0}
                  className="border rounded px-2 py-1"
                  value={linea.numero_medias_dietas}
                  onChange={(e) => actualizarLineaPersonal(i, { numero_medias_dietas: Number(e.target.value) })}
                />
              </label>
              <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                Dietas completas &lt;7 días
                <input
                  type="number"
                  min={0}
                  className="border rounded px-2 py-1"
                  value={linea.numero_dietas_completas_cortas}
                  onChange={(e) =>
                    actualizarLineaPersonal(i, { numero_dietas_completas_cortas: Number(e.target.value) })
                  }
                />
              </label>
              <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                Dietas completas ≥7 días
                <input
                  type="number"
                  min={0}
                  className="border rounded px-2 py-1"
                  value={linea.numero_dietas_completas_largas}
                  onChange={(e) =>
                    actualizarLineaPersonal(i, { numero_dietas_completas_largas: Number(e.target.value) })
                  }
                />
              </label>
              <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                Mejora voluntaria mensual (€)
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  className="border rounded px-2 py-1"
                  value={linea.complemento_mensual}
                  onChange={(e) => actualizarLineaPersonal(i, { complemento_mensual: e.target.value })}
                />
              </label>
              <label className="flex items-center gap-1.5 text-xs text-slate-500">
                <input
                  type="checkbox"
                  checked={linea.pagas_extra_prorrateadas}
                  onChange={(e) => actualizarLineaPersonal(i, { pagas_extra_prorrateadas: e.target.checked })}
                />
                Prorratear pagas extra
              </label>
              {lineasPersonal.length > 1 && (
                <button
                  type="button"
                  onClick={() => setLineasPersonal((prev) => prev.filter((_, idx) => idx !== i))}
                  className="text-red-600 text-xs underline text-left"
                >
                  Quitar
                </button>
              )}
            </div>
          ))}
          <p className="text-xs text-slate-400">
            El coste de mano de obra se calcula tomando el sueldo mensual del convenio (con la paga extra
            prorrateada y las cotizaciones a cargo de la empresa) y dividiéndolo entre 20 días laborables, no
            entre los días naturales del mes — así se ajusta mejor a los días que la persona realmente va a
            trabajar en el proyecto.
          </p>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-medium text-sm">Materiales y otros costes (opcional)</h2>
            <button
              type="button"
              onClick={() => setLineasOtros((prev) => [...prev, { ...lineaOtroVacia }])}
              className="text-sm text-blue-600 underline"
            >
              + Añadir línea
            </button>
          </div>
          {lineasOtros.map((linea, i) => (
            <div key={i} className="border rounded p-3 mb-2 grid sm:grid-cols-4 gap-2 text-sm">
              <input
                placeholder="Concepto (ej. Materiales)"
                className="border rounded px-2 py-1 sm:col-span-2"
                value={linea.concepto}
                onChange={(e) => actualizarLineaOtro(i, { concepto: e.target.value })}
              />
              <input
                type="number"
                min={0}
                step="0.01"
                placeholder="Cantidad"
                className="border rounded px-2 py-1"
                value={linea.cantidad}
                onChange={(e) => actualizarLineaOtro(i, { cantidad: e.target.value })}
              />
              <input
                type="number"
                min={0}
                step="0.01"
                placeholder="Precio unitario (€)"
                className="border rounded px-2 py-1"
                value={linea.precio_unitario}
                onChange={(e) => actualizarLineaOtro(i, { precio_unitario: e.target.value })}
              />
              <button
                type="button"
                onClick={() => setLineasOtros((prev) => prev.filter((_, idx) => idx !== i))}
                className="text-red-600 text-xs underline text-left"
              >
                Quitar
              </button>
            </div>
          ))}
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          <label className="flex flex-col gap-1 text-xs text-slate-500">
            Margen de beneficio (%)
            <input
              type="number"
              step="0.01"
              className="border rounded px-3 py-2"
              value={margenPct}
              onChange={(e) => setMargenPct(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-slate-500">
            Gastos generales (%)
            <input
              type="number"
              step="0.01"
              className="border rounded px-3 py-2"
              value={gastosPct}
              onChange={(e) => setGastosPct(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-slate-500">
            IVA (%)
            <input
              type="number"
              step="0.01"
              className="border rounded px-3 py-2"
              value={ivaPct}
              onChange={(e) => setIvaPct(e.target.value)}
            />
          </label>
        </div>
        <p className="text-xs text-slate-400">
          Valores por defecto configurables en Admin → Parámetros de negocio. Puedes cambiarlos solo para este
          presupuesto sin afectar al resto.
        </p>

        <textarea
          placeholder="Notas (opcional)"
          className="border rounded px-3 py-2 w-full text-sm"
          rows={2}
          value={notas}
          onChange={(e) => setNotas(e.target.value)}
        />

        <div className="flex gap-2">
          <button disabled={cargando} className="bg-slate-900 text-white rounded py-2 px-4 disabled:opacity-50">
            {cargando ? "Calculando..." : presupuestoEditarId ? "Guardar cambios" : "Crear presupuesto"}
          </button>
          {presupuestoEditarId && (
            <button
              type="button"
              onClick={() => router.push(`/presupuestos/${presupuestoEditarId}`)}
              className="px-4 rounded border text-sm"
            >
              Cancelar
            </button>
          )}
        </div>
      </form>
      )}

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      {!presupuestoEditarId && (
      <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2">Proyecto</th>
            <th className="text-left p-2">Cliente</th>
            <th className="text-left p-2">Empresa</th>
            <th className="text-left p-2">Fecha</th>
            <th className="text-right p-2">Total cliente</th>
            <th className="text-right p-2"></th>
          </tr>
        </thead>
        <tbody>
          {presupuestos.map((p) => (
            <tr key={p.id} className="border-t">
              <td className="p-2">{p.nombre}</td>
              <td className="p-2">{p.cliente_nombre || "-"}</td>
              <td className="p-2">{nombreEmpresa(p.empresa_id)}</td>
              <td className="p-2">{p.fecha}</td>
              <td className="p-2 text-right">{Number(p.precio_total_cliente).toFixed(2)} €</td>
              <td className="p-2 text-right">
                <Link href={`/presupuestos/${p.id}`} className="text-blue-600 underline">
                  Ver
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      )}
    </div>
  );
}

export default function PresupuestosPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Cargando...</p>}>
      <PresupuestosForm />
    </Suspense>
  );
}
