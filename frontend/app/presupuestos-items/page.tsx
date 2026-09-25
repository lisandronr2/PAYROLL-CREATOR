"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api, Empresa, ParametroNegocio, PartidaCatalogo, PresupuestoItems, PresupuestoItemsLinea } from "@/lib/api";

const lineaVacia: PresupuestoItemsLinea = {
  partida_id: 0,
  cantidad: "1",
  descuento_pct: "0",
};

function valorDefecto(parametros: ParametroNegocio[], clave: string): string {
  return parametros.find((p) => p.clave === clave)?.valor ?? "";
}

function PresupuestosItemsForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const presupuestoEditarId = searchParams.get("editar");

  const [presupuestos, setPresupuestos] = useState<PresupuestoItems[]>([]);
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [partidas, setPartidas] = useState<PartidaCatalogo[]>([]);
  const [parametrosNegocio, setParametrosNegocio] = useState<ParametroNegocio[]>([]);

  const [empresaId, setEmpresaId] = useState("");
  const [nombre, setNombre] = useState("");
  const [clienteNombre, setClienteNombre] = useState("");
  const [clienteNif, setClienteNif] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10));
  const [ivaPct, setIvaPct] = useState("");
  const [sinIva, setSinIva] = useState(false);
  const [notas, setNotas] = useState("");
  const [lineas, setLineas] = useState<PresupuestoItemsLinea[]>([{ ...lineaVacia }]);

  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [cargandoEdicion, setCargandoEdicion] = useState(!!presupuestoEditarId);

  function cargar() {
    Promise.all([api.presupuestosItems.listar(), api.empresas.listar(), api.partidasCatalogo.listar(), api.referencia.parametrosNegocio()])
      .then(([p, e, part, pn]) => {
        setPresupuestos(p);
        setEmpresas(e);
        setPartidas(part);
        setParametrosNegocio(pn);
        if (!presupuestoEditarId) {
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
    if (!presupuestoEditarId) return;
    api.presupuestosItems
      .obtener(Number(presupuestoEditarId))
      .then((p) => {
        setEmpresaId(String(p.empresa_id));
        setNombre(p.nombre);
        setClienteNombre(p.cliente_nombre ?? "");
        setClienteNif(p.cliente_nif ?? "");
        setFecha(p.fecha);
        setIvaPct(p.iva_pct);
        setSinIva(Number(p.iva_pct) === 0);
        setNotas(p.notas ?? "");
        setLineas(
          p.lineas.length
            ? p.lineas.map((l) => ({
                partida_id: l.partida_id,
                cantidad: l.cantidad,
                descuento_pct: l.descuento_pct,
              }))
            : [{ ...lineaVacia }]
        );
      })
      .catch((e) => setError(String(e)))
      .finally(() => setCargandoEdicion(false));
  }, [presupuestoEditarId]);

  function nombreEmpresa(id: number) {
    return empresas.find((e) => e.id === id)?.razon_social ?? id;
  }

  function partida(id: number) {
    return partidas.find((p) => p.id === id);
  }

  function actualizarLinea(i: number, cambios: Partial<PresupuestoItemsLinea>) {
    setLineas((prev) => prev.map((l, idx) => (idx === i ? { ...l, ...cambios } : l)));
  }

  function importeLinea(l: PresupuestoItemsLinea): number {
    const p = partida(l.partida_id);
    if (!p) return 0;
    const precio = Number(p.precio_venta);
    const cantidad = Number(l.cantidad) || 0;
    const descuento = Number(l.descuento_pct) || 0;
    return precio * cantidad * (1 - descuento / 100);
  }

  const subtotal = lineas.reduce((acc, l) => acc + importeLinea(l), 0);
  const ivaPctEfectivo = sinIva ? 0 : Number(ivaPct) || 0;
  const ivaImporte = (subtotal * ivaPctEfectivo) / 100;

  function limpiarFormulario() {
    setNombre("");
    setClienteNombre("");
    setClienteNif("");
    setNotas("");
    setSinIva(false);
    setLineas([{ ...lineaVacia }]);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const payload = {
        empresa_id: Number(empresaId),
        nombre,
        cliente_nombre: clienteNombre || null,
        cliente_nif: clienteNif || null,
        fecha,
        iva_pct: sinIva ? "0" : ivaPct,
        notas: notas || null,
        lineas: lineas
          .filter((l) => l.partida_id)
          .map((l) => ({
            partida_id: l.partida_id,
            cantidad: l.cantidad,
            descuento_pct: l.descuento_pct,
          })),
      };

      if (presupuestoEditarId) {
        await api.presupuestosItems.actualizar(Number(presupuestoEditarId), payload);
        router.push(`/presupuestos-items/${presupuestoEditarId}`);
      } else {
        await api.presupuestosItems.crear(payload);
        limpiarFormulario();
        cargar();
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  const familias = Array.from(new Set(partidas.map((p) => p.familia)));

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">
        {presupuestoEditarId ? "Editar presupuesto por items" : "Presupuesto por items"}
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
          <label className="flex items-center gap-2 text-xs text-slate-500">
            IVA (%)
            <input
              type="number"
              step="0.01"
              disabled={sinIva}
              className="border rounded px-3 py-2 flex-1 disabled:bg-slate-100 disabled:text-slate-400"
              value={sinIva ? "0" : ivaPct}
              onChange={(e) => setIvaPct(e.target.value)}
            />
          </label>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={sinIva}
            onChange={(e) => {
              const marcado = e.target.checked;
              setSinIva(marcado);
              if (!marcado) setIvaPct((prev) => prev || valorDefecto(parametrosNegocio, "iva_pct_defecto"));
            }}
          />
          No incluir IVA en este presupuesto
        </label>
        {sinIva && (
          <p className="text-xs text-amber-700">
            El precio final se mostrará como "IVA no incluido" en el PDF y en el resumen.
          </p>
        )}

        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-medium text-sm">Partidas</h2>
            <button
              type="button"
              onClick={() => setLineas((prev) => [...prev, { ...lineaVacia }])}
              className="text-sm text-blue-600 underline"
            >
              + Añadir partida
            </button>
          </div>
          {lineas.map((linea, i) => {
            const p = partida(linea.partida_id);
            return (
              <div key={i} className="border rounded p-3 mb-2 grid sm:grid-cols-5 gap-2 text-sm items-end">
                <select
                  className="border rounded px-2 py-1 sm:col-span-2"
                  value={linea.partida_id || ""}
                  onChange={(e) => actualizarLinea(i, { partida_id: Number(e.target.value) })}
                >
                  <option value="">Partida del catálogo...</option>
                  {familias.map((familia) => (
                    <optgroup key={familia} label={familia}>
                      {partidas
                        .filter((part) => part.familia === familia)
                        .map((part) => (
                          <option key={part.id} value={part.id}>
                            {part.nombre} ({part.unidad}) — {Number(part.precio_venta).toFixed(2)} €
                          </option>
                        ))}
                    </optgroup>
                  ))}
                </select>
                <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                  Cantidad ({p?.unidad ?? "ud"})
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    className="border rounded px-2 py-1"
                    value={linea.cantidad}
                    onChange={(e) => actualizarLinea(i, { cantidad: e.target.value })}
                  />
                </label>
                <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                  Descuento %
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step="0.01"
                    className="border rounded px-2 py-1"
                    value={linea.descuento_pct}
                    onChange={(e) => actualizarLinea(i, { descuento_pct: e.target.value })}
                  />
                </label>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-slate-600">{importeLinea(linea).toFixed(2)} €</span>
                  {lineas.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setLineas((prev) => prev.filter((_, idx) => idx !== i))}
                      className="text-red-600 text-xs underline"
                    >
                      Quitar
                    </button>
                  )}
                </div>
              </div>
            );
          })}
          <p className="text-xs text-slate-400">
            Cada partida ya trae su margen incluido en el precio unitario — el importe de la línea es
            precio unitario × cantidad, con el descuento que indiques. Solo se añade el IVA al final.
          </p>
        </div>

        <div className="bg-slate-50 border rounded p-3 text-sm space-y-1">
          <div className="flex justify-between"><span>Subtotal</span><strong>{subtotal.toFixed(2)} €</strong></div>
          {!sinIva && (
            <div className="flex justify-between"><span>IVA ({ivaPctEfectivo}%)</span><strong>{ivaImporte.toFixed(2)} €</strong></div>
          )}
          <div className="flex justify-between text-base border-t pt-1 mt-1">
            <span>Total{sinIva ? " (IVA no incluido)" : ""}</span><strong>{(subtotal + ivaImporte).toFixed(2)} €</strong>
          </div>
        </div>

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
              onClick={() => router.push(`/presupuestos-items/${presupuestoEditarId}`)}
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
                <Link href={`/presupuestos-items/${p.id}`} className="text-blue-600 underline">
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

export default function PresupuestosItemsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Cargando...</p>}>
      <PresupuestosItemsForm />
    </Suspense>
  );
}
