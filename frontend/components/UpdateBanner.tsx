"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { BUILD } from "@/lib/version";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const INTERVALO_COMPROBACION_MS = 5 * 60 * 1000;

/**
 * Icono en el menú (junto al de cambio de tema) para forzar una
 * actualización manualmente cuando haga falta. Además, compara el build
 * con el que se compiló este frontend contra el que está sirviendo el
 * backend ahora mismo (el health check ya lo expone) para resaltarlo
 * cuando sabemos que hay una versión más nueva — backend y frontend se
 * despliegan juntos con el mismo número de build en este proyecto.
 */
export default function UpdateBanner() {
  const [actualizacionDisponible, setActualizacionDisponible] = useState(false);
  const [actualizando, setActualizando] = useState(false);

  useEffect(() => {
    let cancelado = false;

    async function comprobar() {
      try {
        const res = await fetch(`${API_URL}/health`);
        if (!res.ok) return;
        const datos = await res.json();
        if (!cancelado && datos.build && String(datos.build) !== BUILD) {
          setActualizacionDisponible(true);
        }
      } catch {
        // Sin conexión o backend caído: no molestar con el aviso.
      }
    }

    comprobar();
    const intervalo = window.setInterval(comprobar, INTERVALO_COMPROBACION_MS);
    function alVolverAPrimerPlano() {
      if (document.visibilityState === "visible") comprobar();
    }
    document.addEventListener("visibilitychange", alVolverAPrimerPlano);

    return () => {
      cancelado = true;
      window.clearInterval(intervalo);
      document.removeEventListener("visibilitychange", alVolverAPrimerPlano);
    };
  }, []);

  async function actualizarAhora() {
    setActualizando(true);
    try {
      // Fuerza a que el service worker compruebe si hay una versión nueva de
      // sí mismo y vacía la caché de datos/páginas, para no quedarse con
      // nada guardado de antes al recargar.
      if ("serviceWorker" in navigator) {
        const registros = await navigator.serviceWorker.getRegistrations();
        await Promise.all(registros.map((r) => r.update().catch(() => {})));
      }
      if ("caches" in window) {
        const claves = await caches.keys();
        await Promise.all(claves.map((clave) => caches.delete(clave)));
      }
    } finally {
      window.location.reload();
    }
  }

  return (
    <button
      onClick={actualizarAhora}
      disabled={actualizando}
      title={actualizacionDisponible ? "Hay una versión nueva disponible — actualizar" : "Forzar actualización de la app"}
      className={`p-2 rounded hover:bg-slate-100 shrink-0 disabled:opacity-60 relative ${
        actualizacionDisponible ? "text-amber-600" : "text-slate-500"
      }`}
    >
      <RefreshCw size={16} className={actualizando ? "animate-spin" : ""} />
      {actualizacionDisponible && !actualizando && (
        <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-amber-500 rounded-full" />
      )}
    </button>
  );
}
