import argparse
import logging
import os
import importlib
import yaml
from config import Config
from conversation_manager import ConversationManager
from speech_recognizer import SpeechRecognizer
from keyword_detector import KeywordDetector
from ollama_client import OllamaClient

def parse_arguments():
    parser = argparse.ArgumentParser(description="Speech recognition with conversation context management.")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to the configuration file')
    parser.add_argument('--mode', type=str, choices=['keyword', 'conversation'], help='Mode of operation')
    parser.add_argument('--keyword', type=str, help='Keyword phrase to listen for in keyword mode')
    parser.add_argument('--keyword-timeout', type=float, help='Timeout (in seconds) for listening for the keyword phrase')
    parser.add_argument('--speech-timeout', type=float, help='Timeout (in seconds) for listening for speech input')
    parser.add_argument('--pause-threshold', type=float, help='Pause threshold (in seconds) for speech recognition')
    parser.add_argument('--max-history', type=int, help='Maximum number of utterances to keep in the conversation history')
    parser.add_argument('--use-whisper', type=bool, help='Use Whisper for speech recognition')
    parser.add_argument('--whisper-model', type=str, choices=['tiny', 'base', 'small', 'medium', 'large'], help='Whisper model to use')
    parser.add_argument('--stream-response', type=bool, help='Stream the response from the language model')
    parser.add_argument('--language-model', type=str, help='Language model to use with Ollama')
    parser.add_argument('--verbose', action='store_true', help='Show all output from the language model, including JSON data')
    parser.add_argument('--porcupine-key', type=str, help='Specify Porcupine activation key')
    parser.add_argument('--porcupine-model-path', type=str, help='Specify the path to the Porcupine model folder')
    parser.add_argument('--ollama-url', type=str, help='URL of the Ollama server')
    parser.add_argument('--ollama-port', type=int, help='Port of the Ollama server')
    parser.add_argument('--temperature', type=float, help='Temperature for the Ollama model')
    return parser.parse_args()

def load_config(config_path):
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return config_data
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Error loading config file: {e}")
        return {}

def merge_config_and_args(config_data, args, config_path):
    merged_config = {}

    # Load default values from Config class
    default_config = Config.get_default_config()

    # Merge values based on the specified logic
    for key in default_config:
        if hasattr(args, key) and getattr(args, key) is not None:
            value = getattr(args, key)
            logging.info(f"Using {key} = {value} provided in command-line argument")
            merged_config[key] = value
        elif key in config_data:
            value = config_data[key]
            logging.info(f"Using {key} = {value} provided in {config_path}")
            merged_config[key] = value
        else:
            value = default_config[key]
            logging.info(f"Using default {key} = {value}")
            merged_config[key] = value

    return merged_config

def load_extensions(extensions_dir, config):
    extensions = []
    for extension_name in os.listdir(extensions_dir):
        extension_path = os.path.join(extensions_dir, extension_name)
        if os.path.isdir(extension_path):
            module_path = os.path.join(extension_path, f"{extension_name}_extension.py")
            if os.path.isfile(module_path):
                module_name = f"extensions.{extension_name}.{extension_name}_extension"
                module = importlib.import_module(module_name)
                if hasattr(module, 'initialize'):
                    extension_config_path = os.path.join(extension_path, "config.yaml")
                    if os.path.isfile(extension_config_path):
                        with open(extension_config_path, 'r') as f:
                            extension_config = yaml.safe_load(f)
                        module.initialize(extension_config)
                    else:
                        module.initialize(config)
                extensions.append(module)
    return extensions

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    args = parse_arguments()

    # Step 1: Check for arguments
    if len(vars(args)) == 1:  # Only 'config' argument is present by default
        logging.info("No arguments received.")
    else:
        logging.info("Arguments received:")
        for arg_name, arg_value in vars(args).items():
            if arg_name != 'config' and arg_value is not None:
                logging.info(f"{arg_name}: {arg_value}")

    # Step 2: Check for config.yaml
    config_path = args.config
    if os.path.exists(config_path):
        logging.info(f"Reading config file '{config_path}' found at {os.path.abspath(config_path)}")
        config_data = load_config(config_path)
    else:
        logging.info(f"Config file '{config_path}' not found. Using default values.")
        config_data = {}

    # Step 3: Merge config and arguments
    merged_config = merge_config_and_args(config_data, args, config_path)
    config = Config(merged_config) 

    if config.verbose or args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    speech_recognizer = SpeechRecognizer(config)
    keyword_detector = KeywordDetector(config)
    conversation_manager = ConversationManager(config)
    ollama_client = OllamaClient(config)

    extensions_dir = 'extensions'
    extensions = load_extensions(extensions_dir, merged_config)

    while True:
        if config.mode == "keyword":
            if not keyword_detector.listen_for_keyword(conversation_manager):
                continue
            text = speech_recognizer.listen_for_speech()
            if text in ["goodbye", "goodbye assistant"]:
                conversation_manager.say_goodbye()
                break
            if text:
                handled = False
                for extension in extensions:
                    if hasattr(extension, 'handle_command'):
                        handled = extension.handle_command(text, conversation_manager, ollama_client)
                        if handled:
                            break
                if not handled:
                    ollama_client.send_to_ollama_and_respond(text, conversation_manager)
        elif config.mode == "conversation":
            text = speech_recognizer.listen_for_speech()
            if text in ["goodbye", "goodbye assistant"]:
                conversation_manager.say_goodbye()
                break
            if text:
                handled = False
                for extension in extensions:
                    if hasattr(extension, 'handle_command'):
                        handled = extension.handle_command(text, conversation_manager, ollama_client)
                        if handled:
                            break
                if not handled:
                    ollama_client.send_to_ollama_and_respond(text, conversation_manager)

if __name__ == "__main__":
    main()
