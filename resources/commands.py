import json
from schemas import get_notfollowers_schema_followers, get_notfollowers_schema_following
from .utils import defineLogs, validate_json

user_states = {}


async def messageHandler(update, context):
    defineLogs().info(f"Mensaje recibido: {update.message.text}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Mensaje recibido")


# NOTFOLLOWERS
async def notfollowers(update, context):
    defineLogs().info(f"El usuario {update.effective_user['username']} consultó por /notfollowers")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Por favor, sube los dos archivos .json.")
    user_states[update.effective_chat.id] = {'awaiting_files': True, 'files': {'followers': [], 'following': []}}


# FILES HANDLER
async def handle_files(update, context):
    try:
        chat_id = update.effective_chat.id
        
        if chat_id in user_states and user_states[chat_id]['awaiting_files']:
            document = update.message.document
            
            if document.mime_type == 'application/json':
                file_path = await context.bot.get_file(document.file_id)
                file = await file_path.download_as_bytearray()
                file_to_dict = json.loads(file.decode('utf-8'))

                if validate_json(file_to_dict, get_notfollowers_schema_followers()) or validate_json(file_to_dict, get_notfollowers_schema_following()):
                    if 'followers' in document.file_name:
                        user_states[chat_id]['files']['followers'].append(file_to_dict)
                    elif 'following' in document.file_name:
                        user_states[chat_id]['files']['following'].append(file_to_dict)
                    
                    if (len(user_states[chat_id]['files']['followers']) > 0 and len(user_states[chat_id]['files']['following']) > 0):
                        # Procesa los archivos JSON
                        response = process_files(followers=user_states[chat_id]['files']['followers'][0], following=user_states[chat_id]['files']['following'][0])
                        await context.bot.send_message(chat_id=chat_id, text=response)
                        del user_states[chat_id]  # Reset state after process
                    else:
                        await context.bot.send_message(chat_id=chat_id, text="Archivo recibido, por favor sube el segundo archivo .json.")
                else:
                    await context.bot.send_message(chat_id=chat_id, text="El formato del .json no es el esperado. Vuelve a intentarlo con otro archivo.")
            else:
                await context.bot.send_message(chat_id=chat_id, text="Por favor, sube solo archivos .json.")
        else:
            await context.bot.send_message(chat_id=chat_id, text="No estoy esperando archivos. Envía /notfollowers para iniciar el proceso.")
    except ValueError as ve:
        defineLogs().error(ve)
        await context.bot.send_message(chat_id=chat_id, text=ve)
    except Exception as err:
        defineLogs().error(f"Error downloading file from telegram: {err}")
        await context.bot.send_message(chat_id=chat_id, text=f"Error downloading file from telegram: {err}")


def process_files(followers, following):
    def extract_usernames_followers(data):
        """Extrae los nombres de usuario de una lista de diccionarios."""
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
                    defineLogs().error(f"Error: 'string_list_data' no encontrado o entrada no es un diccionario")
            return usernames
        except Exception as err:
            raise ValueError(f"Error extracting followers username: {err}")

    def extract_usernames_following(json_data):
        try:
            return {entry['string_list_data'][0]['value'] for entry in json_data['relationships_following']}
        except Exception as err:
            raise ValueError(f"Error extracting following username: {err}")

    # Asegúrate de que followers y following sean listas
    try:
        if not isinstance(followers, list) or not isinstance(following, dict):
            return "Error en los datos"
        followers_set = extract_usernames_followers(followers)
        following_set = extract_usernames_following(following)
    
        # Encuentra los usuarios que están en following pero no en followers
        difference = following_set - followers_set
        
        # Convierte el resultado a una lista para poder manejarlo como texto
        if not difference:
            return 'No hay usuarios que no te sigan de vuelta.'
        mssg = 'Listado de usuarios que no te siguen de vuelta:\n\n'
        for user in difference:
            mssg = mssg + f"- {user}\n"
        return mssg
    except ValueError as ve:
        raise ValueError(ve)
    except Exception as err:
        raise ValueError(f"Error getting difference between followers and following: {err}")
