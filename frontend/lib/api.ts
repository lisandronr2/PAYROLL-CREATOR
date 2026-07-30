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
  poblacion?: string | null;
  cnae?: string | null;
  codigo_cuenta_cotizacion?: string | null;
  tipo_at_ep_pct: string;
  convenio_id?: number | null;
}

export interface Trabajador {
  id: number;
  empresa_id: number;
  nombre: string;
  apellidos: string;
  nif: string;
  tipo_documento: string;
  numero_afiliacion_ss?: string | null;
  fecha_nacimiento?: string | null;
  fecha_alta: string;
  fecha_baja?: string | null;
  situacion_familiar: string;
  hijos_menores_25: number;
  grado_discapacidad: number;
  iban?: string | null;
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
  puesto_trabajo?: string | null;
  seccion?: string | null;
  salario_pactado_mensual?: string | null;
  complemento_mensual: string;
  pagas_extra_prorrateadas: boolean;
  fecha_antiguedad?: string | null;
}

export interface NominaLinea {
  bloque: string;
  concepto: string;
  cantidad?: string | null;
  base?: string | null;
  tipo_pct?: string | null;
  importe: string;
  referencia_legal?: string | null;
  orden: number;
  cotiza: boolean;
}

export interface Nomina {
  id: number;
  contrato_id: number;
  periodo_anio: number;
  periodo_mes: number;
  tipo: string;
  dias_naturales_periodo: number;
  dias_trabajados: number;
  horas_extra: string;
  horas_extra_nocturnas: string;
  horas_nocturnas_ordinarias: string;
  dias_it: number;
  dias_vacaciones: number;
  dias_festivos_trabajados: number;
  anticipos: string;
  embargo_mensual: string;
  numero_medias_dietas: number;
  numero_dietas_completas_cortas: number;
  numero_dietas_completas_largas: number;
  total_devengado: string;
  total_deducciones: string;
  liquido_a_percibir: string;
  base_cotizacion_comun: string;
  base_sujeta_irpf: string;
  coste_empresa_total: string;
  total_dietas_exentas: string;
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

export interface ConvenioDietaRef {
  id: number;
  convenio_id: number;
  anio: number;
  media_dieta: string;
  dieta_completa_corta: string;
  dieta_completa_larga: string;
  vigente_desde: string;
  vigente_hasta?: string | null;
}

/**
 * Abre el PDF en una pestaña nueva con el visor del navegador (en vez de
 * descargarlo directamente), para poder verlo antes de decidir imprimirlo o
 * guardarlo — el propio visor del navegador ya trae esos botones.
 *
 * La pestaña se abre ANTES de pedir el PDF (síncronamente, en la misma
 * pila de llamadas del click) para que el navegador no la bloquee como
 * ventana emergente; luego se le asigna la URL del PDF ya descargado.
 */
async function abrirPdfEnNuevaPestana(url: string, nombreArchivo: string) {
  const ventana = window.open("", "_blank");
  try {
    const blobUrl = await fetchPdfComoBlobUrl(url);
    if (ventana) {
      ventana.location.href = blobUrl;
    } else {
      // Si aun así el navegador bloqueó la ventana, se descarga directamente
      // como alternativa (mejor que no hacer nada).
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = nombreArchivo;
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
  } catch (err) {
    ventana?.close();
    throw err;
  }
}

async function fetchPdfComoBlobUrl(url: string): Promise<string> {
  const token = getToken();
  const res = await fetch(`${API_URL}${url}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Error ${res.status} al abrir el PDF`);
  const blob = await res.blob();
  return window.URL.createObjectURL(blob);
}

async function verPdfNomina(nominaId: number, nombreArchivo: string) {
  await abrirPdfEnNuevaPestana(`/nominas/${nominaId}/pdf`, nombreArchivo);
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
    solicitarRecuperacion: (email: string) =>
      request<{ detail: string }>("/auth/solicitar-recuperacion", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    restablecerPassword: (token: string, password: string) =>
      request<{ detail: string }>("/auth/restablecer-password", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      }),
  },
  empresas: {
    listar: () => request<Empresa[]>("/empresas"),
    obtener: (id: number) => request<Empresa>(`/empresas/${id}`),
    crear: (data: Partial<Empresa>) =>
      request<Empresa>("/empresas", { method: "POST", body: JSON.stringify(data) }),
  },
  trabajadores: {
    listar: (empresaId?: number) =>
      request<Trabajador[]>(`/trabajadores${empresaId ? `?empresa_id=${empresaId}` : ""}`),
    obtener: (id: number) => request<Trabajador>(`/trabajadores/${id}`),
    crear: (data: Partial<Trabajador>) =>
      request<Trabajador>("/trabajadores", { method: "POST", body: JSON.stringify(data) }),
    actualizar: (id: number, data: Partial<Trabajador>) =>
      request<Trabajador>(`/trabajadores/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  },
  convenios: {
    listar: () => request<Convenio[]>("/convenios"),
    categorias: (convenioId: number) =>
      request<CategoriaProfesional[]>(`/convenios/${convenioId}/categorias`),
  },
  contratos: {
    listar: (trabajadorId?: number) =>
      request<Contrato[]>(`/contratos${trabajadorId ? `?trabajador_id=${trabajadorId}` : ""}`),
    obtener: (id: number) => request<Contrato>(`/contratos/${id}`),
    crear: (data: Partial<Contrato>) =>
      request<Contrato>("/contratos", { method: "POST", body: JSON.stringify(data) }),
    extraerPdf: async (archivo: File) => {
      const token = getToken();
      const formData = new FormData();
      formData.append("archivo", archivo);
      const res = await fetch(`${API_URL}/contratos/extraer-pdf`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) throw new Error(`Error ${res.status} al leer el PDF`);
      return res.json() as Promise<{
        fecha_inicio: string | null;
        tipo_contrato: string | null;
        jornada_porcentaje: string | null;
        salario_pactado_mensual: string | null;
        puesto_trabajo: string | null;
        texto_extraido_preview: string;
      }>;
    },
  },
  nominas: {
    listar: (contratoId?: number) =>
      request<Nomina[]>(`/nominas${contratoId ? `?contrato_id=${contratoId}` : ""}`),
    obtener: (id: number) => request<Nomina>(`/nominas/${id}`),
    generar: (data: Record<string, unknown>) =>
      request<Nomina>("/nominas/generar", { method: "POST", body: JSON.stringify(data) }),
    actualizar: (id: number, data: Record<string, unknown>) =>
      request<Nomina>(`/nominas/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    eliminar: (id: number) => request<void>(`/nominas/${id}`, { method: "DELETE" }),
    verPdf: verPdfNomina,
  },
  referencia: {
    parametrosLegales: () => request<ParametroLegal[]>("/referencia/parametros-legales"),
    dietasConvenio: (convenioId: number) =>
      request<ConvenioDietaRef[]>(`/referencia/convenios/${convenioId}/dietas`),
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
