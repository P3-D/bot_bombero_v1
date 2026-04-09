from telegram import Update
from telegram.ext import ContextTypes
from src.core.database import guardar_sugerencia

# AHORA IMPORTAMOS LOS TEXTOS CON SU NUEVO NOMBRE
from interfaces.telegram.dialogues import TEXTO_START, TEXTO_AYUDA

async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start"""
    user = update.effective_user
    await update.message.reply_html(rf"Hola {user.mention_html()}! " + TEXTO_START)

async def comando_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el manual de usuario."""
    await update.message.reply_html(TEXTO_AYUDA)


async def comando_sugerencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las sugerencias y AHORA SÍ las guarda en la base de datos"""
    texto = " ".join(context.args)
    if not texto:
        await update.message.reply_text("⚠️ Por favor, escribe tu sugerencia después del comando. Ejemplo: /sugerencia arreglar GPS.")
        return
    
    # Extraemos los datos del bombero
    user_id = update.effective_user.id
    nombre = update.effective_user.first_name
    
    # LA MAGIA V2.0: Guardamos en SQLite
    guardar_sugerencia(user_id, nombre, texto)
    
    await update.message.reply_text("✅ Gracias por tu sugerencia. Ha sido registrada en la base de datos para revisión.")

async def mensaje_desconocido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reemplaza a tu antiguo 'manejar_mensaje' para atrapar textos perdidos"""
    await update.message.reply_text(
        "🤔 No estoy seguro de qué hacer con esto.\n"
        "Si quieres ingresar un parte de emergencia, usa el comando /parte. Si necesitas orientación, usa /ayuda."
    )