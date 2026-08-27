"""Construye las estructuras del motor de cálculo a partir de los datos en BD."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.contrato import Contrato
from app.models.convenio import CategoriaProfesional, ConvenioDieta, ConvenioTablaSalarial
from app.models.empresa import Empresa
from app.models.parametro_legal import ParametroLegal
from app.models.tabla_irpf import TablaIRPF
from app.engine.tipos import DatosConvenioContrato, ParametrosCotizacion


def _valor_parametro(db: Session, clave: str, en_fecha: date, grupo_cotizacion: int | None = None) -> Decimal:
    query = db.query(ParametroLegal).filter(
        ParametroLegal.clave == clave,
        ParametroLegal.vigente_desde <= en_fecha,
    )
    if grupo_cotizacion is not None:
        query = query.filter(ParametroLegal.grupo_cotizacion == grupo_cotizacion)
    query = query.filter(
        (ParametroLegal.vigente_hasta.is_(None)) | (ParametroLegal.vigente_hasta >= en_fecha)
    )
    parametro = query.order_by(ParametroLegal.vigente_desde.desc()).first()
    if parametro is None:
        raise ValueError(f"Parámetro legal no encontrado: {clave} (grupo {grupo_cotizacion}) en {en_fecha}")
    return Decimal(parametro.valor)


def obtener_parametros_cotizacion(
    db: Session, en_fecha: date, grupo_cotizacion: int, tipo_contrato: str = "indefinido"
) -> ParametrosCotizacion:
    # El tipo de cotización por desempleo depende de si el contrato es
    # indefinido o temporal (art. 227 y ss. LGSS); cualquier otro valor de
    # tipo_contrato (formación, prácticas...) se trata como "indefinido" por
    # simplicidad — verificar el tipo aplicable en casos especiales.
    tipo_contrato_desempleo = "temporal" if tipo_contrato == "temporal" else "indefinido"
    return ParametrosCotizacion(
        tipo_cc_empresa_pct=_valor_parametro(db, "tipo_cc_empresa", en_fecha),
        tipo_cc_trabajador_pct=_valor_parametro(db, "tipo_cc_trabajador", en_fecha),
        tipo_desempleo_empresa_pct=_valor_parametro(db, f"tipo_desempleo_{tipo_contrato_desempleo}_empresa", en_fecha),
        tipo_desempleo_trabajador_pct=_valor_parametro(db, f"tipo_desempleo_{tipo_contrato_desempleo}_trabajador", en_fecha),
        tipo_fp_empresa_pct=_valor_parametro(db, "tipo_fp_empresa", en_fecha),
        tipo_fp_trabajador_pct=_valor_parametro(db, "tipo_fp_trabajador", en_fecha),
        tipo_fogasa_empresa_pct=_valor_parametro(db, "tipo_fogasa_empresa", en_fecha),
        tipo_mei_empresa_pct=_valor_parametro(db, "tipo_mei_empresa", en_fecha),
        tipo_mei_trabajador_pct=_valor_parametro(db, "tipo_mei_trabajador", en_fecha),
        tope_min_grupo_mensual=_valor_parametro(db, "tope_min_cotizacion", en_fecha, grupo_cotizacion),
        tope_max_mensual=_valor_parametro(db, "tope_max_cotizacion", en_fecha),
        smi_mensual=_valor_parametro(db, "smi_mensual", en_fecha),
        recargo_hora_extra_pct=_valor_parametro(db, "recargo_hora_extra_pct", en_fecha),
        recargo_hora_extra_nocturna_pct=_valor_parametro(db, "recargo_hora_extra_nocturna_pct", en_fecha),
        plus_nocturnidad_pct=_valor_parametro(db, "plus_nocturnidad_pct", en_fecha),
    )


def obtener_tramos_irpf(db: Session, anio: int) -> list[tuple[Decimal, Decimal | None, Decimal]]:
    tramos = (
        db.query(TablaIRPF)
        .filter(TablaIRPF.anio == anio)
        .order_by(TablaIRPF.base_desde_anual.asc())
        .all()
    )
    return [
        (Decimal(t.base_desde_anual), Decimal(t.base_hasta_anual) if t.base_hasta_anual is not None else None, Decimal(t.tipo_aplicable_pct))
        for t in tramos
    ]


def _numero_quinquenios_o_trienios(fecha_antiguedad: date, en_fecha: date, cada_anios: int = 5) -> int:
    if fecha_antiguedad is None or fecha_antiguedad > en_fecha:
        return 0
    anios_completos = (en_fecha.year - fecha_antiguedad.year) - (
        1 if (en_fecha.month, en_fecha.day) < (fecha_antiguedad.month, fecha_antiguedad.day) else 0
    )
    return max(0, anios_completos // cada_anios)


def obtener_datos_convenio_contrato(db: Session, contrato: Contrato, en_fecha: date) -> DatosConvenioContrato:
    tabla = (
        db.query(ConvenioTablaSalarial)
        .filter(
            ConvenioTablaSalarial.categoria_id == contrato.categoria_id,
            ConvenioTablaSalarial.vigente_desde <= en_fecha,
        )
        .filter(
            (ConvenioTablaSalarial.vigente_hasta.is_(None))
            | (ConvenioTablaSalarial.vigente_hasta >= en_fecha)
        )
        .order_by(ConvenioTablaSalarial.vigente_desde.desc())
        .first()
    )
    if tabla is None:
        raise ValueError("No hay tabla salarial vigente para esta categoría en la fecha indicada")

    convenio = contrato.convenio
    categoria = contrato.categoria
    fecha_antiguedad = contrato.fecha_antiguedad or contrato.fecha_inicio

    dieta = (
        db.query(ConvenioDieta)
        .filter(
            ConvenioDieta.convenio_id == convenio.id,
            ConvenioDieta.vigente_desde <= en_fecha,
        )
        .filter((ConvenioDieta.vigente_hasta.is_(None)) | (ConvenioDieta.vigente_hasta >= en_fecha))
        .order_by(ConvenioDieta.vigente_desde.desc())
        .first()
    )

    return DatosConvenioContrato(
        nombre_convenio=convenio.nombre,
        numero_pagas=convenio.numero_pagas,
        jornada_anual_horas=Decimal(convenio.jornada_anual_horas),
        salario_convenio_mensual=Decimal(tabla.salario_convenio_mensual),
        base_calculo_complementos_mensual=Decimal(
            tabla.base_calculo_complementos_mensual or tabla.salario_convenio_mensual
        ),
        valor_quinquenio_o_trienio=Decimal(tabla.valor_quinquenio_o_trienio or 0),
        plus_convenio_mensual=Decimal(tabla.plus_convenio_mensual or 0),
        jornada_porcentaje=Decimal(contrato.jornada_porcentaje),
        tipo_contrato=contrato.tipo_contrato,
        pagas_extra_prorrateadas=contrato.pagas_extra_prorrateadas,
        numero_quinquenios_o_trienios=_numero_quinquenios_o_trienios(fecha_antiguedad, en_fecha),
        grupo_cotizacion=categoria.grupo_cotizacion,
        salario_pactado_mensual=Decimal(contrato.salario_pactado_mensual) if contrato.salario_pactado_mensual else None,
        media_dieta=Decimal(dieta.media_dieta) if dieta else Decimal("0"),
        dieta_completa_corta=Decimal(dieta.dieta_completa_corta) if dieta else Decimal("0"),
        dieta_completa_larga=Decimal(dieta.dieta_completa_larga) if dieta else Decimal("0"),
        tipo_at_ep_pct=Decimal(contrato.trabajador.empresa.tipo_at_ep_pct),
        complemento_mensual=Decimal(contrato.complemento_mensual or 0),
    )


def obtener_datos_convenio_categoria(
    db: Session,
    categoria_id: int,
    empresa_id: int,
    en_fecha: date,
    jornada_porcentaje: Decimal = Decimal("100"),
    complemento_mensual: Decimal = Decimal("0"),
    pagas_extra_prorrateadas: bool = True,
) -> DatosConvenioContrato:
    """
    Igual que `obtener_datos_convenio_contrato`, pero sin necesitar un
    contrato real: se usa para simular el coste de una categoría de convenio
    en una empresa concreta (presupuestos de proyecto). No hay antigüedad
    real, así que se asume 0 quinquenios/trienios.
    """
    categoria = db.get(CategoriaProfesional, categoria_id)
    if categoria is None:
        raise ValueError("Categoría profesional no encontrada")

    empresa = db.get(Empresa, empresa_id)
    if empresa is None:
        raise ValueError("Empresa no encontrada")

    tabla = (
        db.query(ConvenioTablaSalarial)
        .filter(
            ConvenioTablaSalarial.categoria_id == categoria_id,
            ConvenioTablaSalarial.vigente_desde <= en_fecha,
        )
        .filter(
            (ConvenioTablaSalarial.vigente_hasta.is_(None))
            | (ConvenioTablaSalarial.vigente_hasta >= en_fecha)
        )
        .order_by(ConvenioTablaSalarial.vigente_desde.desc())
        .first()
    )
    if tabla is None:
        raise ValueError("No hay tabla salarial vigente para esta categoría en la fecha indicada")

    convenio = categoria.convenio

    dieta = (
        db.query(ConvenioDieta)
        .filter(
            ConvenioDieta.convenio_id == convenio.id,
            ConvenioDieta.vigente_desde <= en_fecha,
        )
        .filter((ConvenioDieta.vigente_hasta.is_(None)) | (ConvenioDieta.vigente_hasta >= en_fecha))
        .order_by(ConvenioDieta.vigente_desde.desc())
        .first()
    )

    return DatosConvenioContrato(
        nombre_convenio=convenio.nombre,
        numero_pagas=convenio.numero_pagas,
        jornada_anual_horas=Decimal(convenio.jornada_anual_horas),
        salario_convenio_mensual=Decimal(tabla.salario_convenio_mensual),
        base_calculo_complementos_mensual=Decimal(
            tabla.base_calculo_complementos_mensual or tabla.salario_convenio_mensual
        ),
        valor_quinquenio_o_trienio=Decimal(tabla.valor_quinquenio_o_trienio or 0),
        plus_convenio_mensual=Decimal(tabla.plus_convenio_mensual or 0),
        jornada_porcentaje=jornada_porcentaje,
        tipo_contrato="indefinido",
        pagas_extra_prorrateadas=pagas_extra_prorrateadas,
        numero_quinquenios_o_trienios=0,
        grupo_cotizacion=categoria.grupo_cotizacion,
        salario_pactado_mensual=None,
        media_dieta=Decimal(dieta.media_dieta) if dieta else Decimal("0"),
        dieta_completa_corta=Decimal(dieta.dieta_completa_corta) if dieta else Decimal("0"),
        dieta_completa_larga=Decimal(dieta.dieta_completa_larga) if dieta else Decimal("0"),
        tipo_at_ep_pct=Decimal(empresa.tipo_at_ep_pct),
        complemento_mensual=complemento_mensual,
    )
