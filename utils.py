import logging
from jsonschema import validate, ValidationError

def defineLogs():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s,"
    )
    return logging.getLogger()

def validate_json(json_data, schema):
    try:
        validate(instance=json_data, schema=schema)
        return True
    except ValidationError:
        return False
