import io
import json
import zipfile
from .schemas import get_notfollowers_schema_followers, get_notfollowers_schema_following
from .utils import defineLogs, validate_json

# Diccionario para almacenar el estado de los usuarios
user_states = {}

async def message_handler(update, context):
    """Maneja mensajes recibidos."""
    defineLogs().info(f"Mensaje recibido: {update.message.text}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Mensaje recibido")

# COMANDOS
async def fans(update, context):
    """Inicia el proceso de carga de archivos para detectar seguidores que no sigues."""
    command = update.message.text
    defineLogs().info(f"El usuario {update.effective_user['username']} consultó por {command}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Por favor, sube el archivo .zip o los dos archivos .json.")
    user_states[update.effective_chat.id] = {'awaiting_files': True,
                                             'command': command,  # Guarda el comando ejecutado
                                             'files': {'followers': [], 'following': []}}


async def notfollowers(update, context):
    """Inicia el proceso de carga de archivos para detectar seguidores no mutuos."""
    command = update.message.text
    defineLogs().info(f"El usuario {update.effective_user['username']} consultó por {command}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Por favor, sube el archivo .zip o los dos archivos .json.")
    user_states[update.effective_chat.id] = {'awaiting_files': True,
                                             'command': command,  # Guarda el comando ejecutado
                                             'files': {'followers': [], 'following': []}}



# FUNCIONES
async def handle_files(update, context):
    """Maneja la recepción de archivos JSON o ZIP."""
    try:
        chat_id = update.effective_chat.id

        if chat_id not in user_states or not user_states[chat_id]['awaiting_files']:
            await context.bot.send_message(chat_id=chat_id, text="No estoy esperando archivos. Envía /notfollowers o /fans para iniciar el proceso.")
            return
        
        document = update.message.document
        file_path = await context.bot.get_file(document.file_id)
        file_byte_array = await file_path.download_as_bytearray()
        
        command = user_states[chat_id]['command']

        if document.mime_type == 'application/json':
            await process_json_file(chat_id, file_byte_array, context, command)
        elif document.mime_type == 'application/zip':
            await process_zip_file(chat_id, file_byte_array, context, command)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Por favor, sube solo archivos .json o .zip.")
    except ValueError as ve:
        defineLogs().error(ve)
        await context.bot.send_message(chat_id=chat_id, text=str(ve))
    except Exception as err:
        defineLogs().error(f"Error al procesar el archivo: {err}")
        await context.bot.send_message(chat_id=chat_id, text=f"Error al procesar el archivo: {err}")


async def process_json_file(chat_id, file_byte_array, context, command):
    """Procesa archivos JSON individuales."""
    try:
        file_to_dict = json.loads(file_byte_array.decode('utf-8'))
        
        if validate_json(file_to_dict, get_notfollowers_schema_followers()):
            user_states[chat_id]['files']['followers'].append(file_to_dict)
        elif validate_json(file_to_dict, get_notfollowers_schema_following()):
            user_states[chat_id]['files']['following'].append(file_to_dict)
        else:
            await context.bot.send_message(chat_id=chat_id, text="El formato del .json no es el esperado.")
            return
        
        if len(user_states[chat_id]['files']['followers']) > 0 and len(user_states[chat_id]['files']['following']) > 0:
            followers_data = user_states[chat_id]['files']['followers'][0]
            following_data = user_states[chat_id]['files']['following'][0]
            
            response = process_files(followers_data, following_data, command)

            await context.bot.send_message(chat_id=chat_id, text=response)
            del user_states[chat_id]

            # Forzar la liberación de memoria
            del file_byte_array
        else:
            await context.bot.send_message(chat_id=chat_id, text="Archivo recibido, por favor sube el segundo archivo .json.")
    except Exception as err:
        defineLogs().error(f"Error al procesar los archivos json: {err}")
        await context.bot.send_message(chat_id=chat_id, text=f"Error al procesar los archivos json: {err}")

