"""
Diario de Ruta — API
Reemplaza el acceso directo a SQLite local por una API REST sobre una base
de datos central (Postgres en la nube). Cualquier dispositivo que hable con
esta API ve siempre los mismos datos: así es como se resuelve la
sincronización entre PC y celular.
"""
import os
from datetime import date, datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
import schemas
from auth import verificar_api_key
from db import Base, SessionLocal, engine, get_db

app = FastAPI(title="Diario de Ruta API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # protegido por API key, no por origen
    allow_methods=["*"],
    allow_headers=["*"],
)


def ahora():
    return datetime.now().isoformat(timespec="seconds")


def hoy():
    return date.today().isoformat()


DEFAULT_CUENTAS = [
    ("Efectivo", 1, 0),
    ("Banco", 1, 1),
    ("Ingresos", 0, 2),
    ("Gastos", 0, 3),
]


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Cuenta).count() == 0:
            for nombre, incluye, orden in DEFAULT_CUENTAS:
                db.add(models.Cuenta(nombre=nombre, incluye_en_total=incluye, orden=orden))
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


# Todas las rutas de datos requieren la API key
DEP = [Depends(verificar_api_key)]


# ================= 1. DIARIO =================

@app.get("/diario/{fecha}", response_model=Optional[schemas.DiarioOut], dependencies=DEP)
def obtener_diario(fecha: str, db: Session = Depends(get_db)):
    return db.get(models.Diario, fecha)


@app.put("/diario/{fecha}", response_model=schemas.DiarioOut, dependencies=DEP)
def guardar_diario(fecha: str, body: schemas.DiarioIn, db: Session = Depends(get_db)):
    row = db.get(models.Diario, fecha)
    if row:
        row.contenido = body.contenido
        row.actualizado_en = ahora()
    else:
        row = models.Diario(fecha=fecha, contenido=body.contenido, actualizado_en=ahora())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/diario", response_model=List[schemas.DiarioOut], dependencies=DEP)
def listar_diario_historico(db: Session = Depends(get_db)):
    return db.query(models.Diario).order_by(models.Diario.fecha.desc()).all()


# ================= 2. HÁBITOS =================

@app.get("/habitos", response_model=List[schemas.HabitoOut], dependencies=DEP)
def listar_habitos(solo_activos: bool = True, db: Session = Depends(get_db)):
    q = db.query(models.Habito)
    if solo_activos:
        q = q.filter(models.Habito.activo == 1)
    return q.order_by(models.Habito.orden).all()


@app.post("/habitos", response_model=schemas.HabitoOut, dependencies=DEP)
def crear_habito(body: schemas.HabitoIn, db: Session = Depends(get_db)):
    existente = db.query(models.Habito).filter(models.Habito.nombre == body.nombre.strip()).first()
    if existente:
        return existente
    max_orden = db.query(models.Habito).count()
    row = models.Habito(nombre=body.nombre.strip(), orden=max_orden + 1)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/habitos/{habito_id}", status_code=204, dependencies=DEP)
def eliminar_habito(habito_id: int, db: Session = Depends(get_db)):
    db.query(models.HabitoRegistro).filter(models.HabitoRegistro.habito_id == habito_id).delete()
    db.query(models.Habito).filter(models.Habito.id == habito_id).delete()
    db.commit()


