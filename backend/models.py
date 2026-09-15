from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from db import Base


class Diario(Base):
    __tablename__ = "diario"
    fecha = Column(String, primary_key=True)
    contenido = Column(Text, nullable=False)
    actualizado_en = Column(String)


class Habito(Base):
    __tablename__ = "habitos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False, unique=True)
    activo = Column(Integer, default=1)
    orden = Column(Integer, default=0)


class HabitoRegistro(Base):
    __tablename__ = "habito_registro"
    id = Column(Integer, primary_key=True, autoincrement=True)
    habito_id = Column(Integer, ForeignKey("habitos.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(String, nullable=False)
    tiempo = Column(String)
    calificacion = Column(Integer)
    nota = Column(Text)


class Conocimiento(Base):
    __tablename__ = "conocimientos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)


class ProyectoIntelectual(Base):
    __tablename__ = "proyectos_intelectuales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    estado = Column(String, default="activo")


class Tema(Base):
    __tablename__ = "temas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False, unique=True)
    activo = Column(Integer, default=1)
    orden = Column(Integer, default=0)


class TemaRegistro(Base):
    __tablename__ = "tema_registro"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tema_id = Column(Integer, ForeignKey("temas.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(String, nullable=False)
    tiempo = Column(String)
    calificacion = Column(Integer)
    nota = Column(Text)


class Ejercicio(Base):
    __tablename__ = "ejercicios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    repeticiones = Column(String)
    tiempo = Column(String)
    calificacion = Column(Integer)


class Sueno(Base):
    __tablename__ = "sueno"
    fecha = Column(String, primary_key=True)
    horas = Column(Float)
    calidad = Column(Integer)
    nota = Column(Text)


class Alimentacion(Base):
    __tablename__ = "alimentacion"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)


class IdeaNegocio(Base):
    __tablename__ = "ideas_negocio"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String, nullable=False)
    contenido = Column(Text, nullable=False)


class Compra(Base):
    __tablename__ = "compras"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    monto = Column(Float)


class Cuenta(Base):
    __tablename__ = "cuentas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False, unique=True)
    incluye_en_total = Column(Integer, default=1)
    activo = Column(Integer, default=1)
    orden = Column(Integer, default=0)


class Movimiento(Base):
    __tablename__ = "movimientos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String, nullable=False)
    cuenta_debe_id = Column(Integer, ForeignKey("cuentas.id", ondelete="CASCADE"), nullable=False)
    cuenta_haber_id = Column(Integer, ForeignKey("cuentas.id", ondelete="CASCADE"), nullable=False)
    monto = Column(Float, nullable=False)
    concepto = Column(Text)
    creado_en = Column(String)


class TareaMatriz(Base):
    __tablename__ = "matriz_tareas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(Text, nullable=False)
    plazo = Column(String, nullable=False)
    prioridad = Column(String, nullable=False)
    estado = Column(String, default="pendiente")
    creado_en = Column(String)
