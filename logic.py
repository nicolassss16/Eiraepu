import httpx # Para llamar a la API de clima
from sqlalchemy.orm import Session
from . import models, database
from datetime import datetime, timedelta

# --- 1. Conector de API de Clima (Open-Meteo) ---

async def get_clima_actual(lat: float, lon: float) -> dict:
    """
    Obtiene el clima actual de una API externa.
    """
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status() # Lanza error si la API falla
            data = response.json()
            return data.get("current", {})
        except Exception as e:
            print(f"Error al contactar API de clima: {e}")
            return {"temperature_2m": None, "wind_speed_10m": None}

# --- 2. El "Motor de Predicción" (Simulando tu ML) ---

def calcular_riesgo_zona(db: Session, sensor: models.Sensor) -> dict:
    """
    Combina datos de la BD y el clima para generar un riesgo.
    ¡AQUÍ ES DONDE VA TU MODELO DE MACHINE LEARNING!
    """
    
    # 2.1. Obtenemos la última lectura del sensor de la BD
    ultima_lectura = db.query(models.LecturaSensor)\
        .filter(models.LecturaSensor.sensor_id == sensor.id)\
        .order_by(models.LecturaSensor.timestamp.desc())\
        .first()

    if not ultima_lectura:
        # Si no hay datos, no podemos predecir
        return {
            "nombre": sensor.nombre,
            "riesgo_epidemiologico": "INDETERMINADO",
            "calidad_aire": "INDETERMINADA"
        }

    # 2.2. ¡Simulamos la lógica de tu modelo!
    # (Reemplaza esto con la llamada a tu modelo .pkl)
    
    # Lógica de Calidad de Aire (basada en PM2.5)
    calidad_aire = "BUENA"
    if ultima_lectura.particulas_pm25 > 35:
        calidad_aire = "MALA"
    elif ultima_lectura.particulas_pm25 > 12:
        calidad_aire = "MODERADA"

    # Lógica de Riesgo Epidemiológico (ej. Dengue/Respiratorio)
    # Si hace calor (>25°C) y la humedad es alta (>70%), riesgo de dengue.
    riesgo_epi = "BAJO"
    if ultima_lectura.temperatura > 25 and ultima_lectura.humedad > 70:
        riesgo_epi = "ALTO"
    # Si hace frío (<10°C) y el aire es malo, riesgo respiratorio.
    elif ultima_lectura.temperatura < 10 and calidad_aire == "MALA":
        riesgo_epi = "ALTO"
    elif ultima_lectura.temperatura > 20 and calidad_aire == "MODERADA":
        riesgo_epi = "MEDIO"
        
    return {
        "nombre": sensor.nombre,
        "riesgo_epidemiologico": riesgo_epi,
        "calidad_aire": calidad_aire,
        "ultima_lectura": {
            "temp": ultima_lectura.temperatura,
            "hum": ultima_lectura.humedad,
            "pm25": ultima_lectura.particulas_pm25,
            "hora": ultima_lectura.timestamp.isoformat()
        }
    }