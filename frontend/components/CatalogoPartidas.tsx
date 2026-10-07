"use client";

import { useEffect, useMemo, useState } from "react";
import { api, PartidaCatalogo } from "@/lib/api";

const nuevaVacia = {
  nombre: "",
  unidad: "ud",
  precio_coste_mo: "0",
  precio_material: "0",
  precio_medios_aux: "0",
  margen_pct: "20",
  precio_venta_directo: "0",
  observaciones: "",
};

function costeDirecto(mo: string, mat: string, medios: string) {
  return (Number(mo) || 0) + (Number(mat) || 0) + (Number(medios) || 0);
}

function precioVenta(coste: number, margen: string) {
  return coste * (1 + (Number(margen) || 0) / 100);
}

export default function CatalogoPartidas() {
  const [partidas, setPartidas] = useState<PartidaCatalogo[]>([]);
  const [grupo, setGrupo] = useState("");
  const [error, setError] = useState<string | null>(null);

  const [nueva, setNueva] = useState({ ...nuevaVacia });
  const [soloPrecio, setSoloPrecio] = useState(false);
  const [creando, setCreando] = useState(false);

  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [edicion, setEdicion] = useState<Record<string, string>>({});

  function cargar() {
    api.partidasCatalogo
      .listar(false)
      .then((datos) => {
        setPartidas(datos);
        setGrupo((actual) => actual || datos[0]?.familia || "");
      })
      .catch((e) => setError(String(e)));
  }

  useEffect(() => {
    cargar();
  }, []);

  const grupos = useMemo(() => Array.from(new Set(partidas.map((p) => p.familia))).sort(), [partidas]);
  const partidasDelGrupo = useMemo(
    () => partidas.filter((p) => p.familia === grupo).sort((a, b) => a.nombre.localeCompare(b.nombre)),
    [partidas, grupo]
  );

  function cambiarGrupo(valor: string) {
    setGrupo(valor);
    setEditandoId(null);
    setError(null);
  }

  async function crearPartida(e: React.FormEvent) {
    e.preventDefault();
    if (!grupo) return;
    setError(null);
    setCreando(true);
    try {
      await api.partidasCatalogo.crear({
        familia: grupo,
        nombre: nueva.nombre,
        unidad: nueva.unidad,
        precio_coste_mo: soloPrecio ? nueva.precio_venta_directo : nueva.precio_coste_mo,
        precio_material: soloPrecio ? "0" : nueva.precio_material,
        precio_medios_aux: soloPrecio ? "0" : nueva.precio_medios_aux,
        margen_pct: soloPrecio ? "0" : nueva.margen_pct,
        observaciones: nueva.observaciones || null,
      });
      setNueva({ ...nuevaVacia });
      cargar();
    } catch (err) {
      setError(String(err));
    } finally {
      setCreando(false);
    }
  }

  function empezarEdicion(p: PartidaCatalogo) {
    setEditandoId(p.id);
    setEdicion({
      nombre: p.nombre,
      unidad: p.unidad,
      precio_coste_mo: p.precio_coste_mo,
      precio_material: p.precio_material,
      precio_medios_aux: p.precio_medios_aux,
      margen_pct: p.margen_pct,
      observaciones: p.observaciones ?? "",
    });
  }

  async function guardarEdicion(id: number) {
    setError(null);
    try {
      await api.partidasCatalogo.actualizar(id, {
        nombre: edicion.nombre,
        unidad: edicion.unidad,
        precio_coste_mo: edicion.precio_coste_mo,
        precio_material: edicion.precio_material,
        precio_medios_aux: edicion.precio_medios_aux,
        margen_pct: edicion.margen_pct,
        observaciones: edicion.observaciones || null,
      });
      setEditandoId(null);
      cargar();
    } catch (err) {
      setError(String(err));
    }
  }

  async function alternarActivo(p: PartidaCatalogo) {
    setError(null);
    try {
      await api.partidasCatalogo.actualizar(p.id, { activo: !p.activo });
      cargar();
    } catch (err) {
      setError(String(err));
    }
  }

  const costeNueva = soloPrecio
    ? Number(nueva.precio_venta_directo) || 0
    : costeDirecto(nueva.precio_coste_mo, nueva.precio_material, nueva.precio_medios_aux);
  const ventaNueva = soloPrecio ? costeNueva : precioVenta(costeNueva, nueva.margen_pct);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Partidas por grupo</h1>
        <p className="text-sm text-slate-500 mt-1">
          Elige un grupo (Cableado, CCTV, Armarios...) para añadir una partida nueva o modificar las que ya
          tiene. Los cambios se aplican a los presupuestos por items que crees a partir de ahora — los ya
          creados conservan el precio que tenían.
        </p>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <label className="flex flex-col gap-1 text-xs text-slate-500 max-w-xs">
        Grupo
        <select
          className="border rounded px-3 py-2 text-sm text-slate-900"
          value={grupo}
          onChange={(e) => cambiarGrupo(e.target.value)}
        >
          {grupos.map((g) => (
            <option key={g} value={g}>
              {g} ({partidas.filter((p) => p.familia === g).length})
            </option>
          ))}
        </select>
      </label>

      {grupo && (
        <>
          <form onSubmit={crearPartida} className="bg-white border rounded-lg p-4 space-y-3">
            <h2 className="font-medium text-sm">Añadir partida a «{grupo}»</h2>
            <div className="grid sm:grid-cols-3 gap-2 text-sm">
              <input
                required
                placeholder="Nombre de la partida"
                className="border rounded px-2 py-1.5 sm:col-span-2"
                value={nueva.nombre}
                onChange={(e) => setNueva({ ...nueva, nombre: e.target.value })}
              />
              <input
                required
                placeholder="Unidad (m, ud, h, día)"
                className="border rounded px-2 py-1.5"
                value={nueva.unidad}
                onChange={(e) => setNueva({ ...nueva, unidad: e.target.value })}
              />
              {soloPrecio ? (
                <label className="flex flex-col gap-0.5 text-xs text-slate-500 sm:col-span-3">
                  Precio de venta por unidad (€)
                  <input
                    type="number" min={0} step="0.01"
                    className="border rounded px-2 py-1 text-sm text-slate-900"
                    value={nueva.precio_venta_directo}
                    onChange={(e) => setNueva({ ...nueva, precio_venta_directo: e.target.value })}
                  />
                </label>
              ) : (
                <>
                  <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                    Coste MO (€)
                    <input
                      type="number" min={0} step="0.01"
                      className="border rounded px-2 py-1 text-sm text-slate-900"
                      value={nueva.precio_coste_mo}
                      onChange={(e) => setNueva({ ...nueva, precio_coste_mo: e.target.value })}
                    />
                  </label>
                  <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                    Material (€)
                    <input
                      type="number" min={0} step="0.01"
                      className="border rounded px-2 py-1 text-sm text-slate-900"
                      value={nueva.precio_material}
                      onChange={(e) => setNueva({ ...nueva, precio_material: e.target.value })}
                    />
                  </label>
                  <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                    Medios aux. (€)
                    <input
                      type="number" min={0} step="0.01"
                      className="border rounded px-2 py-1 text-sm text-slate-900"
                      value={nueva.precio_medios_aux}
                      onChange={(e) => setNueva({ ...nueva, precio_medios_aux: e.target.value })}
                    />
                  </label>
                  <label className="flex flex-col gap-0.5 text-xs text-slate-500">
                    Margen (%)
                    <input
                      type="number" min={0} step="0.01"
                      className="border rounded px-2 py-1 text-sm text-slate-900"
                      value={nueva.margen_pct}
                      onChange={(e) => setNueva({ ...nueva, margen_pct: e.target.value })}
                    />
                  </label>
                </>
              )}
              <input
                placeholder="Observaciones (opcional)"
                className="border rounded px-2 py-1.5 sm:col-span-3"
                value={nueva.observaciones}
                onChange={(e) => setNueva({ ...nueva, observaciones: e.target.value })}
              />
            </div>
            <label className="flex items-center gap-2 text-xs text-slate-600">
              <input type="checkbox" checked={soloPrecio} onChange={(e) => setSoloPrecio(e.target.checked)} />
              Conozco solo el precio de venta (sin desglosar coste y margen)
            </label>
            <p className="text-xs text-slate-400">
              {soloPrecio
                ? `Precio de venta: ${ventaNueva.toFixed(2)} € (se guarda sin margen añadido).`
                : `Coste directo: ${costeNueva.toFixed(2)} € · Precio de venta: ${ventaNueva.toFixed(2)} €`}
            </p>
            <button disabled={creando} className="bg-slate-900 text-white rounded py-1.5 px-4 text-sm disabled:opacity-50">
              {creando ? "Añadiendo..." : "Añadir partida"}
            </button>
          </form>

          <div className="bg-white border rounded-lg overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="text-left p-2">Partida</th>
                  <th className="text-left p-2">Unidad</th>
                  <th className="text-right p-2">MO</th>
                  <th className="text-right p-2">Material</th>
                  <th className="text-right p-2">Medios aux.</th>
                  <th className="text-right p-2">Coste directo</th>
                  <th className="text-right p-2">Margen %</th>
                  <th className="text-right p-2">Precio venta</th>
                  <th className="text-right p-2"></th>
                </tr>
              </thead>
              <tbody>
                {partidasDelGrupo.map((p) => {
                  const enEdicion = editandoId === p.id;
                  return (
                    <tr key={p.id} className={`border-t ${!p.activo ? "opacity-50" : ""}`}>
                      {enEdicion ? (
                        <>
                          <td className="p-1"><input className="border rounded px-1 py-0.5 w-44" value={edicion.nombre} onChange={(e) => setEdicion({ ...edicion, nombre: e.target.value })} /></td>
                          <td className="p-1"><input className="border rounded px-1 py-0.5 w-14" value={edicion.unidad} onChange={(e) => setEdicion({ ...edicion, unidad: e.target.value })} /></td>
                          <td className="p-1"><input type="number" step="0.01" className="border rounded px-1 py-0.5 w-20 text-right" value={edicion.precio_coste_mo} onChange={(e) => setEdicion({ ...edicion, precio_coste_mo: e.target.value })} /></td>
                          <td className="p-1"><input type="number" step="0.01" className="border rounded px-1 py-0.5 w-20 text-right" value={edicion.precio_material} onChange={(e) => setEdicion({ ...edicion, precio_material: e.target.value })} /></td>
                          <td className="p-1"><input type="number" step="0.01" className="border rounded px-1 py-0.5 w-20 text-right" value={edicion.precio_medios_aux} onChange={(e) => setEdicion({ ...edicion, precio_medios_aux: e.target.value })} /></td>
                          <td className="p-1 text-right text-slate-500">
                            {costeDirecto(edicion.precio_coste_mo, edicion.precio_material, edicion.precio_medios_aux).toFixed(2)}
                          </td>
                          <td className="p-1"><input type="number" step="0.01" className="border rounded px-1 py-0.5 w-16 text-right" value={edicion.margen_pct} onChange={(e) => setEdicion({ ...edicion, margen_pct: e.target.value })} /></td>
                          <td className="p-1 text-right text-slate-500">
                            {precioVenta(costeDirecto(edicion.precio_coste_mo, edicion.precio_material, edicion.precio_medios_aux), edicion.margen_pct).toFixed(2)}
                          </td>
                          <td className="p-1 text-right whitespace-nowrap">
                            <button onClick={() => guardarEdicion(p.id)} className="text-blue-600 underline text-xs mr-2">Guardar</button>
                            <button onClick={() => setEditandoId(null)} className="text-slate-500 underline text-xs">Cancelar</button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td className="p-2">
                            {p.nombre}
                            {!p.activo && <span className="ml-2 text-xs text-slate-400">(desactivada)</span>}
                            {p.observaciones && <div className="text-xs text-slate-400">{p.observaciones}</div>}
                          </td>
                          <td className="p-2">{p.unidad}</td>
                          <td className="p-2 text-right">{Number(p.precio_coste_mo).toFixed(2)}</td>
                          <td className="p-2 text-right">{Number(p.precio_material).toFixed(2)}</td>
                          <td className="p-2 text-right">{Number(p.precio_medios_aux).toFixed(2)}</td>
                          <td className="p-2 text-right">{Number(p.coste_directo).toFixed(2)}</td>
                          <td className="p-2 text-right">{Number(p.margen_pct).toFixed(2)}%</td>
                          <td className="p-2 text-right font-medium">{Number(p.precio_venta).toFixed(2)}</td>
                          <td className="p-2 text-right whitespace-nowrap">
                            <button onClick={() => empezarEdicion(p)} className="text-blue-600 underline text-xs mr-2">Modificar</button>
                            <button onClick={() => alternarActivo(p)} className="text-slate-500 underline text-xs">
                              {p.activo ? "Desactivar" : "Activar"}
                            </button>
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
