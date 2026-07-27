import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import AppShell from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Payroll Creator",
  description: "Motor de cálculo de nóminas para España",
};

const THEME_INIT_SCRIPT = `
(function () {
  try {
    var t = window.localStorage.getItem("payroll_theme") || "light";
    document.documentElement.setAttribute("data-theme", t);
    if (t === "custom") {
      var raw = window.localStorage.getItem("payroll_custom_colors");
      var c = raw ? JSON.parse(raw) : {};
      var s = document.documentElement.style;
      if (c.base) { s.setProperty("--pc-bg", c.base); s.setProperty("--pc-surface", c.base); }
      if (c.tituloBg) { s.setProperty("--pc-surface-alt", c.tituloBg); s.setProperty("--pc-accent", c.tituloBg); s.setProperty("--pc-notice-bg", c.tituloBg); }
      if (c.texto) { s.setProperty("--pc-accent-text", c.texto); s.setProperty("--pc-text", c.texto); s.setProperty("--pc-muted", c.texto); s.setProperty("--pc-link", c.texto); }
    }
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="h-full antialiased" data-theme="light">
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <ThemeProvider>
          <AuthProvider>
            <AppShell>{children}</AppShell>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
