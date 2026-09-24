"""
Catálogo inicial de partidas de precios para "Presupuesto por items",
importado de Base_precios_profesional_comunicaciones_2026.xlsx (hoja
"Precios 2026"). Cada partida es mano de obra + material + medios
auxiliares por unidad de obra, con un margen del 20% ya aplicado en el
precio de venta. Son precios orientativos del sector — se pueden editar o
desactivar desde Admin → Catálogo de partidas.
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.partida_catalogo import PartidaCatalogo

MARGEN_DEFECTO = Decimal("20")

# (familia, nombre, unidad, precio_coste_mo, precio_material, precio_medios_aux, observaciones)
PARTIDAS_DEFECTO = [
    ("Cableado", "Tendido FTP Cat6/Cat6A", "m", "1.01", "0.27", "0.07",
     "Solo mano de obra; bandeja/canalización existente"),
    ("Cableado", "Tendido UTP Cat6/Cat6A", "m", "0.90", "0.24", "0.06", "Solo mano de obra"),
    ("Cableado", "Tendido cable multipar / alarma 6+2", "m", "1.01", "0.27", "0.07",
     "Incluye guiado y fijación básica"),
    ("Cableado", "Tendido cable 3G6 / alimentación", "m", "1.39", "0.37", "0.09", "Sin tubo/bandeja"),
    ("Cableado", "Tendido fibra óptica en bandeja", "m", "0.86", "0.23", "0.06", "Tendido y peinado"),
    ("Cableado", "Tendido fibra por tubo/enterrado", "m", "1.69", "0.45", "0.11", "Sin obra civil"),
    ("Canalización", "Canaleta pequeña hasta 40 mm", "m", "3.75", "1.00", "0.25", "Montaje"),
    ("Canalización", "Canaleta 60–100 mm", "m", "5.25", "1.40", "0.35", "Montaje"),
    ("Canalización", "Bandeja rejilla 60–100 mm", "m", "5.25", "1.40", "0.35", "Montaje"),
    ("Canalización", "Bandeja 150–300 mm", "m", "7.50", "2.00", "0.50", "Montaje"),
    ("Canalización", "Tubo corrugado/rígido", "m", "3.00", "0.80", "0.20", "Sin rozas"),
    ("Racks", "Montaje rack mural 6–12U", "ud", "46.88", "12.50", "3.12", "Anclaje y montaje"),
    ("Racks", "Montaje rack suelo 22–42U", "ud", "93.75", "25.00", "6.25", "Nivelación y montaje"),
    ("Racks", "Organización/peinado rack", "ud", "67.50", "18.00", "4.50", "Por rack"),
    ("Racks", "Montaje PDU/regleta", "ud", "16.88", "4.50", "1.12", "En rack"),
    ("Racks", "Montaje patch panel 24 puertos", "ud", "26.25", "7.00", "1.75", "Sin certificación"),
    ("Red", "Ponchado keystone RJ45", "ud", "5.25", "1.40", "0.35", "Cat6/Cat6A"),
    ("Red", "Conector RJ45 macho", "ud", "4.12", "1.10", "0.28", "Crimpado"),
    ("Red", "Certificación punto cobre DSX", "ud", "8.62", "2.30", "0.58", "Certificación y etiquetado"),
    ("Red", "Etiquetado punto de red", "ud", "1.69", "0.45", "0.11", None),
    ("Red", "Montaje switch en rack", "ud", "22.50", "6.00", "1.50", "Configuración excluida"),
    ("Red", "Configuración básica switch", "ud", "41.25", "11.00", "2.75", "IP, nombre, gateway, VLAN básica"),
    ("CCTV", "Montaje cámara fija", "ud", "35.62", "9.50", "2.38", "Interior/exterior accesible"),
    ("CCTV", "Montaje cámara domo", "ud", "41.25", "11.00", "2.75", None),
    ("CCTV", "Montaje cámara PTZ", "ud", "82.50", "22.00", "5.50", "Sin medios especiales"),
    ("CCTV", "Montaje NVR/DVR", "ud", "50.62", "13.50", "3.38", None),
    ("CCTV", "Configuración cámara IP", "ud", "16.88", "4.50", "1.12", "IP, contraseña, nombre, OSD básico"),
    ("CCTV", "Configuración NVR", "ud", "67.50", "18.00", "4.50", "Grabación, red y cámaras"),
    ("CCTV", "Ajuste/encuadre cámara", "ud", "16.88", "4.50", "1.12", None),
    ("CCTV", "Montaje báculo cámara", "ud", "127.50", "34.00", "8.50", "Sin cimentación"),
    ("CCTV", "Cimentación/obra para báculo", "ud", "187.50", "50.00", "12.50", "Variable según terreno"),
    ("Alarma", "Tendido alarma 6+2", "m", "1.01", "0.27", "0.07", None),
    ("Alarma", "Montaje detector PIR", "ud", "26.25", "7.00", "1.75", "Cableado incluido si cercano"),
    ("Alarma", "Montaje contacto magnético", "ud", "20.62", "5.50", "1.38", None),
    ("Alarma", "Montaje sirena exterior", "ud", "37.50", "10.00", "2.50", "Cableada"),
    ("Alarma", "Montaje teclado", "ud", "26.25", "7.00", "1.75", None),
    ("Alarma", "Montaje central alarma", "ud", "75.00", "20.00", "5.00", None),
    ("Alarma", "Programación central alarma", "ud", "97.50", "26.00", "6.50", "Según sistema"),
    ("Alarma", "Alta/programación zona", "ud", "9.75", "2.60", "0.65", None),
    ("Alarma", "Prueba completa / puesta en marcha", "ud", "63.75", "17.00", "4.25", None),
    ("Fibra", "Fusión fibra óptica", "ud", "12.00", "3.20", "0.80", "Fusión + organización; sin desplazamiento"),
    ("Fibra", "Preparación/empalme en bandeja", "ud", "8.62", "2.30", "0.58", None),
    ("Fibra", "Terminación pigtail", "ud", "8.62", "2.30", "0.58", None),
    ("Fibra", "Medida OTDR", "ud", "11.25", "3.00", "0.75", "Por fibra y dirección"),
    ("Fibra", "Medida OTDR bidireccional", "ud", "22.50", "6.00", "1.50", "Por enlace/fibra, según procedimiento"),
    ("Fibra", "Medida potencia/inserción", "ud", "8.62", "2.30", "0.58", None),
    ("Fibra", "Certificación enlace fibra", "ud", "22.50", "6.00", "1.50", "OTDR + potencia según alcance"),
    ("Fibra", "Montaje torpedo/caja de empalme", "ud", "56.25", "15.00", "3.75", "Sin material"),
    ("Armarios", "Montaje armario comunicaciones", "ud", "90.00", "24.00", "6.00", "Según tamaño"),
    ("Armarios", "Montaje armario exterior", "ud", "120.00", "32.00", "8.00", None),
    ("Armarios", "Montaje caja de paso", "ud", "24.38", "6.50", "1.62", None),
    ("Armarios", "Prensaestopas y entradas cable", "ud", "5.25", "1.40", "0.35", "Mano de obra por entrada"),
    ("Otros", "Desplazamiento técnico", "h", "30.00", "8.00", "2.00", "Como coste de trabajo, no transporte"),
    ("Otros", "Hora oficial telecomunicaciones", "h", "25.50", "6.80", "1.70", "Referencia comercial para presupuesto"),
    ("Otros", "Hora ayudante técnico", "h", "20.25", "5.40", "1.35", None),
    ("Otros", "Trabajo en altura hasta 6 m", "h", "33.75", "9.00", "2.25", "Suplemento por técnico"),
    ("Otros", "Pareja de técnicos", "h", "48.75", "13.00", "3.25", "Hora de equipo"),
    ("Otros", "Jornada técnico 8 h", "día", "204.38", "54.50", "13.62", "Sin dietas/desplazamiento"),
    ("Otros", "Jornada pareja 8 h", "día", "390.00", "104.00", "26.00", "Sin dietas/desplazamiento"),
    ("Otros", "Dietas/alojamiento", "día", "0", "0", "0", "Añadir cuando proceda"),
]


def seed_partidas_catalogo(db: Session) -> None:
    if db.query(PartidaCatalogo).first() is not None:
        return
    for familia, nombre, unidad, mo, material, medios_aux, observaciones in PARTIDAS_DEFECTO:
        mo_d = Decimal(mo)
        material_d = Decimal(material)
        medios_aux_d = Decimal(medios_aux)
        coste_directo = mo_d + material_d + medios_aux_d
        precio_venta = (coste_directo * (1 + MARGEN_DEFECTO / Decimal(100))).quantize(Decimal("0.01"))
        db.add(
            PartidaCatalogo(
                familia=familia,
                nombre=nombre,
                unidad=unidad,
                precio_coste_mo=mo_d,
                precio_material=material_d,
                precio_medios_aux=medios_aux_d,
                coste_directo=coste_directo,
                margen_pct=MARGEN_DEFECTO,
                precio_venta=precio_venta,
                observaciones=observaciones,
                activo=True,
            )
        )
    db.commit()
