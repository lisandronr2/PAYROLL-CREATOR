"use client";

import { useState } from "react";
import { Palette, Check } from "lucide-react";
import { TEMAS, useTheme, ColoresPersonalizados } from "@/contexts/ThemeContext";

const PALETA_TITULO = ["#e0f2fe", "#dbeafe", "#ede9fe", "#fce7f3", "#fee2e2", "#ffedd5", "#fef9c3", "#dcfce7"];
const PALETA_TEXTO = ["#334155", "#475569", "#64748b", "#57534e", "#525252", "#6b7280", "#4b5563", "#3f3f46"];
const PALETA_BASE = ["#ffffff", "#f8fafc", "#fefce8", "#ecfdf5", "#eff6ff", "#fdf2f8", "#f5f3ff", "#fff7ed"];

function FilaSwatches({
  etiqueta,
  paleta,
  valor,
  onElegir,
}: {
  etiqueta: string;
  paleta: string[];
  valor: string;
  onElegir: (color: string) => void;
}) {
  return (
    <div className="mb-2">
      <div className="text-[11px] text-slate-500 mb-1">{etiqueta}</div>
      <div className="flex flex-wrap gap-1.5">
        {paleta.map((color) => (
          <button
            key={color}
            type="button"
            onClick={() => onElegir(color)}
            title={color}
            className="w-6 h-6 rounded-full border border-black/10 flex items-center justify-center"
            style={{ backgroundColor: color }}
          >
            {valor.toLowerCase() === color.toLowerCase() && (
              <Check size={12} className="drop-shadow" color="#00000080" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ThemeSwitcher({ direction = "down" }: { direction?: "up" | "down" }) {
  const { tema, setTema, coloresPersonalizados, setColorPersonalizado } = useTheme();
  const [abierto, setAbierto] = useState(false);

  function elegirColor(clave: keyof ColoresPersonalizados, color: string) {
    setColorPersonalizado(clave, color);
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        className="p-2 rounded hover:bg-slate-100 text-slate-500 shrink-0"
        title="Cambiar tema"
        aria-label="Cambiar tema"
      >
        <Palette size={16} />
      </button>

      {abierto && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setAbierto(false)} />
          <div
            className={`absolute left-0 z-50 bg-white border rounded-lg shadow-xl p-2 w-56 text-slate-900 ${
              direction === "up" ? "bottom-full mb-2" : "top-full mt-2"
            }`}
          >
            <div className="text-[11px] font-semibold text-slate-500 px-1 mb-1">TEMA</div>
            {TEMAS.map((t) => (
              <button
                key={t.value}
                onClick={() => setTema(t.value)}
                className={`w-full text-left px-2 py-1.5 rounded text-sm flex items-center justify-between hover:bg-slate-100 ${
                  tema === t.value ? "font-semibold" : ""
                }`}
              >
                {t.label}
                {tema === t.value && <Check size={14} />}
              </button>
            ))}

            {tema === "custom" && (
              <div className="border-t mt-2 pt-2 px-1">
                <FilaSwatches
                  etiqueta="Fondo de títulos"
                  paleta={PALETA_TITULO}
                  valor={coloresPersonalizados.tituloBg}
                  onElegir={(c) => elegirColor("tituloBg", c)}
                />
                <FilaSwatches
                  etiqueta="Color de las letras"
                  paleta={PALETA_TEXTO}
                  valor={coloresPersonalizados.texto}
                  onElegir={(c) => elegirColor("texto", c)}
                />
                <FilaSwatches
                  etiqueta="Base de la pantalla"
                  paleta={PALETA_BASE}
                  valor={coloresPersonalizados.base}
                  onElegir={(c) => elegirColor("base", c)}
                />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
