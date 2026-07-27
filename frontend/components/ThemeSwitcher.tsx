"use client";

import { TEMAS, useTheme } from "@/contexts/ThemeContext";

export default function ThemeSwitcher({ className = "" }: { className?: string }) {
  const { tema, setTema } = useTheme();

  return (
    <select
      value={tema}
      onChange={(e) => setTema(e.target.value as typeof tema)}
      className={`border rounded px-2 py-1 text-xs bg-white text-slate-900 ${className}`}
      aria-label="Tema de la aplicación"
    >
      {TEMAS.map((t) => (
        <option key={t.value} value={t.value}>
          {t.label}
        </option>
      ))}
    </select>
  );
}
