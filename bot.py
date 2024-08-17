import os
import sys
import telegram
from resources.commands import handle_files, notfollowers
from dotenv import load_dotenv
from pathlib import Path
from telegram.ext import CommandHandler, MessageHandler, filters, Application
from resources.utils import defineLogs


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

telegram_token = os.getenv('TELEGRAM_TOKEN')

if os.getenv('MODE') == "dev":
    # Acceso local
    def run():
        print("CORRIENDO DESARROLLO...")
        application.run_polling()
        application.shutdown()  # permite finalizar el bot con ctrl+C

elif os.getenv('MODE') == "prod":
    # Acceso HEROKU (produccion)
    def run():
        port = int(os.environ.get('PORT', '8443'))
        host_url = os.environ.get("HOST_URL")
        application.run_webhook(listen="0.0.0.0", port=port, url_path=telegram_token, webhook_url= host_url + telegram_token)
        print("CORRIENDO PRODUCCION...")

else:
    defineLogs().info("ERROR: No se especifico el MODE")
    sys.exit

# Creo el bot con el token
if __name__ == "__main__":
    bot = telegram.Bot(token=telegram_token)

# Enlazamos el updater con el bot
application = Application.builder().token(telegram_token).build()

# COMANDOS
application.add_handler(CommandHandler("notfollowers", notfollowers))


# COMANDOS DINAMICOS
#application.add_handler(MessageHandler(filters.Regex(r"^/\w+$"), hola))


# MANEJADOR DE MENSAJES SIN "/"
#application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messageHandler))
application.add_handler(MessageHandler(filters.Document.ALL, handle_files))

# RUN
run()
