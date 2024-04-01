import os
import logging
import pvporcupine
from pvrecorder import PvRecorder
import speech_recognition as sr

class KeywordDetector:
    def __init__(self, config):
        self.config = config
        self.porcupine = None
        self.keyword_paths = []
        self.recognizer = sr.Recognizer()  # Add this line
        if config.porcupine_key or os.environ.get('PORCUPINE_KEY'):
            activation_key = config.porcupine_key or os.environ.get('PORCUPINE_KEY')
            if os.path.exists(config.models_folder):
                for file in os.listdir(config.models_folder):
                    if file.endswith('.ppn'):
                        self.keyword_paths.append(os.path.join(config.models_folder, file))

            if self.keyword_paths:
                self.porcupine = pvporcupine.create(access_key=activation_key, keyword_paths=self.keyword_paths)
                logging.debug("Porcupine initialized successfully.")
            else:
                logging.warning(f'No .ppn files found in the "{config.models_folder}" folder.')
        else:
            logging.warning('Porcupine activation key not provided. Wake word detection will not be used.')

    def listen_for_keyword(self, conversation_manager):  # Add conversation_manager as a parameter
        logging.info("Listening for keyword...")
        if self.porcupine:
            recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
            recorder.start()
            try:
                while True:
                    pcm = recorder.read()
                    result = self.porcupine.process(pcm)
                    if result >= 0:
                        logging.info("Keyword detected. Ready for speech...")
                        conversation_manager.greet_user()  # Call greet_user on conversation_manager
                        return True
            finally:
                recorder.stop()
                recorder.delete()
        else:
            try:
                with sr.Microphone() as source:
                    audio = self.recognizer.listen(source, timeout=self.config.keyword_timeout)
                    detected_text = self.recognizer.recognize_google(audio).lower()
                    if self.config.keyword in detected_text:
                        logging.info("Keyword detected. Ready for speech...")
                        conversation_manager.greet_user()  # Call greet_user on conversation_manager
                        return True
            except sr.WaitTimeoutError:
                logging.warning("Listening timed out while waiting for keyword to start.")
            except sr.UnknownValueError:
                logging.warning("Could not understand audio.")
            except sr.RequestError as e:
                logging.error(f"Could not request results; {e}")
        logging.info("Keyword not detected.")
        return False
