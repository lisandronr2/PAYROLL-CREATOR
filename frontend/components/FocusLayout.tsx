"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import { FULL_VERSION } from "@/lib/version";

/**
 * Layout para las pantallas "de ejecución" (cualquier opción elegida en el
 * menú). Aquí el menú desaparece: solo queda una barra superior mínima
 * (marca, tema, salir) y, al final del contenido, el botón "Volver" que
 * retrocede en el historial página por página hasta llegar al inicio,
 * donde vuelve a verse el menú.
 */
export default function FocusLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { usuario, logout } = useAuth();

  return (
    <div className="flex min-h-screen w-full flex-col">
      <header className="bg-slate-900 text-white">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-2">
          <Link href="/" className="font-semibold text-base">
            PAYROLL CREATOR
          </Link>
          <div className="flex items-center gap-3">
            {usuario && (
              <span className="text-slate-300 text-xs hidden sm:inline">
                {usuario.nombre} ({usuario.rol})
              </span>
            )}
            <ThemeSwitcher />
            <button onClick={logout} className="text-sm hover:underline">
              Salir
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">{children}</main>

      <div className="max-w-5xl w-full mx-auto px-4 pb-6">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 border rounded-lg px-4 py-2 text-sm font-medium bg-white hover:bg-slate-100"
        >
          <ArrowLeft size={16} />
          Volver
        </button>
      </div>

      <footer className="text-center text-xs text-slate-500 py-4">
        Motor de cálculo MVP — valores legales orientativos, verificar con asesoría antes de uso real.
        <span className="block text-slate-400 mt-1">v{FULL_VERSION}</span>
      </footer>
    </div>
  );
}
