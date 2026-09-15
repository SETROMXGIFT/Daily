from typing import Optional
from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Diario ----------
class DiarioIn(ORMBase):
    contenido: str


class DiarioOut(ORMBase):
    fecha: str
    contenido: str
    actualizado_en: Optional[str] = None


# ---------- Hábitos ----------
class HabitoIn(ORMBase):
    nombre: str


class HabitoOut(ORMBase):
    id: int
    nombre: str
    activo: int
    orden: int


class HabitoRegistroIn(ORMBase):
    habito_id: int
    fecha: str
    tiempo: Optional[str] = None
    calificacion: Optional[int] = None
    nota: Optional[str] = None


class HabitoRegistroOut(ORMBase):
    id: int
    habito_id: int
    fecha: str
    tiempo: Optional[str] = None
    calificacion: Optional[int] = None
    nota: Optional[str] = None
    habito_nombre: Optional[str] = None


# ---------- Conocimiento ----------
class ConocimientoIn(ORMBase):
    fecha: str
    descripcion: str


class ConocimientoOut(ConocimientoIn):
    id: int


class ProyectoIntelectualIn(ORMBase):
    fecha: str
    nombre: str


class ProyectoIntelectualOut(ProyectoIntelectualIn):
    id: int
    estado: str


class ProyectoEstadoIn(ORMBase):
    estado: str


class TemaIn(ORMBase):
    nombre: str


class TemaOut(ORMBase):
    id: int
    nombre: str
    activo: int
    orden: int


class TemaRegistroIn(ORMBase):
    tema_id: int
    fecha: str
    tiempo: Optional[str] = None
    calificacion: Optional[int] = None
    nota: Optional[str] = None


class TemaRegistroOut(ORMBase):
    id: int
    tema_id: int
    fecha: str
    tiempo: Optional[str] = None
    calificacion: Optional[int] = None
    nota: Optional[str] = None
    tema_nombre: Optional[str] = None


# ---------- Ejercicio y sueño ----------
class EjercicioIn(ORMBase):
    fecha: str
    nombre: str
    repeticiones: Optional[str] = None
    tiempo: Optional[str] = None
    calificacion: Optional[int] = None


class EjercicioOut(EjercicioIn):
    id: int


class SuenoIn(ORMBase):
    horas: Optional[float] = None
    calidad: Optional[int] = None
    nota: Optional[str] = None


class SuenoOut(SuenoIn):
    fecha: str


# ---------- Alimentación ----------
class AlimentacionIn(ORMBase):
    fecha: str
    tipo: str
    descripcion: str


class AlimentacionOut(AlimentacionIn):
    id: int


# ---------- Finanzas ----------
class IdeaNegocioIn(ORMBase):
    fecha: str
    contenido: str


class IdeaNegocioOut(IdeaNegocioIn):
    id: int


class CompraIn(ORMBase):
    fecha: str
    descripcion: str
    monto: float = 0


class CompraOut(CompraIn):
    id: int


class CuentaIn(ORMBase):
    nombre: str
    incluye_en_total: bool = True


class CuentaOut(ORMBase):
    id: int
    nombre: str
    incluye_en_total: int
    activo: int
    orden: int


class MovimientoIn(ORMBase):
    fecha: str
    cuenta_debe_id: int
    cuenta_haber_id: int
    monto: float
    concepto: Optional[str] = ""


class MovimientoOut(ORMBase):
    id: int
    fecha: str
    cuenta_debe_id: int
    cuenta_haber_id: int
    monto: float
    concepto: Optional[str] = None
    creado_en: Optional[str] = None
    cuenta_debe_nombre: Optional[str] = None
    cuenta_haber_nombre: Optional[str] = None


class BalanceCuentaOut(ORMBase):
    cuenta: CuentaOut
    saldo: float


# ---------- Matriz de tareas ----------
class TareaMatrizIn(ORMBase):
    titulo: str
    plazo: str
    prioridad: str


class TareaMatrizOut(ORMBase):
    id: int
    titulo: str
    plazo: str
    prioridad: str
    estado: str
    creado_en: Optional[str] = None
