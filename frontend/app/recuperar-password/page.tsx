"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import ThemeSwitcher from "@/components/ThemeSwitcher";

export default function RecuperarPasswordPage() {
  const [email, setEmail] = useState("");
  const [enviado, setEnviado] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await api.auth.solicitarRecuperacion(email);
      setEnviado(true);
    } catch {
      setError("No se pudo procesar la solicitud. Inténtalo de nuevo.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="flex justify-end mb-2">
        <ThemeSwitcher />
      </div>
      <h1 className="text-xl font-semibold mb-4 text-center">Recuperar contraseña</h1>
      <div className="bg-white border rounded-lg p-6 space-y-3">
        {enviado ? (
          <>
            <p className="text-sm text-slate-600">
              Si ese correo existe en el sistema, te hemos enviado un enlace para elegir una nueva
              contraseña. Revisa tu bandeja de entrada (y la carpeta de spam).
            </p>
            <div className="text-center">
              <Link href="/login" className="text-sm text-slate-500 hover:underline">
                Volver a iniciar sesión
              </Link>
            </div>
          </>
        ) : (
          <form onSubmit={onSubmit} className="space-y-3">
            <p className="text-sm text-slate-600">
              Introduce el correo con el que inicias sesión y te enviaremos un enlace para
              restablecer tu contraseña.
            </p>
            <input
              required
              type="email"
              placeholder="Email"
              className="w-full border rounded px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            {error && <p className="text-red-600 text-sm">{error}</p>}
            <button
              disabled={cargando}
              className="w-full bg-slate-900 text-white rounded py-2 disabled:opacity-50"
            >
              {cargando ? "Enviando..." : "Enviar enlace de recuperación"}
            </button>
            <div className="text-center">
              <Link href="/login" className="text-sm text-slate-500 hover:underline">
                Volver a iniciar sesión
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
