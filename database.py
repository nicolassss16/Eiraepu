from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Configuración de la Base de Datos ---
# Usamos SQLite. Es solo un archivo (eirae.db) en tu carpeta.
# Para producción (MySQL/PostgreSQL), solo cambias esta línea:
# "mysql+pymysql://user:password@host/dbname"
# "postgresql://user:password@host/dbname"
DATABASE_URL = "sqlite:///./eirae.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread es solo para SQLite
)

# Creamos una "Sesión" para hablar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para nuestros modelos (tablas)
Base = declarative_base()

# Función para inicializar la BD
def init_db():
    # Importa los modelos y crea las tablas si no existen
    from . import models # noqa
    Base.metadata.create_all(bind=engine)