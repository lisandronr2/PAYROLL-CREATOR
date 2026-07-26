"use client";

import { useEffect, useState } from "react";
import RequireAuth from "@/components/RequireAuth";
import { api, Usuario } from "@/lib/api";

export default function UsuariosPage() {
  return (
    <RequireAuth soloAdmin>
      <Contenido />
    </RequireAuth>
  );
}

const initialForm = { email: "", nombre: "", password: "", rol: "operador" };

function Contenido() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function cargar() {
    setUsuarios(await api.admin.usuarios.listar());
  }

  useEffect(() => {
    cargar().catch((e) => setError(String(e)));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await api.admin.usuarios.crear(form);
      setForm(initialForm);
      await cargar();
    } catch (err) {
      setError(String(err));
    } finally {
      setCargando(false);
    }
  }

  async function toggleActivo(u: Usuario) {
    await api.admin.usuarios.actualizar(u.id, { activo: !u.activo });
    await cargar();
  }

  async function cambiarRol(u: Usuario) {
    const nuevoRol = u.rol === "admin" ? "operador" : "admin";
    if (!window.confirm(`¿Cambiar el rol de ${u.email} a "${nuevoRol}"?`)) return;
    await api.admin.usuarios.actualizar(u.id, { rol: nuevoRol });
    await cargar();
  }

  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">Usuarios</h1>
      <p className="text-sm text-slate-500 mb-4">
        Los operadores pueden dar de alta empresas, trabajadores, contratos y generar nóminas, pero no
        pueden editar parámetros legales, tablas de convenio ni otros usuarios.
      </p>

      <form onSubmit={onSubmit} className="bg-white border rounded-lg p-4 mb-6 grid sm:grid-cols-2 gap-3">
        <input required type="email" placeholder="Email" className="border rounded px-3 py-2"
          value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input required placeholder="Nombre" className="border rounded px-3 py-2"
          value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
        <input required type="password" placeholder="Contraseña" className="border rounded px-3 py-2"
          value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <select className="border rounded px-3 py-2" value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value })}>
          <option value="operador">Operador</option>
          <option value="admin">Admin</option>
        </select>
        <button disabled={cargando} className="sm:col-span-2 bg-slate-900 text-white rounded py-2 disabled:opacity-50">
          {cargando ? "Guardando..." : "Crear usuario"}
        </button>
      </form>

      {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

      <table className="w-full bg-white border rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-2">Email</th>
            <th className="text-left p-2">Nombre</th>
            <th className="text-left p-2">Rol</th>
            <th className="text-left p-2">Activo</th>
            <th className="text-right p-2">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <tr key={u.id} className="border-t">
              <td className="p-2">{u.email}</td>
              <td className="p-2">{u.nombre}</td>
              <td className="p-2">{u.rol}</td>
              <td className="p-2">{u.activo ? "Sí" : "No"}</td>
              <td className="p-2 text-right space-x-2">
                <button onClick={() => cambiarRol(u)} className="text-blue-600 underline">
                  Cambiar rol
                </button>
                <button onClick={() => toggleActivo(u)} className="text-red-600 underline">
                  {u.activo ? "Desactivar" : "Activar"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
