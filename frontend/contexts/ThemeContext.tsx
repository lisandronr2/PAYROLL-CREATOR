"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Tema = "light" | "dark" | "modern" | "yellow" | "bw";

export const TEMAS: { value: Tema; label: string }[] = [
  { value: "light", label: "Modo Claro" },
  { value: "dark", label: "Modo Oscuro" },
  { value: "modern", label: "Modo Moderno" },
  { value: "yellow", label: "Monocromo Amarillo" },
  { value: "bw", label: "Blanco y Negro" },
];

const STORAGE_KEY = "payroll_theme";

interface ThemeState {
  tema: Tema;
  setTema: (t: Tema) => void;
}

const ThemeContext = createContext<ThemeState | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [tema, setTemaState] = useState<Tema>("light");

  useEffect(() => {
    const guardado = window.localStorage.getItem(STORAGE_KEY) as Tema | null;
    if (guardado) setTemaState(guardado);
  }, []);

  function setTema(t: Tema) {
    setTemaState(t);
    window.localStorage.setItem(STORAGE_KEY, t);
    document.documentElement.setAttribute("data-theme", t);
  }

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", tema);
  }, [tema]);

  return <ThemeContext.Provider value={{ tema, setTema }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme debe usarse dentro de ThemeProvider");
  return ctx;
}
