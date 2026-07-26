const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "payroll_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, {
    headers,
    ...options,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    throw new Error("No autenticado");
  }

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Error ${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface Usuario {
  id: number;
  email: string;
  nombre: string;
  rol: "admin" | "operador";
  activo: boolean;
  creado_en: string;
}

export interface Empresa {
  id: number;
  razon_social: string;
  cif: string;
  direccion?: string | null;
  cnae?: string | null;
  codigo_cuenta_cotizacion?: string | null;
  convenio_id?: number | null;
}

export interface Trabajador {
  id: number;
  empresa_id: number;
  nombre: string;
  apellidos: string;
  nif: string;
  numero_afiliacion_ss?: string | null;
  fecha_alta: string;
  fecha_baja?: string | null;
  situacion_familiar: string;
  hijos_menores_25: number;
  grado_discapacidad: number;
  activo: boolean;
}

export interface Convenio {
  id: number;
  nombre: string;
  ambito?: string | null;
  provincia?: string | null;
  numero_pagas: number;
  jornada_anual_horas: string;
  notas?: string | null;
}

export interface CategoriaProfesional {
  id: number;
  convenio_id: number;
  grupo: string;
  nombre: string;
  grupo_cotizacion: number;
}

export interface Contrato {
  id: number;
  trabajador_id: number;
  convenio_id: number;
  categoria_id: number;
  tipo_contrato: string;
  jornada_porcentaje: string;
  fecha_inicio: string;
  fecha_fin?: string | null;
  pagas_extra_prorrateadas: boolean;
}

export interface NominaLinea {
  bloque: string;
  concepto: string;
  base?: string | null;
  tipo_pct?: string | null;
  importe: string;
  referencia_legal?: string | null;
  orden: number;
}

export interface Nomina {
  id: number;
  contrato_id: number;
  periodo_anio: number;
  periodo_mes: number;
  tipo: string;
  total_devengado: string;
  total_deducciones: string;
  liquido_a_percibir: string;
  base_cotizacion_comun: string;
  base_sujeta_irpf: string;
  coste_empresa_total: string;
  lineas: NominaLinea[];
}

export interface ParametroLegal {
  id: number;
  clave: string;
  valor: string;
  grupo_cotizacion?: number | null;
  vigente_desde: string;
  vigente_hasta?: string | null;
  referencia_legal?: string | null;
}

export interface TramoIRPF {
  id: number;
  anio: number;
  base_desde_anual: string;
  base_hasta_anual?: string | null;
  tipo_aplicable_pct: string;
  vigente_desde: string;
  vigente_hasta?: string | null;
}

async function descargarPdf(nominaId: number, nombreArchivo: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/nominas/${nominaId}/pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Error ${res.status} al descargar el PDF`);
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombreArchivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export const api = {
  auth: {
    login: async (email: string, password: string) => {
      const data = await request<{ access_token: string; usuario: Usuario }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(data.access_token);
      return data.usuario;
    },
    me: () => request<Usuario>("/auth/me"),
    logout: () => clearToken(),
  },
  empresas: {
    listar: () => request<Empresa[]>("/empresas"),
    crear: (data: Partial<Empresa>) =>
      request<Empresa>("/empresas", { method: "POST", body: JSON.stringify(data) }),
  },
  trabajadores: {
    listar: (empresaId?: number) =>
      request<Trabajador[]>(`/trabajadores${empresaId ? `?empresa_id=${empresaId}` : ""}`),
    crear: (data: Partial<Trabajador>) =>
      request<Trabajador>("/trabajadores", { method: "POST", body: JSON.stringify(data) }),
  },
  convenios: {
    listar: () => request<Convenio[]>("/convenios"),
    categorias: (convenioId: number) =>
      request<CategoriaProfesional[]>(`/convenios/${convenioId}/categorias`),
  },
  contratos: {
    listar: (trabajadorId?: number) =>
      request<Contrato[]>(`/contratos${trabajadorId ? `?trabajador_id=${trabajadorId}` : ""}`),
    crear: (data: Partial<Contrato>) =>
      request<Contrato>("/contratos", { method: "POST", body: JSON.stringify(data) }),
  },
  nominas: {
    listar: (contratoId?: number) =>
      request<Nomina[]>(`/nominas${contratoId ? `?contrato_id=${contratoId}` : ""}`),
    generar: (data: Record<string, unknown>) =>
      request<Nomina>("/nominas/generar", { method: "POST", body: JSON.stringify(data) }),
    descargarPdf,
  },
  admin: {
    usuarios: {
      listar: () => request<Usuario[]>("/admin/usuarios"),
      crear: (data: { email: string; nombre: string; password: string; rol: string }) =>
        request<Usuario>("/admin/usuarios", { method: "POST", body: JSON.stringify(data) }),
      actualizar: (id: number, data: Partial<{ nombre: string; rol: string; activo: boolean; password: string }>) =>
        request<Usuario>(`/admin/usuarios/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    },
    parametrosLegales: {
      listar: (clave?: string) =>
        request<ParametroLegal[]>(`/admin/parametros-legales${clave ? `?clave=${clave}` : ""}`),
      crear: (data: Partial<ParametroLegal>) =>
        request<ParametroLegal>("/admin/parametros-legales", { method: "POST", body: JSON.stringify(data) }),
      actualizar: (id: number, data: Partial<ParametroLegal>) =>
        request<ParametroLegal>(`/admin/parametros-legales/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
      eliminar: (id: number) => request<void>(`/admin/parametros-legales/${id}`, { method: "DELETE" }),
    },
    tablaIrpf: {
      listar: (anio?: number) => request<TramoIRPF[]>(`/admin/tabla-irpf${anio ? `?anio=${anio}` : ""}`),
      crear: (data: Partial<TramoIRPF>) =>
        request<TramoIRPF>("/admin/tabla-irpf", { method: "POST", body: JSON.stringify(data) }),
      actualizar: (id: number, data: Partial<TramoIRPF>) =>
        request<TramoIRPF>(`/admin/tabla-irpf/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
      eliminar: (id: number) => request<void>(`/admin/tabla-irpf/${id}`, { method: "DELETE" }),
    },
    convenios: {
      crear: (data: Partial<Convenio>) =>
        request<Convenio>("/admin/convenios", { method: "POST", body: JSON.stringify(data) }),
      actualizar: (id: number, data: Partial<Convenio>) =>
        request<Convenio>(`/admin/convenios/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
      crearCategoria: (data: Partial<CategoriaProfesional>) =>
        request<CategoriaProfesional>("/admin/categorias-profesionales", {
          method: "POST",
          body: JSON.stringify(data),
        }),
      crearTablaSalarial: (data: Record<string, unknown>) =>
        request("/admin/tablas-salariales", { method: "POST", body: JSON.stringify(data) }),
    },
  },
};
