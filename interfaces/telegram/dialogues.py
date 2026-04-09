import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from src.core.database import guardar_emergencia_local
from src.services.sheets_sync import subir_a_nube

# 🌍 Traductor de coordenadas a calles
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="bot_bomberos_chile")

# ==========================================
# 📖 TEXTOS Y TECLADOS
# ==========================================
TEXTO_START = "<b>Bienvenido al Bot de Gestión de Emergencias.</b>\nUsa /parte para empezar."

TEXTO_AYUDA = """<b>Comandos disponibles:</b>
🔹 /parte - Iniciar el registro de una emergencia
🔹 /cancelar - Detiene un parte en curso
🔹 /sugerencia [texto] - Enviar una idea de mejora"""

teclado_unidades = ReplyKeyboardMarkup([['R-2', 'BF-2'], ['B-2']], resize_keyboard=True, one_time_keyboard=True)
teclado_claves = ReplyKeyboardMarkup([['10-0', '10-2', '10-3'], ['10-4', '10-10', '10-12']], resize_keyboard=True, one_time_keyboard=True)
teclado_ninguno = ReplyKeyboardMarkup([['Ninguno']], resize_keyboard=True, one_time_keyboard=True)
teclado_detalles = ReplyKeyboardMarkup([['Sin detalles']], resize_keyboard=True, one_time_keyboard=True)
teclado_sn = ReplyKeyboardMarkup([['SI', 'NO']], resize_keyboard=True, one_time_keyboard=True)
teclado_ubicacion = ReplyKeyboardMarkup([[KeyboardButton("📍 Enviar mi ubicación actual", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)

# ==========================================
# 🚦 ESTADOS DE LA CONVERSACIÓN
# ==========================================
UNIDAD, CLAVE, KM_SALIDA, UBICACION, KM_LLEGADA, PERSONAL, APOYO, AFECTADOS, DETALLES, CONFIRMACION = range(10)

# ==========================================
# 👮‍♂️ FLUJO DEL PARTE DE EMERGENCIA (CON VALIDACIONES)
# ==========================================
async def iniciar_parte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🚒 Iniciando Parte. Selecciona la UNIDAD:", reply_markup=teclado_unidades)
    return UNIDAD

async def recibir_unidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['unidad'] = update.message.text.upper()
    await update.message.reply_text("¿Cuál es la CLAVE?", reply_markup=teclado_claves)
    return CLAVE

async def recibir_clave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['clave'] = update.message.text.upper()
    await update.message.reply_text("Indica KM DE SALIDA (solo números puros):", reply_markup=ReplyKeyboardRemove())
    return KM_SALIDA

async def recibir_km_salida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    
    # 🚨 VALIDACIÓN 1: Solo números
    if not texto.isdigit():
        await update.message.reply_text("❌ Error: El kilometraje debe contener SOLO NÚMEROS (ej: 15400).\nPor favor, ingresa el KM DE SALIDA nuevamente:")
        return KM_SALIDA # Vuelve a pedirlo, no avanza
        
    context.user_data['km_salida'] = texto
    await update.message.reply_text("📍 Envía la UBICACIÓN:", reply_markup=teclado_ubicacion)
    return UBICACION

async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data['coordenadas'] = f"{lat}, {lon}"
        try:
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            direccion_corta = ", ".join(location.address.split(",")[:3]) 
            context.user_data['ubicacion'] = direccion_corta
            await update.message.reply_text(f"🏠 Dirección detectada: {direccion_corta}")
        except:
            context.user_data['ubicacion'] = f"Coordenadas: {lat}, {lon}"
            await update.message.reply_text("📍 Ubicación guardada por coordenadas.")
    else:
        context.user_data['ubicacion'] = update.message.text

    await update.message.reply_text("Indica el KM DE LLEGADA al cuartel (solo números):", reply_markup=ReplyKeyboardRemove())
    return KM_LLEGADA

async def recibir_km_llegada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    
    # 🚨 VALIDACIÓN 2: Solo números
    if not texto.isdigit():
        await update.message.reply_text("❌ Error: Debes usar SOLO NÚMEROS.\nIndica el KM DE LLEGADA nuevamente:")
        return KM_LLEGADA
        
    # 🚨 VALIDACIÓN 3: Lógica matemática
    if int(texto) < int(context.user_data['km_salida']):
        await update.message.reply_text(f"❌ Error Físico: El KM de llegada ({texto}) no puede ser menor al de salida ({context.user_data['km_salida']}).\nIndica el KM DE LLEGADA real:")
        return KM_LLEGADA

    context.user_data['km_llegada'] = texto
    await update.message.reply_text("¿Quiénes componen el PERSONAL a cargo y asistentes? (Nombres o IDs):")
    return PERSONAL

async def recibir_personal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['personal'] = update.message.text
    await update.message.reply_text("¿Asistieron unidades de APOYO? (Indica cuáles o presiona Ninguno):", reply_markup=teclado_ninguno)
    return APOYO

async def recibir_apoyo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['apoyo'] = update.message.text
    await update.message.reply_text("¿Hubo AFECTADOS o lesionados? (Detalla o presiona Ninguno):", reply_markup=teclado_ninguno)
    return AFECTADOS

async def recibir_afectados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['afectados'] = update.message.text
    await update.message.reply_text("Añade DETALLES de la emergencia. (Debes detallar lo sucedido o presionar el botón 'Sin detalles'):", reply_markup=teclado_detalles)
    return DETALLES

async def recibir_detalles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    
    # 🚨 VALIDACIÓN 4: Filtro de flojera (Mínimo 15 caracteres o botón exacto)
    if len(texto) < 15 and texto.lower() != "sin detalles":
        await update.message.reply_text("❌ Reporte muy breve. El parte oficial requiere un mínimo de detalle.\nPor favor, describe mejor lo sucedido o presiona 'Sin detalles':")
        return DETALLES

    context.user_data['detalles'] = texto
    
    d = context.user_data
    resumen = (
        "📋 *RESUMEN DEL PARTE*\n"
        f"Unidad: {d['unidad']} | Clave: {d['clave']}\n"
        f"Lugar: {d['ubicacion']}\n"
        f"KM: {d['km_salida']} -> {d['km_llegada']} (Recorridos: {int(d['km_llegada']) - int(d['km_salida'])})\n"
        f"Personal: {d['personal']}\n\n"
        "¿Está todo correcto?"
    )
    await update.message.reply_markdown(resumen, reply_markup=teclado_sn)
    return CONFIRMACION

async def guardar_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    respuesta = update.message.text.upper()
    if respuesta == "SI":
        d = context.user_data
        responsable = update.effective_user.first_name
        
        datos_db = {
            'fecha': datetime.datetime.now().strftime("%Y-%m-%d"),
            'hora': datetime.datetime.now().strftime("%H:%M"),
            'unidad': d['unidad'], 'clave': d['clave'], 'km_salida': d['km_salida'],
            'ubicacion': d['ubicacion'], 'km_llegada': d['km_llegada'],
            'personal': d['personal'], 'apoyos': d['apoyo'], 'afectados': d['afectados'],
            'detalles': d['detalles'], 'responsable': responsable
        }
        
        exito, folio = guardar_emergencia_local(datos_db)
        
        if exito:
            await update.message.reply_text(f"✅ Parte guardado localmente (Folio: {folio}). Sincronizando...", reply_markup=ReplyKeyboardRemove())
            
            try:
                km_rec = int(d['km_llegada']) - int(d['km_salida'])
            except:
                km_rec = 0
                
            fila_sheets = [
                folio, datos_db['fecha'], datos_db['hora'], d['unidad'], d['clave'], 
                d['km_salida'], d['ubicacion'], d['km_llegada'], km_rec, 
                d['personal'], d['apoyo'], d['afectados'], d['detalles'], responsable
            ]
            
            if subir_a_nube(fila_sheets):
                await update.message.reply_text("☁️ Nube sincronizada exitosamente. ¡Buen trabajo!")
            else:
                await update.message.reply_text("⚠️ Guardado en disco, pero falló la sincronización a la Nube.")
        else:
            await update.message.reply_text("❌ Error crítico al guardar en base de datos local.")
    else:
        await update.message.reply_text("❌ Parte cancelado. Inicia uno nuevo con /parte.", reply_markup=ReplyKeyboardRemove())
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Parte abortado manualmente.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END