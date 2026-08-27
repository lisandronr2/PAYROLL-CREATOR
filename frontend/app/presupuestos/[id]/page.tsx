"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, CategoriaProfesional, Convenio, Empresa, Presupuesto } from "@/lib/api";

export default function DetallePresupuestoPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [presupuesto, setPresupuesto] = useState<Presupuesto | null>(null);
  const [empresa, setEmpresa] = useState<Empresa | null>(null);
  const [convenio, setConvenio] = useState<Convenio | null>(null);
  const [categorias, setCategorias] = useState<CategoriaProfesional[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [eliminando, setEliminando] = useState(false);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const p = await api.presupuestos.obtener(id);
        setPresupuesto(p);
        const [e, c] = await Promise.all([api.empresas.obtener(p.empresa_id), api.convenios.categorias(p.convenio_id)]);
        setEmpresa(e);
        setCategorias(c);
        const convenios = await api.convenios.listar();
        setConvenio(convenios.find((x) => x.id === p.convenio_id) ?? null);
      } catch (err) {
        setError(String(err));
      }
    })();
  }, [id]);

  function nombreCategoria(categoriaId: number) {
    const c = categorias.find((x) => x.id === categoriaId);
    return c ? `${c.grupo} — ${c.nombre}` : `#${categoriaId}`;
  }

  async function eliminar() {
    if (!presupuesto) return;
    const confirmado = window.confirm(`¿Eliminar el presupuesto "${presupuesto.nombre}"? No se puede deshacer.`);
    if (!confirmado) return;
    setEliminando(true);
    try {
      await api.presupuestos.eliminar(presupuesto.id);
      router.push("/presupuestos");
    } catch (err) {
      setError(String(err));
      setEliminando(false);
    }
  }

  if (error) return <p className="text-red-600 text-sm">{error}</p>;
  if (!presupuesto) return <p className="text-sm text-slate-500">Cargando...</p>;

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex justify-between items-center">
        <button onClick={() => router.push("/presupuestos")} className="text-sm text-slate-500 hover:underline">
          ← Volver a presupuestos
        </button>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => api.presupuestos.verPdf(presupuesto.id, "cliente", `presupuesto_${presupuesto.id}_cliente.pdf`)}
            className="text-sm bg-slate-900 text-white px-3 py-1.5 rounded"
          >
            Ver PDF (cliente)
          </button>
          <button
            onClick={() => api.presupuestos.verPdf(presupuesto.id, "interno", `presupuesto_${presupuesto.id}_interno.pdf`)}
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
            {empresa?.razon_social} · Convenio: {convenio?.nombre} · Fecha: {presupuesto.fecha}
          </p>
          {presupuesto.cliente_nombre && (
            <p className="text-sm text-slate-500">
              Cliente: {presupuesto.cliente_nombre} {presupuesto.cliente_nif ? `(${presupuesto.cliente_nif})` : ""}
            </p>
          )}
        </div>

        <section>
          <h2 className="text-sm font-semibold text-slate-600 mb-1">Personal</h2>
          <table className="w-full text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left p-1.5">Categoría</th>
                <th className="text-right p-1.5">Personas</th>
                <th className="text-right p-1.5">Días</th>
                <th className="text-right p-1.5">Jornada</th>
                <th className="text-right p-1.5">Coste unitario</th>
                <th className="text-right p-1.5">Coste total</th>
              </tr>
            </thead>
            <tbody>
              {presupuesto.lineas_personal.map((l, i) => (
                <tr key={i} className="border-t">
                  <td className="p-1.5">{nombreCategoria(l.categoria_id)}</td>
                  <td className="p-1.5 text-right">{l.cantidad_personas}</td>
                  <td className="p-1.5 text-right">{Number(l.dias_dedicacion).toFixed(0)}</td>
                  <td className="p-1.5 text-right">{Number(l.jornada_porcentaje).toFixed(0)}%</td>
                  <td className="p-1.5 text-right">{Number(l.coste_unitario).toFixed(2)} €</td>
                  <td className="p-1.5 text-right">{Number(l.coste_total_linea).toFixed(2)} €</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {presupuesto.lineas_otros.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold text-slate-600 mb-1">Materiales y otros costes</h2>
            <table className="w-full text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="text-left p-1.5">Concepto</th>
                  <th className="text-right p-1.5">Cantidad</th>
                  <th className="text-right p-1.5">Precio unitario</th>
                  <th className="text-right p-1.5">Importe</th>
                </tr>
              </thead>
              <tbody>
                {presupuesto.lineas_otros.map((l, i) => (
                  <tr key={i} className="border-t">
                    <td className="p-1.5">{l.concepto}</td>
                    <td className="p-1.5 text-right">{Number(l.cantidad).toFixed(2)}</td>
                    <td className="p-1.5 text-right">{Number(l.precio_unitario).toFixed(2)} €</td>
                    <td className="p-1.5 text-right">{Number(l.importe).toFixed(2)} €</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        <section className="border-t pt-3 grid sm:grid-cols-2 gap-1 text-sm">
          <div>Coste directo — personal: <strong>{Number(presupuesto.coste_directo_personal).toFixed(2)} €</strong></div>
          <div>Coste directo — materiales/otros: <strong>{Number(presupuesto.coste_directo_otros).toFixed(2)} €</strong></div>
          <div>Coste directo total: <strong>{Number(presupuesto.coste_directo_total).toFixed(2)} €</strong></div>
          <div>Gastos generales ({Number(presupuesto.gastos_generales_pct).toFixed(2)}%): <strong>{Number(presupuesto.gastos_generales_importe).toFixed(2)} €</strong></div>
          <div>Coste total: <strong>{Number(presupuesto.coste_total).toFixed(2)} €</strong></div>
          <div>Margen de beneficio ({Number(presupuesto.margen_beneficio_pct).toFixed(2)}%): <strong>{Number(presupuesto.margen_importe).toFixed(2)} €</strong></div>
          <div>Precio de venta (sin IVA): <strong>{Number(presupuesto.precio_venta).toFixed(2)} €</strong></div>
          <div>IVA ({Number(presupuesto.iva_pct).toFixed(2)}%): <strong>{Number(presupuesto.iva_importe).toFixed(2)} €</strong></div>
          <div className="text-base sm:col-span-2">
            Precio total al cliente: <strong>{Number(presupuesto.precio_total_cliente).toFixed(2)} €</strong>
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
