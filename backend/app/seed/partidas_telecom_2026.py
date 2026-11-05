"""
Partidas de la tarifa profesional de telecomunicaciones (España, noviembre 2026),
importadas de "Partidas telecomunicaciones_Espana_2026.xlsx". Precios de VENTA sin IVA:
se guardan con el margen a 0 (precio de venta = precio del Excel), como las partidas
creadas con "Conozco solo el precio de venta". Se añaden sin tocar las partidas existentes.
"""

# (grupo, partida, unidad, precio de venta €, alcance, observaciones internas)
PARTIDAS_TELECOM_2026 = [
    ('Fibra', 'Tendido de fibra óptica entre edificios por canalización/tubería existente, incluyendo paso por arquetas', 'm', '1.65', 'Sin suministro de cable, obra civil, desatascos ni medios especiales.', None),
    ('Fibra', 'Fusión individual de fibra, preparación, protector termorretráctil y organización en bandeja/armario', 'fusión', '17.50', 'No incluye pigtail. Incluye protector de empalme; OTDR se valora en partida separada por enlace.', None),
    ('Fibra', 'Certificación de enlace de fibra mediante OTDR, trazas e informe de resultados', 'enlace', '12.50', 'Se factura por enlace óptico, no por fusión. Medición en dos longitudes de onda y bidireccional de acuerdo a los parámetros solicitados por el cliente.', None),
    ('Fibra', 'Conectorización mediante latiguillos de fibra entre armario de fibra y rack a través de tubo flexible', 'ud', '10.00', 'Incluye guiado y conexionado; no incluye suministro de latiguillos ni tubo.', None),
    ('Fibra', 'Etiquetado de extremos de fibra y monotubo', 'ud', '5.50', 'Etiquetado legible en ambos extremos accesibles.', None),
    ('UTP', 'Terminación hembra UTP en rack repartidor, certificación Cat6A de enlace permanente e informe', 'enlace', '15.50', 'Incluye terminación, prueba Cat6A con certificador y registro individual. Sin suministro de keystone/patch panel.', None),
    ('UTP', 'Subsanación de posibles problemas en conectores de patch panel', 'ud', '12.00', 'Mano de obra y nueva prueba del enlace, verificación de correspondencia cableado; materiales especiales aparte.', None),
    ('UTP', 'Etiquetado de puestos de trabajo', 'ud', '2.50', 'Identificación según nomenclatura facilitada.', None),
    ('UTP', 'Etiquetado de cables en puesto de trabajo y rack repartidor', 'enlace', '3.50', 'Identificación coordinada en ambos extremos.', None),
    ('UTP', 'Realización y conectorización de latiguillos UTP', 'ud', '8.50', 'Mano de obra; cable y conectores especiales/suministro aparte.', None),
    ('UTP', 'Conexión de latiguillos UTP en rack principal desde patch panel a equipo final', 'ud', '4.50', 'Incluye conexión y ordenación básica.', None),
    ('UTP', 'Tirada de cable UTP por canalización existente (si fuera necesario)', 'm', '1.25', 'Sin suministro de cable ni obra civil.', 'Cantidad pendiente'),
    ('FTP', 'Terminación hembra FTP en rack repartidor, certificación Cat6A de enlace permanente e informe', 'enlace', '25.00', 'Incluye terminación apantallada, continuidad de pantalla, prueba Cat6A y registro individual.', None),
    ('FTP', 'Subsanación de posibles problemas en conectores de patch panel', 'ud', '12.00', 'Mano de obra y nueva prueba; materiales especiales aparte.', None),
    ('FTP', 'Subsanación de posibles problemas en conectores en extremos de cámaras', 'ud', '14.00', 'Incluye revisión de terminación apantallada y nueva comprobación.', None),
    ('FTP', 'Etiquetado de extremos de cables en rack repartidor y latiguillos FTP', 'enlace', '3.50', 'Identificación coordinada en ambos extremos.', None),
    ('FTP', 'Realización y conectorización de latiguillos FTP entre rack de cobre y rack principal', 'ud', '9.50', 'Incluye preparación y terminación apantallada; material especial aparte.', None),
    ('FTP', 'Conexión de latiguillos FTP en rack principal desde patch panel a equipo final', 'ud', '5.50', 'Incluye conexión y ordenación básica.', None),
    ('FTP', 'Tirada de cable FTP por canalización existente (si fuera necesario)', 'm', '1.55', 'Sin suministro de cable ni obra civil.', 'Cantidad pendiente'),
    ('Rack cobre', 'Etiquetado de patch panels en rack de cobre', 'patch panel', '12.00', 'Identificación de puertos conforme a esquema.', None),
    ('Rack cobre', 'Peinado y adecuación de racks de cobre: colocación de cables y embridado', 'rack', '165.00', 'Ordenación de cableado existente; sin sustitución de equipos ni latiguillos.', None),
    ('Racks principales', 'Peinado y adecuación de racks principales, colocación de cables, embridado y conexionado eléctrico según esquema', 'rack', '225.00', 'Conexionado a tomas existentes; no incluye modificaciones de cuadros ni nuevas líneas eléctricas.', None),
    ('Racks principales', 'Etiquetado de patch panels en racks principales', 'patch panel', '12.00', 'Identificación de puertos conforme a esquema.', None),
    ('Cámaras perimetrales', 'Instalación de báculo exterior sobre peana de hormigón existente, aplomado y fijación', 'báculo', '225.00', 'Incluye montaje y nivelación con anclajes disponibles. Sin báculo, obra civil, grúa o PEMP.', None),
    ('Cámaras perimetrales', 'Montaje de cámara PTZ sobre báculo/soporte, conexionado físico y prueba funcional básica', 'cámara PTZ', '185.00', 'Sin cámara ni soporte especial.', 'Cantidad pendiente de desglose de las 26 cámaras'),
    ('Cámaras perimetrales', 'Montaje de cámara fija Bullet/térmica sobre báculo/soporte, conexionado físico y encuadre inicial', 'cámara fija', '95.00', 'Sin cámara ni soporte especial.', 'Cantidad pendiente de desglose de las 26 cámaras'),
    ('Cámaras perimetrales', 'Conexión FTP desde cámara en báculo a armario en la base, conexionado', 'cámara', '19.50', 'Presupone cable instalado y disponible en ambos extremos; tendido adicional aparte.', None),
    ('Cámaras perimetrales', 'Instalación de armario exterior sobre peana existente, sin obra civil', 'armario', '125.00', 'No incluye armario, peana, obra civil ni medios de elevación.', None),
    ('Cámaras perimetrales', 'Instalación de elementos interiores de armario exterior conforme a esquema', 'armario', '95.00', 'Montaje y conexionado de elementos suministrados y ubicados en el armario.', None),
    ('Cámaras interior / exterior', 'Orientación final de cámaras instaladas: Bullet en fachadas y minidomos en interior', 'cámara', '42.00', 'Ajuste de encuadre y comprobación visual. No incluye reconfiguración avanzada del sistema.', None),
]
