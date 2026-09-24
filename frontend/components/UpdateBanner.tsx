"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { BUILD } from "@/lib/version";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const INTERVALO_COMPROBACION_MS = 5 * 60 * 1000;

/**
 * Compara el build con el que se compiló este frontend contra el build que
 * está sirviendo el backend en este momento (el health check ya lo expone).
 * Backend y frontend se despliegan juntos con el mismo número de build en
 * este proyecto, así que un backend con un build distinto es la señal más
 * fiable de que hay una versión nueva — no depende de que el propio
 * service worker cambie de bytes, que con despliegues normales no ocurre.
 */
export default function UpdateBanner() {
  const [actualizacionDisponible, setActualizacionDisponible] = useState(false);

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

  if (!actualizacionDisponible) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 bg-slate-900 text-white rounded-lg shadow-lg px-4 py-3 flex items-center gap-3 text-sm max-w-xs">
      <span>Hay una nueva versión de la aplicación disponible.</span>
      <button
        onClick={() => window.location.reload()}
        className="bg-white text-slate-900 rounded px-3 py-1.5 font-medium flex items-center gap-1.5 shrink-0 whitespace-nowrap"
      >
        <RefreshCw size={14} />
        Actualizar
      </button>
    </div>
  );
}
