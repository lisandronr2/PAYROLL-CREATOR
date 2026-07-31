"use client";

import { useEffect } from "react";

export default function ServiceWorkerRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Si falla el registro (ej. navegador sin soporte), la app sigue
        // funcionando con conexión, solo sin caché offline.
      });
    }
  }, []);

  return null;
}