async def process_zip_file(chat_id, file_byte_array, context, command):
    """Procesa archivos ZIP y extrae los JSON requeridos, liberando memoria después."""
    try:
        with zipfile.ZipFile(io.BytesIO(file_byte_array), 'r') as zip_ref:
            json_files = {name: zip_ref.read(name) for name in zip_ref.namelist() if name.endswith('.json') and "connections/followers_and_following/" in name}
            
            required_files = {'connections/followers_and_following/followers_1.json': None, 'connections/followers_and_following/following.json': None}
            
            for file_name, file_content in json_files.items():
                if file_name in required_files:
                    required_files[file_name] = json.loads(file_content.decode('utf-8'))
            
            if None in required_files.values():
                await context.bot.send_message(chat_id=chat_id, text="El archivo .zip debe contener 'followers_1.json' y 'following.json' dentro de 'connections/followers_and_following/'.")
                return
            
            user_states[chat_id]['files']['followers'].append(required_files['connections/followers_and_following/followers_1.json'])
            user_states[chat_id]['files']['following'].append(required_files['connections/followers_and_following/following.json'])


            followers_data = required_files['connections/followers_and_following/followers_1.json']
            following_data = required_files['connections/followers_and_following/following.json']
            response = process_files(followers_data, following_data, command)

            await context.bot.send_message(chat_id=chat_id, text=response)
            del user_states[chat_id]
            
        # Forzar la liberación de memoria
        del file_byte_array
    except Exception as err:
        defineLogs().error(f"Error al procesar el archivo ZIP: {err}")
        await context.bot.send_message(chat_id=chat_id, text=f"Error al procesar el archivo ZIP: {err}")


def extract_usernames_followers(data):
    """Extrae los nombres de usuario de la lista de seguidores."""
    try:
        usernames = set()
        for entry in data:
            if isinstance(entry, dict) and 'string_list_data' in entry:
                for item in entry['string_list_data']:
                    if 'value' in item:
                        usernames.add(item['value'])
                    else:
                        defineLogs().error(f"Error: 'value' no encontrado en {item}")
            else:
                defineLogs().error("Error: 'string_list_data' no encontrado o entrada no es un diccionario")
        return usernames
    except Exception as err:
        raise ValueError(f"Error extrayendo los nombres de usuario de seguidores: {err}")

def extract_usernames_following(json_data):
    """Extrae los nombres de usuario de la lista de seguidos."""
    try:
        return {entry['string_list_data'][0]['value'] for entry in json_data['relationships_following']}
    except Exception as err:
        raise ValueError(f"Error extrayendo los nombres de usuario de seguidos: {err}")

def process_files(followers, following, command):
    """Compara listas de seguidores y seguidos para encontrar usuarios que no te siguen de vuelta."""
    try:
        if not isinstance(followers, list) or not isinstance(following, dict):
            return "Error en los datos"
        followers_set = extract_usernames_followers(followers)
        following_set = extract_usernames_following(following)
    
        if command == '/notfollowers':
            difference = following_set - followers_set
            if not difference:
                return 'No hay usuarios que no te sigan de vuelta.'
            return 'Listado de usuarios que no te siguen de vuelta:\n\n' + '\n'.join(f"- {user}" for user in sorted(difference)) + f"\n\nTotal: {len(difference)}"
        else:   # El comando es /fans
            difference =  followers_set - following_set
            if not difference:
                return 'No hay usuarios que te sigan y no los sigas de vuelta.'
        
            return 'Listado de usuarios que te siguen sin que los sigas de vuelta:\n\n' + '\n'.join(f"- {user}" for user in sorted(difference)) + f"\n\nTotal: {len(difference)}"
    except ValueError as ve:
        raise ValueError(ve)
    except Exception as err:
        raise ValueError(f"Error comparando seguidores y seguidos: {err}")
