from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from . import models, logic, database
from datetime import datetime, timedelta

router = APIRouter()

# --- Dependencia para obtener la Sesión de la BD ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Modelos de Pydantic (para validar datos de entrada/salida) ---
class ZonaRiesgo(BaseModel):
    id: int
    nombre: str
    lat: float
    lon: float
    riesgo_epidemiologico: str
    calidad_aire: str
    clima_actual: dict | None = None
    ultima_lectura: dict | None = None
    
    class Config:
        from_attributes = True

class LecturaSensorIn(BaseModel):
    sensor_nombre: str
    temperatura: float
    humedad: float
    particulas_pm25: float

class ReporteComunitarioIn(BaseModel):
    lat: float
    lon: float
    tipo_sintoma: str
    comentario: str | None = None

class LecturaHistorial(BaseModel):
    timestamp: datetime
    temperatura: float
    humedad: float
    particulas_pm25: float
    
    class Config:
        from_attributes = True

class ReportePublico(BaseModel):
    id: int
    lat: float
    lon: float
    tipo_sintoma: str
    comentario: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True

# --- ¡NUEVO! Modelos para crear sensores ---
class SensorCreate(BaseModel):
    nombre: str
    lat: float
    lon: float

class SensorPublic(BaseModel):
    id: int
    nombre: str
    lat: float
    lon: float
    
    class Config:
        from_attributes = True


# --- Endpoint del Dashboard (el que ve el mapa) ---
@router.get("/api/map_data", response_model=List[ZonaRiesgo])
async def get_map_data(db: Session = Depends(get_db)):
    zonas_con_riesgo = []
    sensores = db.query(models.Sensor).all()
    
    for sensor in sensores:
        clima_actual = await logic.get_clima_actual(sensor.lat, sensor.lon)
        riesgo_calculado = logic.calcular_riesgo_zona(db, sensor)
        
        zona_data = {
            "id": sensor.id,
            "nombre": sensor.nombre,
            "lat": sensor.lat,
            "lon": sensor.lon,
            "riesgo_epidemiologico": riesgo_calculado["riesgo_epidemiologico"],
            "calidad_aire": riesgo_calculado["calidad_aire"],
            "clima_actual": clima_actual,
            "ultima_lectura": riesgo_calculado.get("ultima_lectura")
        }
        zonas_con_riesgo.append(zona_data)
        
    return zonas_con_riesgo

# --- ENDPOINTS DE INGESTA ---
@router.post("/api/ingest/sensor", status_code=201)
async def ingest_sensor_data(lectura: LecturaSensorIn, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.nombre == lectura.sensor_nombre).first()
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{lectura.sensor_nombre}' no encontrado.")
    
    nueva_lectura = models.LecturaSensor(
        sensor_id = sensor.id,
        temperatura = lectura.temperatura,
        humedad = lectura.humedad,
        particulas_pm25 = lectura.particulas_pm25
    )
    db.add(nueva_lectura)
    db.commit()
    db.refresh(nueva_lectura)
    return {"status": "ok", "lectura_id": nueva_lectura.id}

@router.post("/api/ingest/report", status_code=201)
async def ingest_community_report(reporte: ReporteComunitarioIn, db: Session = Depends(get_db)):
    nuevo_reporte = models.ReporteComunitario(
        lat = reporte.lat,
        lon = reporte.lon,
        tipo_sintoma = reporte.tipo_sintoma,
        comentario = reporte.comentario
    )
    db.add(nuevo_reporte)
    db.commit()
    return {"status": "ok", "reporte_id": nuevo_reporte.id}


# --- ENDPOINTS DE HISTORIAL Y REPORTES ---
@router.get("/api/sensor/{sensor_id}/history", response_model=List[LecturaHistorial])
async def get_sensor_history(sensor_id: int, db: Session = Depends(get_db)):
    hace_24_horas = datetime.utcnow() - timedelta(hours=24)
    historial = db.query(models.LecturaSensor)\
        .filter(models.LecturaSensor.sensor_id == sensor_id)\
        .filter(models.LecturaSensor.timestamp >= hace_24_horas)\
        .order_by(models.LecturaSensor.timestamp.asc())\
        .all()
    return historial

@router.get("/api/reports", response_model=List[ReportePublico])
async def get_community_reports(db: Session = Depends(get_db)):
    reportes = db.query(models.ReporteComunitario)\
        .order_by(models.ReporteComunitario.timestamp.desc())\
        .limit(50)\
        .all()
    return reportes

# --- ENDPOINT DEL FORMULARIO DE DEMO ---
@router.post("/api/solicitar_demo")
async def recibir_solicitud_demo(
    nombre: str = Form(...),
    email: str = Form(...),
    organizacion: Optional[str] = Form(None)
):
    print("\n--- ¡NUEVA SOLICITUD DE DEMO RECIBIDA! ---")
    print(f"Nombre: {nombre}")
    print(f"Email: {email}")
    print(f"Organización: {organizacion}")
    print("-------------------------------------------\n")
    return RedirectResponse(url="/", status_code=303)


# --- ¡NUEVO! Endpoint para crear sensores ---
@router.post("/api/sensor/create", response_model=SensorPublic, status_code=201)
async def create_new_sensor(sensor_data: SensorCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo sensor (zona) en la base de datos.
    """
    # 1. Verificar si ya existe
    db_sensor = db.query(models.Sensor).filter(models.Sensor.nombre == sensor_data.nombre).first()
    if db_sensor:
        raise HTTPException(status_code=400, detail=f"El sensor con nombre '{sensor_data.nombre}' ya existe.")
    
    # 2. Crear el nuevo objeto
    nuevo_sensor = models.Sensor(
        nombre=sensor_data.nombre,
        lat=sensor_data.lat,
        lon=sensor_data.lon
    )
    
    # 3. Guardar en BD
    db.add(nuevo_sensor)
    db.commit()
    db.refresh(nuevo_sensor)
    
    print(f"\n--- ¡NUEVO SENSOR AGREGADO! ---")
    print(f"Nombre: {nuevo_sensor.nombre}")
    print("--------------------------------\n")
    
    return nuevo_sensor