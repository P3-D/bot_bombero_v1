import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Definimos la variable privada afuera para poder cargar el .env
_BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Cargamos el .env
load_dotenv(_BASE_DIR / ".env")

class Config:
    # 🔌 La publicamos dentro del Tablero para que todos la encuentren
    BASE_DIR = _BASE_DIR
    
    # Tokens y llaves (Cargados del .env)
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    
    # Rutas de Archivos (Instalaciones)
    DB_PATH = BASE_DIR / "data" / "emergencias.db"
    LOG_FILE = BASE_DIR / "logs" / "system.log"
    ASSETS_DIR = BASE_DIR / "assets"
    
    # Credenciales de Google Sheets centralizadas
    GOOGLE_SHEETS_CREDENTIALS = ASSETS_DIR / "credenciales.json"
    
    # Salidas y Temporales
    REPORTS_DIR = BASE_DIR / "outputs" / "reportes_pdf"
    TEMP_DIR = BASE_DIR / "temp" # Usada para procesar antes de exportar

    # Auto-construcción y Validación Crítica
    @classmethod
    def self_check(cls):
        # 1. Cortacorriente: Validar que existan las variables de entorno
        faltantes = []
        if not cls.TELEGRAM_TOKEN:
            faltantes.append("TELEGRAM_TOKEN")
        if not cls.GOOGLE_SHEET_ID:
            faltantes.append("GOOGLE_SHEET_ID")
            
        if faltantes:
            raise ValueError(f"🚨 ERROR DE ARRANQUE: Faltan variables en el archivo .env: {', '.join(faltantes)}")

        # 2. Cortacorriente: Validar archivo de credenciales
        if not cls.GOOGLE_SHEETS_CREDENTIALS.exists():
            # Solo lanza advertencia si quieres que el bot corra sin Google Sheets por un rato, 
            # pero es mejor que falle rápido para obligarnos a poner el archivo.
            raise FileNotFoundError(f"🚨 ERROR DE ARRANQUE: Falta el archivo de credenciales en {cls.GOOGLE_SHEETS_CREDENTIALS}")

        # 3. Auto-construcción de carpetas estructurales
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Ejecuta el chequeo apenas arranca el programa
Config.self_check()