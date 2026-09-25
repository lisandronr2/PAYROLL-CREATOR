"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Printer } from "lucide-react";
import { api, Empresa, PresupuestoItems } from "@/lib/api";

export default function DetallePresupuestoItemsPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [presupuesto, setPresupuesto] = useState<PresupuestoItems | null>(null);
  const [empresa, setEmpresa] = useState<Empresa | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [eliminando, setEliminando] = useState(false);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const p = await api.presupuestosItems.obtener(id);
        setPresupuesto(p);
        const e = await api.empresas.obtener(p.empresa_id);
        setEmpresa(e);
      } catch (err) {
        setError(String(err));
      }
    })();
  }, [id]);

  async function eliminar() {
    if (!presupuesto) return;
    const confirmado = window.confirm(`¿Eliminar el presupuesto "${presupuesto.nombre}"? No se puede deshacer.`);
    if (!confirmado) return;
    setEliminando(true);
    try {
      await api.presupuestosItems.eliminar(presupuesto.id);
      router.push("/presupuestos-items");
    } catch (err) {
      setError(String(err));
      setEliminando(false);
    }
  }

  if (error) return <p className="text-red-600 text-sm">{error}</p>;
  if (!presupuesto) return <p className="text-sm text-slate-500">Cargando...</p>;

  const hayDescuentos = presupuesto.lineas.some((l) => Number(l.descuento_pct) > 0);

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex justify-between items-center">
        <button onClick={() => router.push("/presupuestos-items")} className="text-sm text-slate-500 hover:underline">
          ← Volver a presupuestos por items
        </button>
        <div className="flex gap-2 flex-wrap">
          <Link
            href={`/presupuestos-items?editar=${presupuesto.id}`}
            className="text-sm bg-white border px-3 py-1.5 rounded"
          >
            Editar
          </Link>
          <button
            onClick={() => api.presupuestosItems.verPdf(presupuesto.id, "cliente", `presupuesto_items_${presupuesto.id}_cliente.pdf`)}
            className="text-sm bg-slate-900 text-white px-3 py-1.5 rounded flex items-center gap-1.5"
            title="Ver / imprimir PDF para el cliente"
          >
            <Printer size={14} />
            Ver PDF (cliente)
          </button>
          <button
            onClick={() => api.presupuestosItems.verPdf(presupuesto.id, "interno", `presupuesto_items_${presupuesto.id}_interno.pdf`)}
            className="text-sm bg-white border px-3 py-1.5 rounded"
          >
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

      <div className="bg-white border rounded-lg p-4 space-y-4">
        <div>
          <h1 className="text-xl font-semibold">{presupuesto.nombre}</h1>
          <p className="text-sm text-slate-500">
            {empresa?.razon_social} · Fecha: {presupuesto.fecha}
          </p>
          {presupuesto.cliente_nombre && (
            <p className="text-sm text-slate-500">
              Cliente: {presupuesto.cliente_nombre} {presupuesto.cliente_nif ? `(${presupuesto.cliente_nif})` : ""}
            </p>
          )}
        </div>

        <section>
          <h2 className="text-sm font-semibold text-slate-600 mb-1">Partidas</h2>
          <table className="w-full text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left p-1.5">Familia</th>
                <th className="text-left p-1.5">Partida</th>
                <th className="text-right p-1.5">Unidad</th>
                <th className="text-right p-1.5">Cantidad</th>
                <th className="text-right p-1.5">Precio unit.</th>
                {hayDescuentos && <th className="text-right p-1.5">Descuento</th>}
                <th className="text-right p-1.5">Importe</th>
              </tr>
            </thead>
            <tbody>
              {presupuesto.lineas.map((l, i) => (
                <tr key={i} className="border-t">
                  <td className="p-1.5">{l.familia}</td>
                  <td className="p-1.5">{l.nombre}</td>
                  <td className="p-1.5 text-right">{l.unidad}</td>
                  <td className="p-1.5 text-right">{Number(l.cantidad).toFixed(2)}</td>
                  <td className="p-1.5 text-right">{Number(l.precio_unitario).toFixed(2)} €</td>
                  {hayDescuentos && (
                    <td className="p-1.5 text-right">
                      {Number(l.descuento_pct) > 0 ? `${Number(l.descuento_pct).toFixed(2)}%` : "-"}
                    </td>
                  )}
                  <td className="p-1.5 text-right">{Number(l.importe).toFixed(2)} €</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="border-t pt-3 grid gap-1 text-sm">
          <div>Subtotal: <strong>{Number(presupuesto.subtotal).toFixed(2)} €</strong></div>
          {Number(presupuesto.iva_pct) > 0 && (
            <div>IVA ({Number(presupuesto.iva_pct).toFixed(2)}%): <strong>{Number(presupuesto.iva_importe).toFixed(2)} €</strong></div>
          )}
          <div className="text-base border-t pt-1 mt-1">
            TOTAL{Number(presupuesto.iva_pct) === 0 ? " (IVA no incluido)" : ""}:{" "}
            <strong>{Number(presupuesto.precio_total_cliente).toFixed(2)} €</strong>
          </div>
        </section>

        {presupuesto.notas && (
          <section className="border-t pt-3 text-sm">
            <h2 className="text-sm font-semibold text-slate-600 mb-1">Notas</h2>
            <p className="text-slate-600 whitespace-pre-wrap">{presupuesto.notas}</p>
          </section>
        )}
      </div>
    </div>
  );
}
