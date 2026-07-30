"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2,
  Users,
  FileSignature,
  BookOpen,
  Calculator,
  History,
  ShieldCheck,
  SlidersHorizontal,
  Percent,
  BookOpenCheck,
  UserCog,
  ChevronDown,
  Menu,
  X,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import { FULL_VERSION } from "@/lib/version";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

interface NavGroup {
  id: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  items: NavItem[];
}

const GROUPS: NavGroup[] = [
  {
    id: "gestion",
    label: "Gestión",
    icon: Building2,
    items: [
      { href: "/empresas", label: "Empresas", icon: Building2 },
      { href: "/trabajadores", label: "Trabajadores", icon: Users },
      { href: "/contratos", label: "Contratos", icon: FileSignature },
      { href: "/convenios", label: "Convenios", icon: BookOpen },
    ],
  },
  {
    id: "nominas",
    label: "Nóminas",
    icon: Calculator,
    items: [
      { href: "/nominas/generar", label: "Generar nómina", icon: Calculator },
      { href: "/nominas/historial", label: "Historial", icon: History },
    ],
  },
];

const ADMIN_GROUP: NavGroup = {
  id: "admin",
  label: "Administración",
  icon: ShieldCheck,
  items: [
    { href: "/admin/parametros", label: "Parámetros legales", icon: SlidersHorizontal },
    { href: "/admin/tabla-irpf", label: "Tabla IRPF", icon: Percent },
    { href: "/admin/convenios", label: "Convenios (editar)", icon: BookOpenCheck },
    { href: "/admin/usuarios", label: "Usuarios", icon: UserCog },
  ],
};

const STORAGE_GROUPS = "payroll_sidebar_groups_open";
const SWIPE_EDGE_PX = 24;
const SWIPE_THRESHOLD_PX = 50;

