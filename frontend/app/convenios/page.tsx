"use client";

import { useEffect, useState } from "react";
import { api, CategoriaProfesional, Convenio } from "@/lib/api";

export default function ConveniosPage() {
  const [convenios, setConvenios] = useState<Convenio[]>([]);
  const [categoriasPorConvenio, setCategoriasPorConvenio] = useState<Record<number, CategoriaProfesional[]>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.convenios
      .listar()
      .then(async (lista) => {
        setConvenios(lista);
        const entries = await Promise.all(
          lista.map(async (c) => [c.id, await api.convenios.categorias(c.id)] as const)
        );
        setCategoriasPorConvenio(Object.fromEntries(entries));
      })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">Convenios cargados</h1>
      <p className="text-sm text-slate-500 mb-4">
        Datos de ejemplo/orientativos salvo indicación contraria en las notas. Verificar vigencia
        antes de uso real — ver docs/LEGAL_DISCLAIMER.md.
      </p>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="space-y-4">
        {convenios.map((c) => (
          <div key={c.id} className="bg-white border rounded-lg p-4">
            <h2 className="font-medium">{c.nombre}</h2>
            <p className="text-xs text-slate-500 mb-2">
              {c.ambito} — {c.provincia ?? "N/A"} — {c.numero_pagas} pagas
            </p>
            {c.notas && <p className="text-xs bg-amber-50 border border-amber-200 rounded p-2 mb-2">{c.notas}</p>}
            <table className="w-full text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="text-left p-1">Grupo</th>
                  <th className="text-left p-1">Categoría</th>
                  <th className="text-left p-1">Grupo cotización</th>
                </tr>
              </thead>
              <tbody>
                {(categoriasPorConvenio[c.id] ?? []).map((cat) => (
                  <tr key={cat.id} className="border-t">
                    <td className="p-1">{cat.grupo}</td>
                    <td className="p-1">{cat.nombre}</td>
                    <td className="p-1">{cat.grupo_cotizacion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
}
