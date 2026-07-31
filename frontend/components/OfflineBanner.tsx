"use client";

import { useEffect, useState } from "react";

export default function OfflineBanner() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    setOffline(!navigator.onLine);
    const marcarOnline = () => setOffline(false);
    const marcarOffline = () => setOffline(true);
    window.addEventListener("online", marcarOnline);
    window.addEventListener("offline", marcarOffline);
    return () => {
      window.removeEventListener("online", marcarOnline);
      window.removeEventListener("offline", marcarOffline);
    };
  }, []);

  if (!offline) return null;

  return (
    <div className="bg-amber-100 text-amber-900 text-sm text-center py-1.5 px-4">
      Sin conexión — mostrando los últimos datos guardados. No se pueden crear ni guardar cambios hasta
      volver a tener internet.
    </div>
  );
}
