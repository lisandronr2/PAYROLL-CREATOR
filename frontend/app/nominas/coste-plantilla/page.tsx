"use client";

import { useEffect, useState } from "react";
import { api, CategoriaProfesional, CostePlantilla, Empresa } from "@/lib/api";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export default function CostePlantillaPage() {
  const hoy = new Date();

  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [categorias, setCategorias] = useState<CategoriaProfesional[]>([]);
  const [convenios, setConvenios] = useState<{ id: number; nombre: string }[]>([]);
  const [empresaId, setEmpresaId] = useState("");
  const [convenioId, setConvenioId] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [anio, setAnio] = useState(String(hoy.getFullYear()));
  const [mes, setMes] = useState(String(hoy.getMonth() + 1));
  const [festivosAdicionales, setFestivosAdicionales] = useState("0");

  const [numeroEmpleados, setNumeroEmpleados] = useState("1");
  const [horasExtraTotal, setHorasExtraTotal] = useState("0");
  const [combustible, setCombustible] = useState("0");
  const [alojamiento, setAlojamiento] = useState("0");
  const [dietas, setDietas] = useState("0");
  const [gastosVarios, setGastosVarios] = useState("0");

  const [resultado, setResultado] = useState<CostePlantilla | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    Promise.all([api.empresas.listar(), api.convenios.listar()])
      .then(([e, c]) => {
        setEmpresas(e);
        setConvenios(c);
      })
      .catch((err) => setError(String(err)));
  }, []);

  useEffect(() => {
    if (!convenioId) {
      setCategorias([]);
      setCategoriaId("");
      return;
    }
    api.convenios.categorias(Number(convenioId)).then(setCategorias);
  }, [convenioId]);

  async function calcular(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    setResultado(null);
    try {
      const r = await api.referencia.costePlantilla({
        empresa_id: Number(empresaId),
        categoria_id: Number(categoriaId),
        anio: Number(anio),
        mes: Number(mes),
        numero_empleados: Number(numeroEmpleados),
        festivos_adicionales: Number(festivosAdicionales) || 0,
        horas_extra_total: horasExtraTotal || "0",
        combustible: combustible || "0",
        alojamiento: alojamiento || "0",
        dietas: dietas || "0",
        gastos_varios: gastosVarios || "0",
      });
      setResultado(r);
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Coste de plantilla</h1>
        <p className="text-sm text-slate-500 mt-1">
          Coste real por empleado de un grupo de la misma categoría: parte del coste laboral individual
          (salario, horas extra repartidas y cotización empresarial a la Seguridad Social) según los días
          laborables reales del mes, y le suma la parte proporcional de los gastos del grupo (combustible,
          alojamiento, dietas, gastos varios) repartidos entre el número de empleados.
        </p>
      </div>

      <form onSubmit={calcular} className="bg-white border rounded-lg p-4 space-y-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <select required className="border rounded px-3 py-2" value={empresaId} onChange={(e) => setEmpresaId(e.target.value)}>
            <option value="">Empresa (para el tipo AT/EP)...</option>
            {empresas.map((e) => (
              <option key={e.id} value={e.id}>{e.razon_social}</option>
            ))}
          </select>
          <select required className="border rounded px-3 py-2" value={convenioId} onChange={(e) => setConvenioId(e.target.value)}>
            <option value="">Convenio...</option>
            {convenios.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
          </select>
          <select
            required
            className="border rounded px-3 py-2 sm:col-span-2"
            value={categoriaId}
            onChange={(e) => setCategoriaId(e.target.value)}
            disabled={!convenioId}
          >
            <option value="">Categoría profesional...</option>
            {categorias.map((c) => (
              <option key={c.id} value={c.id}>{c.grupo} — {c.nombre}</option>
            ))}
          </select>
          <select required className="border rounded px-3 py-2" value={mes} onChange={(e) => setMes(e.target.value)}>
            {MESES.map((nombre, i) => (
              <option key={i + 1} value={i + 1}>{nombre}</option>
            ))}
          </select>
          <input
            required
            type="number"
            placeholder="Año"
            className="border rounded px-3 py-2"
            value={anio}
            onChange={(e) => setAnio(e.target.value)}
          />
          <label className="flex flex-col gap-1 text-xs text-slate-500 sm:col-span-2">
            Festivos adicionales en el mes (opcional)
            <input
              type="number"
              min={0}
              className="border rounded px-3 py-2"
              value={festivosAdicionales}
              onChange={(e) => setFestivosAdicionales(e.target.value)}
            />
          </label>
        </div>

        <div className="border-t pt-3">
          <h2 className="font-medium text-sm mb-2">Datos de la plantilla</h2>
          <div className="grid sm:grid-cols-3 gap-3">
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Número de empleados
              <input
                required
                type="number"
                min={1}
                className="border rounded px-3 py-2"
                value={numeroEmpleados}
                onChange={(e) => setNumeroEmpleados(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Horas extra (total del grupo)
              <input
                type="number"
                min={0}
                step="0.01"
                className="border rounded px-3 py-2"
                value={horasExtraTotal}
                onChange={(e) => setHorasExtraTotal(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Combustible (€, total)
              <input
                type="number"
                min={0}
                step="0.01"
                className="border rounded px-3 py-2"
                value={combustible}
                onChange={(e) => setCombustible(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Alojamiento (€, total)
              <input
                type="number"
                min={0}
                step="0.01"
                className="border rounded px-3 py-2"
                value={alojamiento}
                onChange={(e) => setAlojamiento(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Dietas (€, total)
              <input
                type="number"
                min={0}
                step="0.01"
                className="border rounded px-3 py-2"
                value={dietas}
                onChange={(e) => setDietas(e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Gastos varios (€, total)
              <input
                type="number"
                min={0}
                step="0.01"
                className="border rounded px-3 py-2"
                value={gastosVarios}
                onChange={(e) => setGastosVarios(e.target.value)}
              />
            </label>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Las horas extra y los gastos se indican como <strong>total del grupo</strong> — se reparten a
            partes iguales entre el número de empleados. Combustible, alojamiento, dietas y gastos varios no
            cotizan a la Seguridad Social (son compensación de gastos, no salario).
          </p>
        </div>

        <button disabled={cargando} className="bg-slate-900 text-white rounded py-2 px-4 text-sm disabled:opacity-50">
          {cargando ? "Calculando..." : "Calcular"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {resultado && (
        <div className="bg-white border rounded-lg p-4 space-y-3">
          <div>
            <h2 className="font-medium">{resultado.categoria_grupo} — {resultado.categoria_nombre}</h2>
            <p className="text-sm text-slate-500">
              {resultado.convenio_nombre} · {MESES[resultado.mes - 1]} {resultado.anio} · {resultado.numero_empleados} empleados
            </p>
          </div>

          <div className="grid sm:grid-cols-3 gap-2 text-sm bg-slate-50 border rounded p-3">
            <div>Días laborables del mes: <strong>{resultado.dias_laborables_mes}</strong></div>
            <div>Horas del mes: <strong>{Number(resultado.horas_mes).toFixed(0)}</strong></div>
            <div>Precio hora real: <strong>{Number(resultado.precio_hora_real).toFixed(2)} €</strong></div>
          </div>

          <table className="w-full text-sm">
            <tbody>
              <tr className="border-t">
                <td className="p-1.5">Salario base + complementos (por empleado)</td>
                <td className="p-1.5 text-right">{Number(resultado.salario_base_mensual_individual).toFixed(2)} €</td>
              </tr>
              <tr className="border-t">
                <td className="p-1.5">Prorrata de pagas extraordinarias (por empleado)</td>
                <td className="p-1.5 text-right">{Number(resultado.prorrata_pagas_extra_individual).toFixed(2)} €</td>
              </tr>
              {Number(resultado.horas_extra_total) > 0 && (
                <tr className="border-t">
                  <td className="p-1.5">
                    Horas extra ({Number(resultado.horas_extra_total).toFixed(2)}h grupo ÷ {resultado.numero_empleados} ={" "}
                    {Number(resultado.horas_extra_individual).toFixed(2)}h/empleado)
                  </td>
                  <td className="p-1.5 text-right">{Number(resultado.importe_horas_extra_individual).toFixed(2)} €</td>
                </tr>
              )}
              <tr className="border-t font-medium">
                <td className="p-1.5">Total devengado (por empleado)</td>
                <td className="p-1.5 text-right">{Number(resultado.total_devengado_individual).toFixed(2)} €</td>
              </tr>
              <tr className="border-t">
                <td className="p-1.5">Cotización a la Seguridad Social — empresa (por empleado)</td>
                <td className="p-1.5 text-right">{Number(resultado.cuota_empresa_ss_individual).toFixed(2)} €</td>
              </tr>
              <tr className="border-t font-medium">
                <td className="p-1.5">Coste laboral (por empleado)</td>
                <td className="p-1.5 text-right">{Number(resultado.coste_laboral_individual).toFixed(2)} €</td>
              </tr>
              {Number(resultado.gastos_reparto_total) > 0 && (
                <tr className="border-t">
                  <td className="p-1.5">
                    Gastos del grupo ({Number(resultado.gastos_reparto_total).toFixed(2)} € ÷ {resultado.numero_empleados})
                  </td>
                  <td className="p-1.5 text-right">{Number(resultado.gastos_reparto_individual).toFixed(2)} €</td>
                </tr>
              )}
            </tbody>
          </table>

          <div className="border-t pt-3 grid sm:grid-cols-2 gap-2">
            <div className="bg-slate-900 text-white rounded p-3">
              <div className="text-xs opacity-80">Coste real por empleado</div>
              <div className="text-xl font-semibold">{Number(resultado.coste_real_individual).toFixed(2)} €</div>
            </div>
            <div className="bg-slate-900 text-white rounded p-3">
              <div className="text-xs opacity-80">Coste total de la plantilla ({resultado.numero_empleados})</div>
              <div className="text-xl font-semibold">{Number(resultado.coste_total_plantilla).toFixed(2)} €</div>
            </div>
          </div>
          <p className="text-xs text-slate-400">
            Coste orientativo: salario de convenio (100% jornada, sin antigüedad ni mejoras), pagas extra
            prorrateadas, horas extra repartidas al precio de la hora real de este mes con el recargo legal,
            cotización empresarial a la Seguridad Social sobre esa base, y el reparto proporcional de los
            gastos del grupo introducidos.
          </p>
        </div>
      )}
    </div>
  );
}
