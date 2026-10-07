"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Printer } from "lucide-react";
import { api, LiquidacionGuardada } from "@/lib/api";
import ResultadoLiquidacion from "@/components/ResultadoLiquidacion";

export default function DetalleLiquidacionPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [liquidacion, setLiquidacion] = useState<LiquidacionGuardada | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [eliminando, setEliminando] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.liquidaciones
      .obtener(id)
      .then(setLiquidacion)
      .catch((e) => setError(String(e)));
  }, [id]);

  async function verPdf(tipo: "trabajador" | "interno") {
    setError(null);
    try {
      await api.liquidaciones.verPdf(id, tipo, `liquidacion_${id}_${tipo}.pdf`);
    } catch (err) {
      setError(String(err));
    }
  }

  async function eliminar() {
    if (!liquidacion) return;
    const confirmado = window.confirm(
      `¿Eliminar la liquidación de ${liquidacion.trabajador_nombre}? No se puede deshacer.`
    );
    if (!confirmado) return;
    setEliminando(true);
    try {
      await api.liquidaciones.eliminar(id);
      router.push("/nominas/liquidacion");
    } catch (err) {
      setError(String(err));
      setEliminando(false);
    }
  }

  if (error && !liquidacion) return <p className="text-red-600 text-sm">{error}</p>;
  if (!liquidacion) return <p className="text-sm text-slate-500">Cargando...</p>;

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex justify-between items-center">
        <button onClick={() => router.push("/nominas/liquidacion")} className="text-sm text-slate-500 hover:underline">
          ← Volver a liquidaciones
        </button>
        <div className="flex gap-2 flex-wrap">
          <Link href={`/nominas/liquidacion?editar=${liquidacion.id}`} className="text-sm bg-white border px-3 py-1.5 rounded">
            Editar
          </Link>
          <button
            onClick={() => verPdf("trabajador")}
            className="text-sm bg-slate-900 text-white px-3 py-1.5 rounded flex items-center gap-1.5"
            title="Ver / imprimir el PDF para entregar al trabajador"
          >
            <Printer size={14} />
            Ver PDF (trabajador)
          </button>
          <button onClick={() => verPdf("interno")} className="text-sm bg-white border px-3 py-1.5 rounded">
            Ver PDF (interno)
          </button>
          <button
            onClick={eliminar}
            disabled={eliminando}
            className="text-sm text-red-600 border border-red-200 px-3 py-1.5 rounded disabled:opacity-50"
          >
            {eliminando ? "Eliminando..." : "Eliminar"}
          </button>
        </div>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <div className="bg-white border rounded-lg p-4">
        <ResultadoLiquidacion resultado={liquidacion} notas={liquidacion.notas} />
      </div>
    </div>
  );
}
