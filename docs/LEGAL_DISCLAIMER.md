# Aviso legal — PAYROLL CREATOR (MVP)

Esta aplicación es un **motor de cálculo de nómina de apoyo**, no un producto
homologado ni validado por ninguna asesoría laboral. Antes de usar las nóminas
generadas como documento oficial frente a trabajadores, Seguridad Social o
Hacienda, es imprescindible que una persona con capacitación jurídico-laboral
revise:

1. **Tablas salariales de convenio**: los convenios cargados en el seed
   (`backend/app/seed/convenios.py`) incluyen datos reales (Metal Madrid 2026,
   tomados del BOCM núm. 59 de 11/03/2026) y datos de **EJEMPLO** claramente
   marcados (Construcción, Comercio) que deben sustituirse por las tablas
   oficiales vigentes del convenio aplicable a cada empresa.

2. **Parámetros legales** (`backend/app/seed/parametros_legales.py`): SMI,
   tipos de cotización (contingencias comunes, desempleo, FP, FOGASA, MEI) y
   topes de bases son valores orientativos para 2026 y deben verificarse
   contra la Orden de Cotización a la Seguridad Social y el Real Decreto del
   SMI vigentes en el momento de generar cada nómina.

3. **Tabla de IRPF** (`backend/app/seed/tabla_irpf.py`): se aplica el
   procedimiento general simplificado (tarifa por tramos + reducción fija
   por hijos/discapacidad). El cálculo real de la retención (arts. 80-88 del
   Reglamento del IRPF) considera más circunstancias personales y familiares
   que no están implementadas en este MVP.

4. **Simplificaciones del motor de cálculo** (documentadas también en
   `backend/app/engine/calculo.py`):
   - Horas extraordinarias cotizadas con los tipos generales, en vez de los
     tipos especiales que la normativa prevé para ellas.
   - Incapacidad Temporal calculada como importe teórico (60%/75% de la base
     reguladora), sin gestionar el circuito de pago delegado empresa/INSS/mutua.
   - Embargos limitados de forma simplificada al SMI, sin aplicar la escala
     completa del art. 607 de la Ley de Enjuiciamiento Civil.

Todos los parámetros están modelados como **datos versionados y editables**
(tablas `parametros_legales`, `tabla_irpf`, `convenio_tablas_salariales`) para
que puedan actualizarse sin tocar código a medida que cambien las leyes, el
SMI, los convenios o las tablas de IRPF.

**Responsabilidad**: el uso de esta herramienta no sustituye el asesoramiento
de un graduado social, abogado laboralista o asesoría fiscal colegiada.