@app.post("/habitos/registro", response_model=schemas.HabitoRegistroOut, dependencies=DEP)
def agregar_registro_habito(body: schemas.HabitoRegistroIn, db: Session = Depends(get_db)):
    row = models.HabitoRegistro(
        habito_id=body.habito_id, fecha=body.fecha,
        tiempo=(body.tiempo or "").strip() or None,
        calificacion=body.calificacion,
        nota=(body.nota or "").strip() or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    habito = db.get(models.Habito, row.habito_id)
    return schemas.HabitoRegistroOut(**row.__dict__, habito_nombre=habito.nombre if habito else None)


@app.get("/habitos/registro/{fecha}", response_model=List[schemas.HabitoRegistroOut], dependencies=DEP)
def listar_registro_habitos(fecha: str, db: Session = Depends(get_db)):
    rows = (
        db.query(models.HabitoRegistro, models.Habito.nombre)
        .join(models.Habito, models.Habito.id == models.HabitoRegistro.habito_id)
        .filter(models.HabitoRegistro.fecha == fecha)
        .order_by(models.HabitoRegistro.id)
        .all()
    )
    return [
        schemas.HabitoRegistroOut(**r.__dict__, habito_nombre=nombre) for r, nombre in rows
    ]


@app.get("/habitos/registro-semana", response_model=dict, dependencies=DEP)
def listar_registro_habitos_semana(fechas: List[str] = Query(default=[]), db: Session = Depends(get_db)):
    resultado = {f: [] for f in fechas}
    if not fechas:
        return resultado
    rows = (
        db.query(models.HabitoRegistro, models.Habito.nombre)
        .join(models.Habito, models.Habito.id == models.HabitoRegistro.habito_id)
        .filter(models.HabitoRegistro.fecha.in_(fechas))
        .order_by(models.HabitoRegistro.fecha, models.HabitoRegistro.id)
        .all()
    )
    for r, nombre in rows:
        resultado[r.fecha].append(
            schemas.HabitoRegistroOut(**r.__dict__, habito_nombre=nombre).model_dump()
        )
    return resultado


@app.delete("/habitos/registro/{registro_id}", status_code=204, dependencies=DEP)
def eliminar_registro_habito(registro_id: int, db: Session = Depends(get_db)):
    db.query(models.HabitoRegistro).filter(models.HabitoRegistro.id == registro_id).delete()
    db.commit()


# ================= 3. CONOCIMIENTO INTELECTUAL =================

@app.get("/conocimientos", response_model=List[schemas.ConocimientoOut], dependencies=DEP)
def listar_conocimientos(fecha: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Conocimiento)
    if fecha:
        q = q.filter(models.Conocimiento.fecha == fecha).order_by(models.Conocimiento.id.desc())
    else:
        q = q.order_by(models.Conocimiento.fecha.desc())
    return q.all()


@app.post("/conocimientos", response_model=schemas.ConocimientoOut, dependencies=DEP)
def agregar_conocimiento(body: schemas.ConocimientoIn, db: Session = Depends(get_db)):
    row = models.Conocimiento(fecha=body.fecha, descripcion=body.descripcion.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/conocimientos/{item_id}", status_code=204, dependencies=DEP)
def eliminar_conocimiento(item_id: int, db: Session = Depends(get_db)):
    db.query(models.Conocimiento).filter(models.Conocimiento.id == item_id).delete()
    db.commit()


@app.get("/proyectos", response_model=List[schemas.ProyectoIntelectualOut], dependencies=DEP)
def listar_proyectos(fecha: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.ProyectoIntelectual)
    if fecha:
        q = q.filter(models.ProyectoIntelectual.fecha == fecha).order_by(models.ProyectoIntelectual.id.desc())
    else:
        q = q.order_by(models.ProyectoIntelectual.fecha.desc())
    return q.all()


@app.post("/proyectos", response_model=schemas.ProyectoIntelectualOut, dependencies=DEP)
def agregar_proyecto(body: schemas.ProyectoIntelectualIn, db: Session = Depends(get_db)):
    row = models.ProyectoIntelectual(fecha=body.fecha, nombre=body.nombre.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.patch("/proyectos/{item_id}", response_model=schemas.ProyectoIntelectualOut, dependencies=DEP)
def cambiar_estado_proyecto(item_id: int, body: schemas.ProyectoEstadoIn, db: Session = Depends(get_db)):
    row = db.get(models.ProyectoIntelectual, item_id)
    if not row:
        raise HTTPException(404, "No encontrado")
    row.estado = body.estado
    db.commit()
    db.refresh(row)
    return row


@app.delete("/proyectos/{item_id}", status_code=204, dependencies=DEP)
def eliminar_proyecto(item_id: int, db: Session = Depends(get_db)):
    db.query(models.ProyectoIntelectual).filter(models.ProyectoIntelectual.id == item_id).delete()
    db.commit()


@app.get("/temas", response_model=List[schemas.TemaOut], dependencies=DEP)
def listar_temas(solo_activos: bool = True, db: Session = Depends(get_db)):
    q = db.query(models.Tema)
    if solo_activos:
        q = q.filter(models.Tema.activo == 1)
    return q.order_by(models.Tema.orden).all()


@app.post("/temas", response_model=schemas.TemaOut, dependencies=DEP)
def crear_tema(body: schemas.TemaIn, db: Session = Depends(get_db)):
    existente = db.query(models.Tema).filter(models.Tema.nombre == body.nombre.strip()).first()
    if existente:
        return existente
    max_orden = db.query(models.Tema).count()
    row = models.Tema(nombre=body.nombre.strip(), orden=max_orden + 1)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/temas/{tema_id}", status_code=204, dependencies=DEP)
def eliminar_tema(tema_id: int, db: Session = Depends(get_db)):
    db.query(models.TemaRegistro).filter(models.TemaRegistro.tema_id == tema_id).delete()
    db.query(models.Tema).filter(models.Tema.id == tema_id).delete()
    db.commit()


@app.post("/temas/registro", response_model=schemas.TemaRegistroOut, dependencies=DEP)
def agregar_registro_tema(body: schemas.TemaRegistroIn, db: Session = Depends(get_db)):
    row = models.TemaRegistro(
        tema_id=body.tema_id, fecha=body.fecha,
        tiempo=(body.tiempo or "").strip() or None,
        calificacion=body.calificacion,
        nota=(body.nota or "").strip() or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    tema = db.get(models.Tema, row.tema_id)
    return schemas.TemaRegistroOut(**row.__dict__, tema_nombre=tema.nombre if tema else None)


@app.get("/temas/registro/{fecha}", response_model=List[schemas.TemaRegistroOut], dependencies=DEP)
def listar_registro_temas(fecha: str, db: Session = Depends(get_db)):
    rows = (
        db.query(models.TemaRegistro, models.Tema.nombre)
        .join(models.Tema, models.Tema.id == models.TemaRegistro.tema_id)
        .filter(models.TemaRegistro.fecha == fecha)
        .order_by(models.TemaRegistro.id)
        .all()
    )
    return [schemas.TemaRegistroOut(**r.__dict__, tema_nombre=nombre) for r, nombre in rows]


@app.get("/temas/registro-semana", response_model=dict, dependencies=DEP)
def listar_registro_temas_semana(fechas: List[str] = Query(default=[]), db: Session = Depends(get_db)):
    resultado = {f: [] for f in fechas}
    if not fechas:
        return resultado
    rows = (
        db.query(models.TemaRegistro, models.Tema.nombre)
        .join(models.Tema, models.Tema.id == models.TemaRegistro.tema_id)
        .filter(models.TemaRegistro.fecha.in_(fechas))
        .order_by(models.TemaRegistro.fecha, models.TemaRegistro.id)
        .all()
    )
    for r, nombre in rows:
        resultado[r.fecha].append(schemas.TemaRegistroOut(**r.__dict__, tema_nombre=nombre).model_dump())
    return resultado


@app.delete("/temas/registro/{registro_id}", status_code=204, dependencies=DEP)
def eliminar_registro_tema(registro_id: int, db: Session = Depends(get_db)):
    db.query(models.TemaRegistro).filter(models.TemaRegistro.id == registro_id).delete()
    db.commit()


# ================= 4. EJERCICIO Y SUEÑO =================

@app.get("/ejercicios/{fecha}", response_model=List[schemas.EjercicioOut], dependencies=DEP)
def listar_ejercicios(fecha: str, db: Session = Depends(get_db)):
    return db.query(models.Ejercicio).filter(models.Ejercicio.fecha == fecha).order_by(models.Ejercicio.id).all()


@app.get("/ejercicios-semana", response_model=dict, dependencies=DEP)
def listar_ejercicios_semana(fechas: List[str] = Query(default=[]), db: Session = Depends(get_db)):
    resultado = {f: [] for f in fechas}
    if not fechas:
        return resultado
    rows = (
        db.query(models.Ejercicio)
        .filter(models.Ejercicio.fecha.in_(fechas))
        .order_by(models.Ejercicio.fecha, models.Ejercicio.id)
        .all()
    )
    for r in rows:
        resultado[r.fecha].append(schemas.EjercicioOut.model_validate(r).model_dump())
    return resultado


@app.post("/ejercicios", response_model=schemas.EjercicioOut, dependencies=DEP)
def agregar_ejercicio(body: schemas.EjercicioIn, db: Session = Depends(get_db)):
    row = models.Ejercicio(
        fecha=body.fecha, nombre=body.nombre.strip(),
        repeticiones=(body.repeticiones or "").strip(),
        tiempo=(body.tiempo or "").strip(),
        calificacion=body.calificacion,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/ejercicios/{item_id}", status_code=204, dependencies=DEP)
def eliminar_ejercicio(item_id: int, db: Session = Depends(get_db)):
    db.query(models.Ejercicio).filter(models.Ejercicio.id == item_id).delete()
    db.commit()


@app.get("/sueno/{fecha}", response_model=Optional[schemas.SuenoOut], dependencies=DEP)
def obtener_sueno(fecha: str, db: Session = Depends(get_db)):
    return db.get(models.Sueno, fecha)


@app.put("/sueno/{fecha}", response_model=schemas.SuenoOut, dependencies=DEP)
def guardar_sueno(fecha: str, body: schemas.SuenoIn, db: Session = Depends(get_db)):
    row = db.get(models.Sueno, fecha)
    if row:
        row.horas, row.calidad, row.nota = body.horas, body.calidad, body.nota
    else:
        row = models.Sueno(fecha=fecha, horas=body.horas, calidad=body.calidad, nota=body.nota)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/sueno-semana", response_model=dict, dependencies=DEP)
def sueno_semana(fechas: List[str] = Query(default=[]), db: Session = Depends(get_db)):
    if not fechas:
        return {}
    rows = db.query(models.Sueno).filter(models.Sueno.fecha.in_(fechas)).all()
    return {r.fecha: schemas.SuenoOut.model_validate(r).model_dump() for r in rows}


# ================= 5. ALIMENTACIÓN =================

@app.get("/alimentacion/{fecha}", response_model=List[schemas.AlimentacionOut], dependencies=DEP)
def listar_alimentos(fecha: str, tipo: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Alimentacion).filter(models.Alimentacion.fecha == fecha)
    if tipo:
        q = q.filter(models.Alimentacion.tipo == tipo)
    return q.order_by(models.Alimentacion.tipo, models.Alimentacion.id).all()


@app.post("/alimentacion", response_model=schemas.AlimentacionOut, dependencies=DEP)
def agregar_alimento(body: schemas.AlimentacionIn, db: Session = Depends(get_db)):
    row = models.Alimentacion(fecha=body.fecha, tipo=body.tipo, descripcion=body.descripcion.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/alimentacion/{item_id}", status_code=204, dependencies=DEP)
def eliminar_alimento(item_id: int, db: Session = Depends(get_db)):
    db.query(models.Alimentacion).filter(models.Alimentacion.id == item_id).delete()
    db.commit()


# ================= 6. FINANZAS =================

@app.get("/ideas-negocio", response_model=List[schemas.IdeaNegocioOut], dependencies=DEP)
def listar_ideas_negocio(fecha: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.IdeaNegocio)
    if fecha:
        q = q.filter(models.IdeaNegocio.fecha == fecha).order_by(models.IdeaNegocio.id.desc())
    else:
        q = q.order_by(models.IdeaNegocio.fecha.desc())
    return q.all()


@app.post("/ideas-negocio", response_model=schemas.IdeaNegocioOut, dependencies=DEP)
def agregar_idea_negocio(body: schemas.IdeaNegocioIn, db: Session = Depends(get_db)):
    row = models.IdeaNegocio(fecha=body.fecha, contenido=body.contenido.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/ideas-negocio/{item_id}", status_code=204, dependencies=DEP)
def eliminar_idea_negocio(item_id: int, db: Session = Depends(get_db)):
    db.query(models.IdeaNegocio).filter(models.IdeaNegocio.id == item_id).delete()
    db.commit()


@app.get("/compras/{fecha}", response_model=List[schemas.CompraOut], dependencies=DEP)
def listar_compras(fecha: str, db: Session = Depends(get_db)):
    return db.query(models.Compra).filter(models.Compra.fecha == fecha).order_by(models.Compra.id).all()


@app.get("/compras/{fecha}/total", dependencies=DEP)
def total_compras_fecha(fecha: str, db: Session = Depends(get_db)):
    total = sum(c.monto or 0 for c in db.query(models.Compra).filter(models.Compra.fecha == fecha).all())
    return {"total": total}


@app.post("/compras", response_model=schemas.CompraOut, dependencies=DEP)
def agregar_compra(body: schemas.CompraIn, db: Session = Depends(get_db)):
    row = models.Compra(fecha=body.fecha, descripcion=body.descripcion.strip(), monto=body.monto)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/compras/{item_id}", status_code=204, dependencies=DEP)
def eliminar_compra(item_id: int, db: Session = Depends(get_db)):
    db.query(models.Compra).filter(models.Compra.id == item_id).delete()
    db.commit()


@app.get("/cuentas", response_model=List[schemas.CuentaOut], dependencies=DEP)
def listar_cuentas(solo_activas: bool = True, db: Session = Depends(get_db)):
    q = db.query(models.Cuenta)
    if solo_activas:
        q = q.filter(models.Cuenta.activo == 1)
    return q.order_by(models.Cuenta.orden, models.Cuenta.nombre).all()


@app.post("/cuentas", response_model=schemas.CuentaOut, dependencies=DEP)
def crear_cuenta(body: schemas.CuentaIn, db: Session = Depends(get_db)):
    row = models.Cuenta(nombre=body.nombre.strip(), incluye_en_total=1 if body.incluye_en_total else 0)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/cuentas/{cuenta_id}", status_code=204, dependencies=DEP)
def eliminar_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    db.query(models.Cuenta).filter(models.Cuenta.id == cuenta_id).delete()
    db.commit()


@app.get("/movimientos/{fecha}", response_model=List[schemas.MovimientoOut], dependencies=DEP)
def listar_movimientos_fecha(fecha: str, db: Session = Depends(get_db)):
    Debe = models.Cuenta
    from sqlalchemy.orm import aliased
    Haber = aliased(models.Cuenta)
    rows = (
        db.query(models.Movimiento, Debe.nombre, Haber.nombre)
        .join(Debe, Debe.id == models.Movimiento.cuenta_debe_id)
        .join(Haber, Haber.id == models.Movimiento.cuenta_haber_id)
        .filter(models.Movimiento.fecha == fecha)
        .order_by(models.Movimiento.id)
        .all()
    )
    return [
        schemas.MovimientoOut(**m.__dict__, cuenta_debe_nombre=dn, cuenta_haber_nombre=hn)
        for m, dn, hn in rows
    ]


@app.post("/movimientos", response_model=schemas.MovimientoOut, dependencies=DEP)
def agregar_movimiento(body: schemas.MovimientoIn, db: Session = Depends(get_db)):
    row = models.Movimiento(
        fecha=body.fecha, cuenta_debe_id=body.cuenta_debe_id, cuenta_haber_id=body.cuenta_haber_id,
        monto=body.monto, concepto=(body.concepto or "").strip(), creado_en=ahora(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    cd = db.get(models.Cuenta, row.cuenta_debe_id)
    ch = db.get(models.Cuenta, row.cuenta_haber_id)
    return schemas.MovimientoOut(
        **row.__dict__,
        cuenta_debe_nombre=cd.nombre if cd else None,
        cuenta_haber_nombre=ch.nombre if ch else None,
    )


@app.delete("/movimientos/{movimiento_id}", status_code=204, dependencies=DEP)
def eliminar_movimiento(movimiento_id: int, db: Session = Depends(get_db)):
    db.query(models.Movimiento).filter(models.Movimiento.id == movimiento_id).delete()
    db.commit()


@app.get("/finanzas/balances", response_model=List[schemas.BalanceCuentaOut], dependencies=DEP)
def balances_por_cuenta(hasta_fecha: Optional[str] = None, db: Session = Depends(get_db)):
    cuentas = db.query(models.Cuenta).filter(models.Cuenta.activo == 1).order_by(
        models.Cuenta.orden, models.Cuenta.nombre
    ).all()
    q_debe = db.query(models.Movimiento)
    q_haber = db.query(models.Movimiento)
    if hasta_fecha:
        q_debe = q_debe.filter(models.Movimiento.fecha <= hasta_fecha)
        q_haber = q_haber.filter(models.Movimiento.fecha <= hasta_fecha)
    debe_map, haber_map = {}, {}
    for m in q_debe.all():
        debe_map[m.cuenta_debe_id] = debe_map.get(m.cuenta_debe_id, 0) + m.monto
        haber_map[m.cuenta_haber_id] = haber_map.get(m.cuenta_haber_id, 0) + m.monto
    return [
        {"cuenta": cu, "saldo": debe_map.get(cu.id, 0) - haber_map.get(cu.id, 0)}
        for cu in cuentas
    ]


@app.get("/finanzas/patrimonio", dependencies=DEP)
def patrimonio_total(hasta_fecha: Optional[str] = None, db: Session = Depends(get_db)):
    balances = balances_por_cuenta(hasta_fecha, db)
    total = sum(b["saldo"] for b in balances if b["cuenta"].incluye_en_total)
    return {"total": total}


# ================= 7. MATRIZ MAESTRA DE TAREAS =================

@app.get("/matriz", response_model=List[schemas.TareaMatrizOut], dependencies=DEP)
def listar_matriz(plazo: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.TareaMatriz)
    orden_prioridad = {"alta": 0, "media": 1, "baja": 2}
    if plazo:
        rows = q.filter(models.TareaMatriz.plazo == plazo).all()
    else:
        rows = q.all()
    rows.sort(key=lambda t: (t.plazo if not plazo else "", orden_prioridad.get(t.prioridad, 9), t.id))
    return rows


@app.get("/matriz/plazos", dependencies=DEP)
def plazos_existentes(db: Session = Depends(get_db)):
    rows = db.query(models.TareaMatriz.plazo).distinct().all()
    return [r[0] for r in rows]


@app.post("/matriz", response_model=schemas.TareaMatrizOut, dependencies=DEP)
def crear_tarea_matriz(body: schemas.TareaMatrizIn, db: Session = Depends(get_db)):
    row = models.TareaMatriz(
        titulo=body.titulo.strip(), plazo=body.plazo, prioridad=body.prioridad, creado_en=ahora()
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.patch("/matriz/{item_id}/completar", response_model=schemas.TareaMatrizOut, dependencies=DEP)
def completar_tarea_matriz(item_id: int, db: Session = Depends(get_db)):
    row = db.get(models.TareaMatriz, item_id)
    if not row:
        raise HTTPException(404, "No encontrada")
    row.estado = "completada"
    db.commit()
    db.refresh(row)
    return row


@app.patch("/matriz/{item_id}/reabrir", response_model=schemas.TareaMatrizOut, dependencies=DEP)
def reabrir_tarea_matriz(item_id: int, db: Session = Depends(get_db)):
    row = db.get(models.TareaMatriz, item_id)
    if not row:
        raise HTTPException(404, "No encontrada")
    row.estado = "pendiente"
    db.commit()
    db.refresh(row)
    return row


@app.delete("/matriz/{item_id}", status_code=204, dependencies=DEP)
def eliminar_tarea_matriz(item_id: int, db: Session = Depends(get_db)):
    db.query(models.TareaMatriz).filter(models.TareaMatriz.id == item_id).delete()
    db.commit()


# Sirve el frontend estático (index.html, manifest, service worker) si está presente,
# así el backend y el frontend quedan como UN solo servicio desplegado.
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
