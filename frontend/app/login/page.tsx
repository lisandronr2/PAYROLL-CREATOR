"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import ThemeSwitcher from "@/components/ThemeSwitcher";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await login(email, password);
      router.push("/");
    } catch {
      setError("Email o contraseña incorrectos.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="flex justify-end mb-2">
        <ThemeSwitcher />
      </div>
      <h1 className="text-xl font-semibold mb-4 text-center">PAYROLL CREATOR</h1>
      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-6 space-y-3">
        <input
          required
          type="email"
          placeholder="Email"
          className="w-full border rounded px-3 py-2"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          required
          type="password"
          placeholder="Contraseña"
          className="w-full border rounded px-3 py-2"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button disabled={cargando} className="w-full bg-slate-900 text-white rounded py-2 disabled:opacity-50">
          {cargando ? "Entrando..." : "Entrar"}
        </button>
        <div className="text-center">
          <Link href="/recuperar-password" className="text-sm text-slate-500 hover:underline">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>
      </form>
    </div>
  );
}
