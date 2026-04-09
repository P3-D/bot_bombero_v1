import logging
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ConversationHandler
)

# 🔌 IMPORTAMOS NUESTRO TABLERO CENTRAL Y LOS CIMIENTOS
from src.config import Config
from src.core.database import inicializar_db

# 👨‍💼 IMPORTAMOS AL "RECEPCIONISTA" (Comandos básicos)
from interfaces.telegram.handlers import (
    comando_start, comando_sugerencia, comando_ayuda, mensaje_desconocido
)

# 👮‍♂️ IMPORTAMOS AL "OFICIAL DE GUARDIA" (El flujo del parte y sus estados)
from interfaces.telegram.dialogues import (
    iniciar_parte, recibir_unidad, recibir_clave, recibir_km_salida, 
    recibir_ubicacion, recibir_km_llegada, recibir_personal, 
    recibir_apoyo, recibir_afectados, recibir_detalles, 
    guardar_final, cancel,
    UNIDAD, CLAVE, KM_SALIDA, UBICACION, KM_LLEGADA, 
    PERSONAL, APOYO, AFECTADOS, DETALLES, CONFIRMACION
)

# Configuramos el registro visual en la consola (SOLO AQUÍ)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Función principal que levanta la obra completa."""
    
    # 1. Asegurar cimientos: Si la DB no existe, la crea.
    inicializar_db()

    # 2. Levantar la aplicación con el token de la Caja Fuerte (.env)
    if not Config.TELEGRAM_TOKEN:
        logger.error("❌ NO HAY TOKEN DE TELEGRAM. Revisa tu archivo .env")
        return
        
    application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()

    # =======================================================
    # ⚠️ ORDEN ESTRICTO DE HANDLERS (De mayor a menor prioridad)
    # =======================================================

    # 3. PRIMERO: Registrar al Oficial de Guardia (La conversación)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('parte', iniciar_parte)],
        states={
            UNIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_unidad)],
            CLAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_clave)],
            KM_SALIDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_km_salida)],
            UBICACION: [MessageHandler(filters.LOCATION | (filters.TEXT & ~filters.COMMAND), recibir_ubicacion)],
            KM_LLEGADA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_km_llegada)],
            PERSONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_personal)],
            APOYO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_apoyo)],
            AFECTADOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_afectados)],
            DETALLES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_detalles)],
            CONFIRMACION: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_final)],
        },
        fallbacks=[CommandHandler('cancelar', cancel)],
    )
    application.add_handler(conv_handler)

    # 4. SEGUNDO: Registrar al Recepcionista (Comandos directos y sueltos)
    application.add_handler(CommandHandler("start", comando_start)) # <-- Restaurado
    application.add_handler(CommandHandler("ayuda", comando_ayuda))
    application.add_handler(CommandHandler("sugerencia", comando_sugerencia))

    # 5. TERCERO Y AL FINAL: El Atajador (Mensajes sueltos fuera de conversación)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_desconocido))

    # 6. Encender las luces y abrir puertas
    print("===================================================")
    print("🚒 SISTEMA DE EMERGENCIAS INICIADO Y EN LÍNEA 🚒")
    print("===================================================")
    
    application.run_polling()

if __name__ == '__main__':
    main()