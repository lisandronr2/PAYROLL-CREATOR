"use client";

import { usePathname } from "next/navigation";
import RequireAuth from "@/components/RequireAuth";
import Sidebar from "@/components/Sidebar";
import FocusLayout from "@/components/FocusLayout";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (pathname === "/login") {
    return <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">{children}</main>;
  }

  const esInicio = pathname === "/";

  return (
    <RequireAuth>
      {esInicio ? (
        <Sidebar>
          <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">{children}</main>
          <footer className="text-center text-xs text-slate-500 py-4">
            Motor de cálculo MVP — valores legales orientativos, verificar con asesoría antes de uso real.
          </footer>
        </Sidebar>
      ) : (
        <FocusLayout>{children}</FocusLayout>
      )}
    </RequireAuth>
  );
}
