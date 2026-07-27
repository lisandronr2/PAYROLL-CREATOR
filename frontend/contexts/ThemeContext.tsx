"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Tema = "light" | "dark" | "modern" | "yellow" | "bw" | "custom";

export const TEMAS: { value: Tema; label: string }[] = [
  { value: "light", label: "Modo Claro" },
  { value: "dark", label: "Modo Oscuro" },
  { value: "modern", label: "Modo Moderno" },
  { value: "yellow", label: "Monocromo Amarillo" },
  { value: "bw", label: "Blanco y Negro" },
  { value: "custom", label: "Personalizado" },
];

export interface ColoresPersonalizados {
  tituloBg: string; // fondo de cabeceras/títulos y botón de acento
  texto: string; // color de las letras
  base: string; // fondo base de la pantalla
}

export const COLORES_PERSONALIZADOS_POR_DEFECTO: ColoresPersonalizados = {
  tituloBg: "#e0f2fe",
  texto: "#475569",
  base: "#f8fafc",
};

const STORAGE_KEY = "payroll_theme";
const STORAGE_CUSTOM = "payroll_custom_colors";

interface ThemeState {
  tema: Tema;
  setTema: (t: Tema) => void;
  coloresPersonalizados: ColoresPersonalizados;
  setColorPersonalizado: (clave: keyof ColoresPersonalizados, valor: string) => void;
}

const ThemeContext = createContext<ThemeState | null>(null);

function aplicarColoresPersonalizados(colores: ColoresPersonalizados) {
  const root = document.documentElement.style;
  root.setProperty("--pc-bg", colores.base);
  root.setProperty("--pc-surface", colores.base);
  root.setProperty("--pc-surface-alt", colores.tituloBg);
  root.setProperty("--pc-accent", colores.tituloBg);
  root.setProperty("--pc-accent-text", colores.texto);
  root.setProperty("--pc-text", colores.texto);
  root.setProperty("--pc-muted", colores.texto);
  root.setProperty("--pc-border", "#e5e7eb");
  root.setProperty("--pc-input-bg", "#ffffff");
  root.setProperty("--pc-link", colores.texto);
  root.setProperty("--pc-notice-bg", colores.tituloBg);
  root.setProperty("--pc-notice-border", "#e5e7eb");
}

function limpiarColoresPersonalizados() {
  const root = document.documentElement.style;
  [
    "--pc-bg",
    "--pc-surface",
    "--pc-surface-alt",
    "--pc-accent",
    "--pc-accent-text",
    "--pc-text",
    "--pc-muted",
    "--pc-border",
    "--pc-input-bg",
    "--pc-link",
    "--pc-notice-bg",
    "--pc-notice-border",
  ].forEach((prop) => root.removeProperty(prop));
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [tema, setTemaState] = useState<Tema>("light");
  const [coloresPersonalizados, setColoresPersonalizados] = useState<ColoresPersonalizados>(
    COLORES_PERSONALIZADOS_POR_DEFECTO
  );

  useEffect(() => {
    const guardado = window.localStorage.getItem(STORAGE_KEY) as Tema | null;
    const coloresGuardados = window.localStorage.getItem(STORAGE_CUSTOM);
    let colores = COLORES_PERSONALIZADOS_POR_DEFECTO;
    if (coloresGuardados) {
      try {
        colores = { ...COLORES_PERSONALIZADOS_POR_DEFECTO, ...JSON.parse(coloresGuardados) };
        setColoresPersonalizados(colores);
      } catch {
        /* ignore */
      }
    }
    if (guardado) {
      setTemaState(guardado);
      if (guardado === "custom") aplicarColoresPersonalizados(colores);
    }
  }, []);

  function setTema(t: Tema) {
    setTemaState(t);
    window.localStorage.setItem(STORAGE_KEY, t);
    document.documentElement.setAttribute("data-theme", t);
    if (t === "custom") {
      aplicarColoresPersonalizados(coloresPersonalizados);
    } else {
      limpiarColoresPersonalizados();
    }
  }

  function setColorPersonalizado(clave: keyof ColoresPersonalizados, valor: string) {
    setColoresPersonalizados((prev) => {
      const next = { ...prev, [clave]: valor };
      window.localStorage.setItem(STORAGE_CUSTOM, JSON.stringify(next));
      if (tema === "custom") aplicarColoresPersonalizados(next);
      return next;
    });
  }

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", tema);
  }, [tema]);

  return (
    <ThemeContext.Provider value={{ tema, setTema, coloresPersonalizados, setColorPersonalizado }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme debe usarse dentro de ThemeProvider");
  return ctx;
}
