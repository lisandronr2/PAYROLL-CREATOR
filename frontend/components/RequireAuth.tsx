"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function RequireAuth({
  children,
  soloAdmin = false,
}: {
  children: React.ReactNode;
  soloAdmin?: boolean;
}) {
  const { usuario, cargando } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (cargando) return;
    if (!usuario) {
      router.replace("/login");
      return;
    }
    if (soloAdmin && usuario.rol !== "admin") {
      router.replace("/");
    }
  }, [usuario, cargando, soloAdmin, router, pathname]);

  if (cargando) return <p className="text-slate-500 text-sm">Cargando...</p>;
  if (!usuario) return null;
  if (soloAdmin && usuario.rol !== "admin") return null;

  return <>{children}</>;
}
