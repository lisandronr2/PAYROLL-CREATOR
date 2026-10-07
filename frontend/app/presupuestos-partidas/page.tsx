"use client";

import RequireAuth from "@/components/RequireAuth";
import CatalogoPartidas from "@/components/CatalogoPartidas";

export default function PresupuestosPartidasPage() {
  return (
    <RequireAuth soloAdmin>
      <CatalogoPartidas />
    </RequireAuth>
  );
}
