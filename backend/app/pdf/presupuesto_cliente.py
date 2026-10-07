"""
Datos y formato del PDF de presupuesto "profesional" para el cliente final.

A diferencia del PDF clásico, los importes por línea, los subtotales y el
total que ve el cliente SUMAN EXACTAMENTE: el precio de venta total del
presupuesto se reparte entre secciones y líneas proporcionalmente a su coste
(sin revelarlo), ajustando los céntimos de redondeo. Tampoco se muestran
precios unitarios, que no cuadrarían con el importe al incluir gastos
generales y margen.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.models.presupuesto import Presupuesto
from app.numeracion import numero_visible

HORAS_JORNADA_NORMAL = Decimal("8")
DIAS_VALIDEZ = 15
CERO = Decimal("0.00")


def repartir_redondeando(exactos: list[Decimal], total: Decimal) -> list[Decimal]:
    """Reparte `total` entre importes proporcionales a `exactos`, redondeados a
    céntimos y de forma que sumen exactamente `total` (método del mayor resto)."""
    if not exactos:
        return []
    suma = sum(exactos, Decimal("0"))
    if suma <= 0:
        return [CERO for _ in exactos]
    centimos_total = int((total * 100).to_integral_value(ROUND_HALF_UP))
    brutos = [e / suma * centimos_total for e in exactos]
    bases = [int(b // 1) for b in brutos]
    resto = centimos_total - sum(bases)
    por_resto = sorted(range(len(exactos)), key=lambda i: brutos[i] - bases[i], reverse=True)
    for i in por_resto[:resto]:
        bases[i] += 1
    return [(Decimal(b) / 100).quantize(Decimal("0.01")) for b in bases]


def eur(valor) -> str:
    """1234.5 -> '1.234,50 €' (formato español)."""
    texto = f"{Decimal(valor):,.2f}"
    return texto.replace(",", "\0").replace(".", ",").replace("\0", ".") + " €"


def cant(valor) -> str:
    """2.00 -> '2'; 2.5 -> '2,5'; 2.25 -> '2,25'."""
    numero = Decimal(valor).normalize()
    if numero == numero.to_integral_value():
        return f"{int(numero):,}".replace(",", ".")
    return f"{numero:f}".replace(".", ",")


@dataclass
class LineaVista:
    concepto: str
    coste: Decimal
    cantidad: str = ""
    detalle: str = ""
    personas: str = ""
    dias: str = ""
    horas: str = ""
    importe: Decimal = CERO


@dataclass
class SeccionVista:
    clave: str  # mano_obra | dietas | hotel_combustible | trabajos | materiales
    titulo: str
    lineas: list[LineaVista] = field(default_factory=list)
    total: Decimal = CERO

    @property
    def coste(self) -> Decimal:
        return sum((l.coste for l in self.lineas), Decimal("0"))


def _texto_dietas(medias: int, cortas: int, largas: int) -> str:
    partes = []
    if medias:
        partes.append(f"{medias} {'media dieta' if medias == 1 else 'medias dietas'}")
    if cortas:
        partes.append(f"{cortas} {'dieta completa' if cortas == 1 else 'dietas completas'} (viaje de menos de 7 días)")
    if largas:
        partes.append(f"{largas} {'dieta completa' if largas == 1 else 'dietas completas'} (viaje de 7 días o más)")
    return " · ".join(partes)


def preparar_secciones(presupuesto: Presupuesto) -> list[SeccionVista]:
    secciones: list[SeccionVista] = []

    mano_obra = SeccionVista("mano_obra", "Mano de obra")
    for l in presupuesto.lineas_personal:
        mano_obra.lineas.append(
            LineaVista(
                concepto=f"{l.categoria.grupo} — {l.categoria.nombre}",
                coste=Decimal(l.coste_mano_obra_total),
                personas=cant(l.cantidad_personas),
                dias=cant(l.dias_dedicacion),
                horas=cant(Decimal(l.cantidad_personas) * Decimal(l.dias_dedicacion) * HORAS_JORNADA_NORMAL),
            )
        )
    secciones.append(mano_obra)

    dietas = SeccionVista("dietas", "Dietas y desplazamiento")
    for l in presupuesto.lineas_personal:
        if l.numero_medias_dietas or l.numero_dietas_completas_cortas or l.numero_dietas_completas_largas:
            dietas.lineas.append(
                LineaVista(
                    concepto=f"{l.categoria.grupo} — {l.categoria.nombre} ({l.cantidad_personas} "
                    f"{'persona' if l.cantidad_personas == 1 else 'personas'})",
                    detalle=_texto_dietas(
                        l.numero_medias_dietas, l.numero_dietas_completas_cortas, l.numero_dietas_completas_largas
                    ),
                    coste=Decimal(l.coste_dietas_total),
                )
            )
    secciones.append(dietas)

    hotel_combustible = SeccionVista("hotel_combustible", "Hotel y combustible")
    if Decimal(presupuesto.coste_directo_hotel) > 0:
        hotel_combustible.lineas.append(
            LineaVista(concepto="Alojamiento (hotel)", coste=Decimal(presupuesto.coste_directo_hotel))
        )
    if Decimal(presupuesto.coste_directo_combustible) > 0:
        hotel_combustible.lineas.append(
            LineaVista(concepto="Combustible", coste=Decimal(presupuesto.coste_directo_combustible))
        )
    secciones.append(hotel_combustible)

    trabajos = SeccionVista("trabajos", "Trabajos a realizar")
    for l in presupuesto.lineas_trabajos:
        trabajos.lineas.append(LineaVista(concepto=l.concepto, cantidad=cant(l.cantidad), coste=Decimal(l.importe)))
    secciones.append(trabajos)

    materiales = SeccionVista("materiales", "Materiales y otros costes")
    for l in presupuesto.lineas_otros:
        materiales.lineas.append(LineaVista(concepto=l.concepto, cantidad=cant(l.cantidad), coste=Decimal(l.importe)))
    secciones.append(materiales)

    # Lo que no tiene valor (sección sin líneas o líneas a 0 €) no figura en el PDF.
    for s in secciones:
        s.lineas = [l for l in s.lineas if l.coste > 0]
    secciones = [s for s in secciones if s.lineas]

    # Reparto del precio de venta: primero entre secciones, luego entre sus líneas.
    precio_venta = Decimal(presupuesto.precio_venta)
    for seccion, total in zip(secciones, repartir_redondeando([s.coste for s in secciones], precio_venta)):
        seccion.total = total
        for linea, importe in zip(seccion.lineas, repartir_redondeando([l.coste for l in seccion.lineas], total)):
            linea.importe = importe
    return secciones


@dataclass
class TotalesCliente:
    base: Decimal
    iva_pct: Decimal
    iva_importe: Decimal
    total: Decimal


def totales_de(presupuesto, base: Decimal) -> TotalesCliente:
    """Base imponible, IVA y total tal como están guardados (iva_pct 0 = IVA no incluido)."""
    return TotalesCliente(
        base=Decimal(base),
        iva_pct=Decimal(presupuesto.iva_pct or 0),
        iva_importe=Decimal(presupuesto.iva_importe or 0),
        total=Decimal(presupuesto.precio_total_cliente),
    )


@dataclass
class DatosCliente:
    numero: str
    fecha: str
    valido_hasta: str
    secciones: list[SeccionVista]
    total_sin_iva: Decimal
    dias_validez: int = DIAS_VALIDEZ


def _fecha(fecha: date) -> str:
    return fecha.strftime("%d/%m/%Y")


def preparar_datos_cliente(presupuesto: Presupuesto) -> DatosCliente:
    secciones = preparar_secciones(presupuesto)
    return DatosCliente(
        numero=numero_visible(presupuesto),
        fecha=_fecha(presupuesto.fecha),
        valido_hasta=_fecha(presupuesto.fecha + timedelta(days=DIAS_VALIDEZ)),
        secciones=secciones,
        total_sin_iva=Decimal(presupuesto.precio_venta),
    )
