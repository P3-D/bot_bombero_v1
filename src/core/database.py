import sqlite3
import logging
from datetime import datetime
from src.config import Config

# No usamos basicConfig aquí para no "pisar" la configuración de main_bot.py
logger = logging.getLogger("Database")

def obtener_conexion():
    """Abre la conexión segura usando la ruta centralizada en Config."""
    conn = sqlite3.connect(Config.DB_PATH)
    # Esto permite acceder a las columnas por nombre (ej: fila['unidad'])
    conn.row_factory = sqlite3.Row 
    return conn

def inicializar_db():
    """Crea las fundaciones del sistema."""
    try:
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # 1. Tabla de Partes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS partes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    hora TEXT,
                    unidad TEXT,
                    clave TEXT,
                    km_salida INTEGER,
                    ubicacion TEXT,
                    km_llegada INTEGER,
                    km_recorridos INTEGER,
                    personal TEXT,
                    apoyos TEXT,
                    afectados TEXT,
                    detalles TEXT,
                    responsable TEXT
                )
            ''')

            # 2. Tabla de Usuarios (Para control de acceso futuro)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    telegram_id INTEGER PRIMARY KEY,
                    nombre TEXT,
                    rango TEXT DEFAULT 'voluntario',
                    estado TEXT DEFAULT 'activo'
                )
            ''')

            # 3. Tabla de Sugerencias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sugerencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    telegram_id INTEGER,
                    nombre TEXT,
                    mensaje TEXT
                )
            ''')
            conn.commit()
        logger.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logger.error(f"Error crítico al inicializar DB: {e}")

# --- SECCIÓN DE ESCRITURA (EL BOT ESCRIBE) ---

def guardar_emergencia_local(datos):
    """
    Guarda el parte calculando automáticamente los KM recorridos.
    'datos' debe ser un diccionario para evitar errores de orden de columnas.
    """
    try:
        # Cálculo automático de KM: Evita que el bombero tenga que restar en el momento
        km_recorridos = int(datos['km_llegada']) - int(datos['km_salida'])
        
        columnas = (
            datos['fecha'], datos['hora'], datos['unidad'], datos['clave'],
            datos['km_salida'], datos['ubicacion'], datos['km_llegada'],
            km_recorridos, datos['personal'], datos['apoyos'],
            datos['afectados'], datos['detalles'], datos['responsable']
        )

        with obtener_conexion() as conn:
            cursor = conn.cursor()
            query = '''
                INSERT INTO partes 
                (fecha, hora, unidad, clave, km_salida, ubicacion, km_llegada, 
                 km_recorridos, personal, apoyos, afectados, detalles, responsable) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, columnas)
            conn.commit()
            return True, cursor.lastrowid
    except Exception as e:
        logger.error(f"Error al guardar parte: {e}")
        return False, str(e)

# --- SECCIÓN DE LECTURA (EL DASHBOARD LEE) ---

def obtener_todos_los_partes():
    """Retorna todos los registros para el Dashboard."""
    try:
        with obtener_conexion() as conn:
            # Usamos pandas si está disponible o convertimos a lista de dicts
            cursor = conn.execute("SELECT * FROM partes ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error al leer partes: {e}")
        return []

def obtener_estadisticas_claves():
    """Agrupa emergencias por clave para los gráficos."""
    try:
        with obtener_conexion() as conn:
            cursor = conn.execute("SELECT clave, COUNT(*) as total FROM partes GROUP BY clave")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error en estadísticas: {e}")
        return []
    
def guardar_sugerencia(telegram_id, nombre, mensaje):
    """Guarda el feedback en la tabla de sugerencias."""
    try:
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO sugerencias (fecha, telegram_id, nombre, mensaje) VALUES (?, ?, ?, ?)',
                           (fecha_actual, telegram_id, nombre, mensaje))
            conn.commit()
        logger.info(f"Sugerencia de {nombre} guardada exitosamente.")
    except Exception as e:
        logger.error(f"Error al guardar sugerencia: {e}")