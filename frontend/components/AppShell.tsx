"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import RequireAuth from "@/components/RequireAuth";

const NAV_ITEMS = [
  { href: "/empresas", label: "Empresas" },
  { href: "/trabajadores", label: "Trabajadores" },
  { href: "/contratos", label: "Contratos" },
  { href: "/convenios", label: "Convenios" },
  { href: "/nominas/generar", label: "Generar nómina" },
  { href: "/nominas/historial", label: "Historial" },
];

const ADMIN_ITEMS = [
  { href: "/admin/parametros", label: "Parámetros legales" },
  { href: "/admin/tabla-irpf", label: "Tabla IRPF" },
  { href: "/admin/convenios", label: "Convenios (editar)" },
  { href: "/admin/usuarios", label: "Usuarios" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { usuario, logout } = useAuth();

  if (pathname === "/login") {
    return <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">{children}</main>;
  }

  return (
    <RequireAuth>
      <header className="bg-slate-900 text-white">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between flex-wrap gap-2">
          <Link href="/" className="font-semibold text-lg">
            PAYROLL CREATOR
          </Link>
          <nav className="flex gap-4 text-sm flex-wrap items-center">
            {NAV_ITEMS.map((item) => (
              <Link key={item.href} href={item.href} className="hover:underline">
                {item.label}
              </Link>
            ))}
            {usuario?.rol === "admin" && (
              <div className="relative group">
                <span className="hover:underline cursor-pointer">Admin ▾</span>
                <div className="absolute right-0 hidden group-hover:block bg-white text-slate-900 rounded shadow-lg mt-1 min-w-[180px] z-10">
                  {ADMIN_ITEMS.map((item) => (
                    <Link key={item.href} href={item.href} className="block px-3 py-2 text-sm hover:bg-slate-100">
                      {item.label}
                    </Link>
                  ))}
                </div>
              </div>
            )}
            {usuario && (
              <span className="text-slate-300 text-xs">
                {usuario.nombre} ({usuario.rol})
              </span>
            )}
            <button onClick={logout} className="hover:underline">
              Salir
            </button>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">{children}</main>
      <footer className="text-center text-xs text-slate-500 py-4">
        Motor de cálculo MVP — valores legales orientativos, verificar con asesoría antes de uso real.
      </footer>
    </RequireAuth>
  );
}
