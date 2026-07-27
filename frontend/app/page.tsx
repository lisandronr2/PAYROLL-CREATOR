export default function Home() {
  return (
    <div className="max-w-2xl mx-auto text-center py-10">
      <h1 className="text-3xl font-bold mb-3">PAYROLL CREATOR</h1>
      <p className="text-slate-600 mb-6">
        Motor de cálculo jurídico-laboral para nóminas en España.
      </p>

      <div className="text-left border rounded-lg bg-white p-6 space-y-4">
        <div>
          <h2 className="font-semibold mb-1">Qué es</h2>
          <p className="text-sm text-slate-600">
            Una aplicación que calcula nóminas mensuales de cualquier empresa aplicando de forma
            explícita la normativa laboral española: convenio colectivo, cotización a la Seguridad
            Social, retención de IRPF, horas extraordinarias, incapacidad temporal, dietas y
            prorrata de pagas extraordinarias.
          </p>
        </div>
        <div>
          <h2 className="font-semibold mb-1">Para qué sirve</h2>
          <p className="text-sm text-slate-600">
            Da de alta empresas, trabajadores y contratos, y genera cada nómina con el desglose
            completo de devengos y deducciones — cada línea indica si computa o no en la base de
            cotización, y su referencia legal. Descarga el resultado como PDF listo para entregar.
          </p>
        </div>
        <div>
          <h2 className="font-semibold mb-1">Objetivo</h2>
          <p className="text-sm text-slate-600">
            Ser un motor de cálculo transparente y auditable, no una simple plantilla: los
            parámetros legales (SMI, tipos de cotización, tramos de IRPF, tablas de convenio) se
            mantienen versionados y editables, para que puedan actualizarse cuando cambie la
            normativa sin depender de una nueva versión del programa.
          </p>
        </div>
      </div>

      <p className="text-sm text-slate-500 mt-6">
        Elige una opción en el menú para empezar.
      </p>
    </div>
  );
}
