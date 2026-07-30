"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import ThemeSwitcher from "@/components/ThemeSwitcher";

function RestablecerPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [hecho, setHecho] = useState(false);
  const [cargando, setCargando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    if (password !== confirmar) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setCargando(true);
    try {
      await api.auth.restablecerPassword(token, password);
      setHecho(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch {
      setError("El enlace no es válido o ha caducado. Solicita uno nuevo.");
    } finally {
      setCargando(false);
    }
  }

  if (!token) {
    return (
      <p className="text-sm text-red-600">
        Falta el enlace de recuperación. Solicítalo de nuevo desde{" "}
        <Link href="/recuperar-password" className="underline">
          Recuperar contraseña
        </Link>
        .
      </p>
    );
  }

  if (hecho) {
    return (
      <p className="text-sm text-slate-600">
        Contraseña actualizada correctamente. Te llevamos a la pantalla de inicio de sesión...
      </p>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <p className="text-sm text-slate-600">Elige tu nueva contraseña (mínimo 8 caracteres).</p>
      <input
        required
        type="password"
        placeholder="Nueva contraseña"
        className="w-full border rounded px-3 py-2"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <input
        required
        type="password"
        placeholder="Confirmar nueva contraseña"
        className="w-full border rounded px-3 py-2"
        value={confirmar}
        onChange={(e) => setConfirmar(e.target.value)}
      />
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <button disabled={cargando} className="w-full bg-slate-900 text-white rounded py-2 disabled:opacity-50">
        {cargando ? "Guardando..." : "Cambiar contraseña"}
      </button>
    </form>
  );
}

export default function RestablecerPasswordPage() {
  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="flex justify-end mb-2">
        <ThemeSwitcher />
      </div>
      <h1 className="text-xl font-semibold mb-4 text-center">Nueva contraseña</h1>
      <div className="bg-white border rounded-lg p-6">
        <Suspense fallback={<p className="text-sm text-slate-500">Cargando...</p>}>
          <RestablecerPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}
