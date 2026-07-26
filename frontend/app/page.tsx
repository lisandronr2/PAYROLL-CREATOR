import Link from "next/link";

const CARDS = [
  { href: "/empresas", title: "Empresas", desc: "Alta y gestión de empresas." },
  { href: "/trabajadores", title: "Trabajadores", desc: "Alta y gestión de trabajadores." },
  { href: "/contratos", title: "Contratos", desc: "Vincula trabajador, convenio y categoría." },
  { href: "/convenios", title: "Convenios", desc: "Consulta convenios y tablas salariales cargadas." },
  { href: "/nominas/generar", title: "Generar nómina", desc: "Calcula la nómina mensual de un contrato." },
  { href: "/nominas/historial", title: "Historial de nóminas", desc: "Consulta y descarga nóminas generadas." },
];

export default function Home() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-2">PAYROLL CREATOR</h1>
      <p className="text-slate-600 mb-6 max-w-2xl">
        Motor de cálculo jurídico-laboral para nóminas en España (MVP). Empieza dando de alta una
        empresa, un trabajador y su contrato, y después genera la nómina mensual.
      </p>
      <div className="grid sm:grid-cols-2 gap-4">
        {CARDS.map((c) => (
          <Link
            key={c.href}
            href={c.href}
            className="block border rounded-lg p-4 bg-white hover:shadow transition"
          >
            <h2 className="font-medium">{c.title}</h2>
            <p className="text-sm text-slate-500 mt-1">{c.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
