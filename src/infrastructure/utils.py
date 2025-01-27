import os
import json
from infrastructure.logger import logger

def read_json_file(file_path: str) -> dict:
    """
    Reads a JSON file from the specified path and returns its contents as a dictionary.

    Args:
        file_path (str): The path to the JSON file to be read.

    Returns:
        dict: The contents of the JSON file as a dictionary.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is not a valid JSON file.
        json.JSONDecodeError: If the file contents cannot be decoded as JSON.
    """

    if not os.path.isfile(file_path):
        message = f"File not found or not a valid file: {file_path}"
        logger.error(message)
        raise FileNotFoundError(message)

    if not file_path.lower().endswith('.json'):
        message = f"File is not a valid JSON file: {file_path}"
        logger.error(message)
        raise ValueError(message)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        message = f"Failed to decode JSON from file {file_path}: {e}"
        logger.error(message)
        raise e
    except Exception as e:
        message = f"An unexpected error occurred while reading the file {file_path}: {e}"
        logger.error(message)
        raise
