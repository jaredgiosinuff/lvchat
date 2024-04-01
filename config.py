# config.py
import os
import logging

class Config:
    def __init__(self, config_data):
        self.mode = config_data.get('mode')
        self.keyword = config_data.get('keyword')
        self.keyword_timeout = config_data.get('keyword_timeout')
        self.speech_timeout = config_data.get('speech_timeout')
        self.pause_threshold = config_data.get('pause_threshold')
        self.max_history = config_data.get('max_history')
        self.use_whisper = config_data.get('use_whisper')
        self.whisper_model = config_data.get('whisper_model')
        self.stream_response = config_data.get('stream_response')
        self.language_model = config_data.get('language_model')
        self.verbose = config_data.get('verbose')
        logging.debug(f"Loaded config: verbose = {self.verbose}")
        self.porcupine_key = config_data.get('porcupine_key')
        self.porcupine_model_path = config_data.get('porcupine_model_path')
        self.ollama_url = config_data.get('ollama_url')
        self.ollama_port = config_data.get('ollama_port')
        self.temperature = config_data.get('temperature')
        self.history_timeout = config_data.get('history_timeout')

        script_dir = os.path.dirname(os.path.abspath(__file__))
        models_folder = os.path.join(script_dir, 'models')
        if not os.path.exists(models_folder):
            models_folder = config_data.get('porcupine_model_path', os.path.join('lvchat', 'models'))
        self.models_folder = models_folder

    @staticmethod
    def get_default_config():
        return {
            'mode': 'keyword',
            'keyword': 'hey assistant',
            'keyword_timeout': 5.0,
            'speech_timeout': 5.0,
            'pause_threshold': 0.8,
            'max_history': 10,
            'use_whisper': False,
            'whisper_model': 'tiny',
            'stream_response': True,
            'history_timeout': 300,
            'language_model': 'openhermes:7b-mistral-v2.5-q4_K_M',
            'verbose': False,
            'porcupine_key': None,
            'porcupine_model_path': None,
            'ollama_url': 'http://localhost',
            'ollama_port': 11434,
            'temperature': 0.1
        }
