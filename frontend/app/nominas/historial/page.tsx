"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Contrato, Nomina, Trabajador } from "@/lib/api";

export default function HistorialNominasPage() {
  const [nominas, setNominas] = useState<Nomina[]>([]);
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [eliminando, setEliminando] = useState<number | null>(null);

  function cargar() {
    Promise.all([api.nominas.listar(), api.contratos.listar(), api.trabajadores.listar()])
      .then(([n, c, t]) => {
        setNominas(n);
        setContratos(c);
        setTrabajadores(t);
      })
      .catch((e) => setError(String(e)));
  }

  useEffect(() => {
    cargar();
  }, []);

  function nombreTrabajador(contratoId: number) {
    const contrato = contratos.find((c) => c.id === contratoId);
    if (!contrato) return `Contrato #${contratoId}`;
    const t = trabajadores.find((x) => x.id === contrato.trabajador_id);
    return t ? `${t.nombre} ${t.apellidos}` : `Contrato #${contratoId}`;
  }

  async function eliminar(n: Nomina) {
    const confirmado = window.confirm(
      `¿Eliminar la nómina ${n.periodo_mes}/${n.periodo_anio} de ${nombreTrabajador(n.contrato_id)}? Esta acción no se puede deshacer.`
    );
    if (!confirmado) return;
    setEliminando(n.id);
    try {
      await api.nominas.eliminar(n.id);
      setNominas((prev) => prev.filter((x) => x.id !== n.id));
    } catch (err) {
      setError(String(err));
    } finally {
      setEliminando(null);
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Historial de nóminas</h1>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2">Trabajador</th>
            <th className="text-left p-2">Periodo</th>
            <th className="text-left p-2">Tipo</th>
            <th className="text-right p-2">Líquido</th>
            <th className="text-right p-2"></th>
          </tr>
        </thead>
        <tbody>
          {nominas.map((n) => (
            <tr key={n.id} className="border-t">
              <td className="p-2">{nombreTrabajador(n.contrato_id)}</td>
              <td className="p-2">
                {n.periodo_mes}/{n.periodo_anio}
              </td>
              <td className="p-2">{n.tipo}</td>
              <td className="p-2 text-right">{Number(n.liquido_a_percibir).toFixed(2)} €</td>
              <td className="p-2 text-right whitespace-nowrap space-x-3">
                <Link href={`/nominas/generar?editar=${n.id}`} className="text-blue-600 underline">
                  Ver / editar
                </Link>
                <button
                  onClick={() => api.nominas.verPdf(n.id, `nomina_${n.periodo_anio}_${n.periodo_mes}.pdf`)}
                  className="text-blue-600 underline"
                >
                  Ver PDF
                </button>
                <button
                  onClick={() => eliminar(n)}
                  disabled={eliminando === n.id}
                  className="text-red-600 underline disabled:opacity-50"
                >
                  {eliminando === n.id ? "Eliminando..." : "Eliminar"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
