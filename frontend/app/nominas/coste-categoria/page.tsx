"use client";

import { useEffect, useState } from "react";
import { api, CategoriaProfesional, CosteCategoria, Empresa } from "@/lib/api";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export default function CosteCategoriaPage() {
  const hoy = new Date();

  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [categorias, setCategorias] = useState<CategoriaProfesional[]>([]);
  const [empresaId, setEmpresaId] = useState("");
  const [convenioId, setConvenioId] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [anio, setAnio] = useState(String(hoy.getFullYear()));
  const [mes, setMes] = useState(String(hoy.getMonth() + 1));
  const [festivosAdicionales, setFestivosAdicionales] = useState("0");

  const [resultado, setResultado] = useState<CosteCategoria | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [convenios, setConvenios] = useState<{ id: number; nombre: string }[]>([]);

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
      const r = await api.referencia.costeCategoria({
        empresa_id: Number(empresaId),
        categoria_id: Number(categoriaId),
        anio: Number(anio),
        mes: Number(mes),
        festivos_adicionales: Number(festivosAdicionales) || 0,
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
        <h1 className="text-xl font-semibold">Coste por categoría</h1>
        <p className="text-sm text-slate-500 mt-1">
          Coste mensual y por hora de un empleado según su categoría de convenio, para un mes/año
          concreto. El coste mensual no cambia (el salario de convenio es fijo), pero el coste por hora
          sí, porque cada mes tiene un número distinto de días laborables.
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
        <p className="text-xs text-slate-400">
          Los días laborables se calculan como los días de lunes a viernes del mes — la aplicación no
          tiene cargado un calendario de festivos nacionales/autonómicos/locales, así que si el mes
          elegido tiene alguno, indica cuántos aquí para descontarlos.
        </p>
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
              {resultado.convenio_nombre} · {MESES[resultado.mes - 1]} {resultado.anio}
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-2 text-sm bg-slate-50 border rounded p-3">
            <div>Días naturales del mes: <strong>{resultado.dias_naturales_mes}</strong></div>
            <div>Días laborables del mes: <strong>{resultado.dias_laborables_mes}</strong></div>
            <div>Horas del mes (jornadas de 8h): <strong>{Number(resultado.horas_mes).toFixed(0)}</strong></div>
          </div>

          <table className="w-full text-sm">
            <tbody>
              <tr className="border-t">
                <td className="p-1.5">Salario base + complementos de convenio</td>
                <td className="p-1.5 text-right">{Number(resultado.salario_base_mensual).toFixed(2)} €</td>
              </tr>
              <tr className="border-t">
                <td className="p-1.5">Prorrata de pagas extraordinarias</td>
                <td className="p-1.5 text-right">{Number(resultado.prorrata_pagas_extra_mensual).toFixed(2)} €</td>
              </tr>
              <tr className="border-t font-medium">
                <td className="p-1.5">Total devengado mensual</td>
                <td className="p-1.5 text-right">{Number(resultado.total_devengado_mensual).toFixed(2)} €</td>
              </tr>
              <tr className="border-t">
                <td className="p-1.5">Cotización a la Seguridad Social (empresa)</td>
                <td className="p-1.5 text-right">{Number(resultado.cuota_empresa_ss_mensual).toFixed(2)} €</td>
              </tr>
            </tbody>
          </table>

          <div className="border-t pt-3 grid sm:grid-cols-2 gap-2">
            <div className="bg-slate-900 text-white rounded p-3">
              <div className="text-xs opacity-80">Coste empresa al mes</div>
              <div className="text-xl font-semibold">{Number(resultado.coste_empresa_mensual).toFixed(2)} €</div>
            </div>
            <div className="bg-slate-900 text-white rounded p-3">
              <div className="text-xs opacity-80">Coste empresa por hora este mes</div>
              <div className="text-xl font-semibold">{Number(resultado.coste_empresa_por_hora).toFixed(2)} €</div>
            </div>
          </div>
          <p className="text-xs text-slate-400">
            Coste orientativo: salario de convenio (100% jornada, sin antigüedad ni mejoras), pagas
            extra prorrateadas y cotización empresarial a la Seguridad Social. No incluye dietas,
            horas extra ni otros complementos específicos de un contrato real.
          </p>
        </div>
      )}
    </div>
  );
}