export default function Sidebar({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { usuario, logout } = useAuth();

  // El menú siempre arranca contraído: cada vez que se cierra (se navega a
  // una opción) y se vuelve a abrir (se regresa al inicio), este componente
  // se remonta y este useState vuelve a su valor inicial "true".
  const [collapsed, setCollapsed] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    gestion: true,
    nominas: true,
    admin: true,
  });

  const touchStartX = useRef<number | null>(null);
  const touchStartY = useRef<number | null>(null);

  useEffect(() => {
    const savedGroups = window.localStorage.getItem(STORAGE_GROUPS);
    if (savedGroups) {
      try {
        setOpenGroups(JSON.parse(savedGroups));
      } catch {
        /* ignore */
      }
    }
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Con el drawer móvil abierto, el scroll debe quedarse en el propio menú
  // (nivel más alto), no en la página de fondo.
  useEffect(() => {
    if (mobileOpen) {
      const previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = previousOverflow;
      };
    }
  }, [mobileOpen]);

  function toggleCollapsed() {
    setCollapsed((prev) => !prev);
  }

  function toggleGroup(id: string) {
    setOpenGroups((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      window.localStorage.setItem(STORAGE_GROUPS, JSON.stringify(next));
      return next;
    });
  }

  // Gestos táctiles: deslizar desde el borde izquierdo abre el menú;
  // deslizar hacia la izquierda dentro del panel lo cierra.
  function onTouchStart(e: React.TouchEvent) {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
  }

  function onTouchEndEdge(e: React.TouchEvent) {
    if (touchStartX.current === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX.current;
    const dy = Math.abs(e.changedTouches[0].clientY - (touchStartY.current ?? 0));
    if (dx > SWIPE_THRESHOLD_PX && dy < 60) setMobileOpen(true);
    touchStartX.current = null;
  }

  function onTouchEndPanel(e: React.TouchEvent) {
    if (touchStartX.current === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX.current;
    const dy = Math.abs(e.changedTouches[0].clientY - (touchStartY.current ?? 0));
    if (dx < -SWIPE_THRESHOLD_PX && dy < 60) setMobileOpen(false);
    touchStartX.current = null;
  }

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  function renderGroup(group: NavGroup, effectiveCollapsed: boolean) {
    const abierto = openGroups[group.id] ?? true;
    const activo = group.items.some((i) => isActive(i.href));
    return (
      <div key={group.id} className="mb-1">
        <button
          onClick={() => {
            if (effectiveCollapsed) {
              // Con el rail contraído no hay dónde mostrar los ítems: primero
              // hay que expandir el menú y dejar el grupo abierto.
              setCollapsed(false);
              setOpenGroups((prev) => {
                const next = { ...prev, [group.id]: true };
                window.localStorage.setItem(STORAGE_GROUPS, JSON.stringify(next));
                return next;
              });
            } else {
              toggleGroup(group.id);
            }
          }}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-slate-100 ${
            activo ? "text-slate-900" : "text-slate-600"
          }`}
          title={group.label}
        >
          <group.icon size={18} className="shrink-0" />
          {!effectiveCollapsed && (
            <>
              <span className="flex-1 text-left">{group.label}</span>
              <ChevronDown
                size={16}
                className={`shrink-0 transition-transform duration-200 ${abierto ? "rotate-0" : "-rotate-90"}`}
              />
            </>
          )}
        </button>
        {!effectiveCollapsed && (
          <div
            className="overflow-hidden transition-all duration-200 ease-in-out"
            style={{ maxHeight: abierto ? group.items.length * 44 + 8 : 0 }}
          >
            <div className="pl-3 mt-1 space-y-0.5 border-l ml-4">
              {group.items.map((item) => {
                const activeItem = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                      activeItem
                        ? "bg-slate-900 text-white"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                    }`}
                  >
                    <item.icon size={16} className="shrink-0" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }

  const grupos = usuario?.rol === "admin" ? [...GROUPS, ADMIN_GROUP] : GROUPS;

  function renderSidebarInner(effectiveCollapsed: boolean) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between px-3 py-4 border-b">
          {!effectiveCollapsed && (
            <Link href="/" className="font-semibold text-base leading-tight">
              PAYROLL
              <br />
              CREATOR
            </Link>
          )}
          <button
            onClick={toggleCollapsed}
            className="hidden md:flex p-1.5 rounded hover:bg-slate-100 text-slate-500"
            title={collapsed ? "Expandir menú" : "Colapsar menú"}
          >
            {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
          <button
            onClick={() => setMobileOpen(false)}
            className="md:hidden p-1.5 rounded hover:bg-slate-100 text-slate-500"
            title="Cerrar menú"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-2 py-3">
          {grupos.map((g) => renderGroup(g, effectiveCollapsed))}
        </nav>

        <div className="border-t px-3 py-3 space-y-2">
          {!effectiveCollapsed && usuario && (
            <div className="text-xs text-slate-500 truncate">
              {usuario.nombre} <span className="opacity-70">({usuario.rol})</span>
            </div>
          )}
          <div className={`flex items-center gap-2 ${effectiveCollapsed ? "flex-col" : ""}`}>
            <ThemeSwitcher direction="up" />
            <button
              onClick={logout}
              className="p-2 rounded hover:bg-slate-100 text-slate-500 shrink-0"
              title="Salir"
            >
              <LogOut size={16} />
            </button>
          </div>
          {!effectiveCollapsed && <div className="text-[10px] text-slate-400">v{FULL_VERSION}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-full">
      {/* Zona invisible en el borde izquierdo para detectar el swipe de apertura en móvil */}
      <div
        className="md:hidden fixed left-0 top-0 h-full z-30"
        style={{ width: SWIPE_EDGE_PX }}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEndEdge}
      />

      {/* Sidebar escritorio */}
      <aside
        className="hidden md:block bg-white border-r shrink-0 overflow-hidden"
        style={{ width: collapsed ? 64 : 256 }}
      >
        <div className="sticky top-0 h-screen" style={{ width: collapsed ? 64 : 256 }}>
          {renderSidebarInner(collapsed)}
        </div>
      </aside>

      {/* Sidebar móvil (drawer): siempre expandido, no hay rail de iconos en móvil */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <div
            className="relative bg-white w-72 max-w-[80vw] h-full shadow-xl"
            onTouchStart={onTouchStart}
            onTouchEnd={onTouchEndPanel}
          >
            {renderSidebarInner(false)}
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <div className="md:hidden flex items-center justify-between px-4 py-3 bg-slate-900 text-white">
          <button onClick={() => setMobileOpen(true)} className="p-1.5 -ml-1.5 rounded hover:bg-white/10">
            <Menu size={22} />
          </button>
          <span className="font-semibold">PAYROLL CREATOR</span>
          <div className="w-8" />
        </div>
        {children}
      </div>
    </div>
  );
}
