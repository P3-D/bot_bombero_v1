import gspread
from google.oauth2.service_account import Credentials
import logging
from src.config import Config

logger = logging.getLogger("SheetsSync")

# ==========================================
# 🛠️ PATRÓN SINGLETON: La "Conexión Maestra"
# ==========================================
# Estas variables guardan la conexión abierta para no re-autenticar cada vez
_conexion_abierta = False
_hoja_partes = None
_hoja_usuarios = None

def conectar_sheets():
    """Abre la puerta de Google UNA SOLA VEZ y la mantiene abierta."""
    global _conexion_abierta, _hoja_partes, _hoja_usuarios
    
    # Si ya estamos conectados, no hacemos nada y devolvemos las hojas
    if _conexion_abierta:
        return _hoja_partes, _hoja_usuarios

    logger.debug("🔌 Intentando conectar a Google Sheets por primera vez...")
    
    # Verificamos que el ID exista en Config
    if not Config.GOOGLE_SHEET_ID:
        logger.error("❌ ERROR: El GOOGLE_SHEET_ID está vacío en el .env")
        return None, None
        
    try:
        # Librería MODERNA (google.oauth2)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(
            Config.GOOGLE_SHEETS_CREDENTIALS, 
            scopes=scopes
        )
        gc = gspread.authorize(creds)
        
        # Abrimos el archivo
        archivo = gc.open_by_key(Config.GOOGLE_SHEET_ID)
        
        # Guardamos las hojas en la memoria global (Caché)
        _hoja_partes = archivo.sheet1
        _hoja_usuarios = archivo.worksheet("Usuarios")
        _conexion_abierta = True
        
        logger.info("✅ Conexión a Google Sheets establecida y en caché.")
        return _hoja_partes, _hoja_usuarios
        
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO DE CONEXIÓN A SHEETS: {e}")
        return None, None

# ==========================================
# 📊 FUNCIONES DE OPERACIÓN
# ==========================================

def obtener_mapa_usuarios():
    """Lee los usuarios usando la conexión en caché."""
    logger.debug("🔍 Leyendo pestaña de Usuarios...")
    try:
        _, user_sheet = conectar_sheets()
        if user_sheet:
            registros = user_sheet.get_all_records()
            mapa = {str(r['ID']): r['Nombre'] for r in registros}
            logger.debug(f"🗺️ Mapa traducido para el bot: {mapa}")
            return mapa
        return {}
    except KeyError:
        logger.error("❌ ERROR DE COLUMNA: Asegúrate de que en Sheets se llamen 'ID' y 'Nombre'.")
        return {}
    except Exception as e:
        logger.error(f"❌ ERROR DESCONOCIDO AL LEER USUARIOS: {e}")
        return {}

def subir_a_nube(fila_datos):
    """Sube el parte a Google Sheets de forma silenciosa."""
    try:
        sheet, _ = conectar_sheets()
        if sheet:
            sheet.append_row(fila_datos)
            logger.info("☁️ Parte sincronizado con la nube exitosamente.")
            return True
        return False
    except Exception as e:
        logger.error(f"Fallo al sincronizar con la nube: {e}")
        return False