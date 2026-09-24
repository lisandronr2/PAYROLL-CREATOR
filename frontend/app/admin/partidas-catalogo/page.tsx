"use client";

import { useEffect, useState } from "react";
import RequireAuth from "@/components/RequireAuth";
import { api, PartidaCatalogo } from "@/lib/api";

export default function PartidasCatalogoPage() {
  return (
    <RequireAuth soloAdmin>
      <Contenido />
    </RequireAuth>
  );
}

const partidaVacia = {
  familia: "",
  nombre: "",
  unidad: "ud",
  precio_coste_mo: "0",
  precio_material: "0",
  precio_medios_aux: "0",
  margen_pct: "20",
  observaciones: "",
};

function Contenido() {
  const [partidas, setPartidas] = useState<PartidaCatalogo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mostrarInactivas, setMostrarInactivas] = useState(false);
  const [nueva, setNueva] = useState({ ...partidaVacia });
  const [creando, setCreando] = useState(false);
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [edicion, setEdicion] = useState<Record<string, string>>({});

  function cargar() {
    api.partidasCatalogo
      .listar(!mostrarInactivas)
      .then(setPartidas)
      .catch((e) => setError(String(e)));
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mostrarInactivas]);

  function costeDirectoPreview(mo: string, mat: string, medios: string) {
    return (Number(mo) || 0) + (Number(mat) || 0) + (Number(medios) || 0);
  }

  function precioVentaPreview(costeDirecto: number, margen: string) {
    return costeDirecto * (1 + (Number(margen) || 0) / 100);
  }

  async function crearPartida(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreando(true);
    try {
      await api.partidasCatalogo.crear({
        familia: nueva.familia,
        nombre: nueva.nombre,
        unidad: nueva.unidad,
        precio_coste_mo: nueva.precio_coste_mo,
        precio_material: nueva.precio_material,
        precio_medios_aux: nueva.precio_medios_aux,
        margen_pct: nueva.margen_pct,
        observaciones: nueva.observaciones || null,
      });
      setNueva({ ...partidaVacia });
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
      familia: p.familia,
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
        familia: edicion.familia,
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

  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">Catálogo de partidas</h1>
      <p className="text-sm text-slate-500 mb-4">
        Precios por partida (mano de obra + material + medios auxiliares) usados en "Presupuesto por
        items". El precio de venta ya incluye el margen — es el importe final que se factura por unidad.
      </p>

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      <form onSubmit={crearPartida} className="bg-white border rounded-lg p-4 mb-6 space-y-3">
        <h2 className="font-medium text-sm">Añadir partida nueva</h2>
        <div className="grid sm:grid-cols-3 gap-2 text-sm">
          <input
            required
            placeholder="Familia (ej. CCTV)"
            className="border rounded px-2 py-1.5"
            value={nueva.familia}
            onChange={(e) => setNueva({ ...nueva, familia: e.target.value })}
          />
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
          <label className="flex flex-col gap-0.5 text-xs text-slate-500">
            Coste MO (€)
            <input
              type="number" min={0} step="0.01"
              className="border rounded px-2 py-1"
              value={nueva.precio_coste_mo}
              onChange={(e) => setNueva({ ...nueva, precio_coste_mo: e.target.value })}
            />
          </label>
          <label className="flex flex-col gap-0.5 text-xs text-slate-500">
            Material (€)
            <input
              type="number" min={0} step="0.01"
              className="border rounded px-2 py-1"
              value={nueva.precio_material}
              onChange={(e) => setNueva({ ...nueva, precio_material: e.target.value })}
            />
          </label>
          <label className="flex flex-col gap-0.5 text-xs text-slate-500">
            Medios aux. (€)
            <input
              type="number" min={0} step="0.01"
              className="border rounded px-2 py-1"
              value={nueva.precio_medios_aux}
              onChange={(e) => setNueva({ ...nueva, precio_medios_aux: e.target.value })}
            />
          </label>
          <label className="flex flex-col gap-0.5 text-xs text-slate-500">
            Margen (%)
            <input
              type="number" min={0} step="0.01"
              className="border rounded px-2 py-1"
              value={nueva.margen_pct}
              onChange={(e) => setNueva({ ...nueva, margen_pct: e.target.value })}
            />
          </label>
          <input
            placeholder="Observaciones (opcional)"
            className="border rounded px-2 py-1.5 sm:col-span-2"
            value={nueva.observaciones}
            onChange={(e) => setNueva({ ...nueva, observaciones: e.target.value })}
          />
        </div>
        <p className="text-xs text-slate-400">
          Coste directo: {costeDirectoPreview(nueva.precio_coste_mo, nueva.precio_material, nueva.precio_medios_aux).toFixed(2)} € ·
          Precio de venta: {precioVentaPreview(costeDirectoPreview(nueva.precio_coste_mo, nueva.precio_material, nueva.precio_medios_aux), nueva.margen_pct).toFixed(2)} €
        </p>
        <button disabled={creando} className="bg-slate-900 text-white rounded py-1.5 px-4 text-sm disabled:opacity-50">
          {creando ? "Añadiendo..." : "Añadir partida"}
        </button>
      </form>

      <label className="flex items-center gap-2 text-sm mb-2">
        <input type="checkbox" checked={mostrarInactivas} onChange={(e) => setMostrarInactivas(e.target.checked)} />
        Mostrar también partidas desactivadas
      </label>

      <div className="bg-white border rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-2">Familia</th>
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
            {partidas.map((p) => {
              const enEdicion = editandoId === p.id;
              return (
                <tr key={p.id} className={`border-t ${!p.activo ? "opacity-50" : ""}`}>
                  {enEdicion ? (
                    <>
                      <td className="p-1"><input className="border rounded px-1 py-0.5 w-24" value={edicion.familia} onChange={(e) => setEdicion({ ...edicion, familia: e.target.value })} /></td>
                      <td className="p-1"><input className="border rounded px-1 py-0.5 w-40" value={edicion.nombre} onChange={(e) => setEdicion({ ...edicion, nombre: e.target.value })} /></td>
                      <td className="p-1"><input className="border rounded px-1 py-0.5 w-14" value={edicion.unidad} onChange={(e) => setEdicion({ ...edicion, unidad: e.target.value })} /></td>
                      <td className="p-1"><input type="number" step="0.01" className="border rounded px-1 py-0.5 w-20 text-right" value={edicion.precio_coste_mo} onChange={(e) => setEdicion({ ...edicion, precio_coste_mo: e.target.value })} /></td>
                      <td className="p-1"><input type="number" step="0.01" className="border rounded px-1 py-0.5 w-20 text-right" value={edicion.precio_material} onChange={(e) => setEdicion({ ...edicion, precio_material: e.target.value })} /></td>
                      <td className="p-1"><input type="number" step="0.01" className="border rounded px-1 py-0.5 w-20 text-right" value={edicion.precio_medios_aux} onChange={(e) => setEdicion({ ...edicion, precio_medios_aux: e.target.value })} /></td>
                      <td className="p-1 text-right text-slate-500">
                        {costeDirectoPreview(edicion.precio_coste_mo, edicion.precio_material, edicion.precio_medios_aux).toFixed(2)}
                      </td>
                      <td className="p-1"><input type="number" step="0.01" className="border rounded px-1 py-0.5 w-16 text-right" value={edicion.margen_pct} onChange={(e) => setEdicion({ ...edicion, margen_pct: e.target.value })} /></td>
                      <td className="p-1 text-right text-slate-500">
                        {precioVentaPreview(costeDirectoPreview(edicion.precio_coste_mo, edicion.precio_material, edicion.precio_medios_aux), edicion.margen_pct).toFixed(2)}
                      </td>
                      <td className="p-1 text-right whitespace-nowrap">
                        <button onClick={() => guardarEdicion(p.id)} className="text-blue-600 underline text-xs mr-2">Guardar</button>
                        <button onClick={() => setEditandoId(null)} className="text-slate-500 underline text-xs">Cancelar</button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="p-2">{p.familia}</td>
                      <td className="p-2">{p.nombre}</td>
                      <td className="p-2">{p.unidad}</td>
                      <td className="p-2 text-right">{Number(p.precio_coste_mo).toFixed(2)}</td>
                      <td className="p-2 text-right">{Number(p.precio_material).toFixed(2)}</td>
                      <td className="p-2 text-right">{Number(p.precio_medios_aux).toFixed(2)}</td>
                      <td className="p-2 text-right">{Number(p.coste_directo).toFixed(2)}</td>
                      <td className="p-2 text-right">{Number(p.margen_pct).toFixed(2)}%</td>
                      <td className="p-2 text-right font-medium">{Number(p.precio_venta).toFixed(2)}</td>
                      <td className="p-2 text-right whitespace-nowrap">
                        <button onClick={() => empezarEdicion(p)} className="text-blue-600 underline text-xs mr-2">Editar</button>
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
    </div>
  );
}
