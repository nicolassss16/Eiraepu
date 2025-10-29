from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base

# --- Definición de las Tablas ---

class Sensor(Base):
    __tablename__ = "sensores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    lat = Column(Float)
    lon = Column(Float)
    
    # Relación: Un sensor tiene muchas lecturas
    lecturas = relationship("LecturaSensor", back_populates="sensor")

class LecturaSensor(Base):
    __tablename__ = "lecturas_sensor"
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensores.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    temperatura = Column(Float)
    humedad = Column(Float)
    particulas_pm25 = Column(Float) # Partículas PM2.5

    # Relación: Cada lectura pertenece a un sensor
    sensor = relationship("Sensor", back_populates="lecturas")

class ReporteComunitario(Base):
    __tablename__ = "reportes_comunitarios"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    lat = Column(Float)
    lon = Column(Float)
    tipo_sintoma = Column(String) # Ej: "respiratorio", "dengue"
    comentario = Column(String, nullable=True)