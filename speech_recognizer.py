import speech_recognition as sr
import io
import tempfile
import logging
import whisper
import threading

class SpeechRecognizer:
    def __init__(self, config):
        self.config = config
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = config.pause_threshold
        if config.use_whisper:
            self.model = whisper.load_model(config.whisper_model)
            logging.info(f"Whisper model '{config.whisper_model}' loaded.")

    def listen_for_speech(self):  # Remove conversation_manager as a parameter
        logging.info("Listening for speech...")
        if self.config.use_whisper:
            with sr.Microphone() as mic:
                self.recognizer.adjust_for_ambient_noise(mic, duration=0.5)
                audio_data = self.recognizer.record(mic, duration=self.config.speech_timeout)
                audio_buffer = io.BytesIO(audio_data.get_wav_data())
                audio_text = self.transcribe_with_whisper(audio_buffer)
                logging.info(f"User said: {audio_text}")
                return audio_text
        else:
            try:
                with sr.Microphone() as source:
                    audio_data = self.recognizer.listen(source, timeout=self.config.speech_timeout)
                    text = self.recognizer.recognize_google(audio_data).lower()
                    logging.info(f"User said: {text}")
                    return text
            except sr.WaitTimeoutError:
                logging.warning("Listening timed out while waiting for speech to start.")
                return None
            except sr.UnknownValueError:
                logging.warning("Could not understand audio.")
                return None
            except sr.RequestError as e:
                logging.error(f"Could not request results; {e}")
                return None

    def transcribe_with_whisper(self, audio_buffer):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmpfile:
            audio_buffer.seek(0)
            tmpfile.write(audio_buffer.read())
            tmpfile.flush()
            result = self.model.transcribe(tmpfile.name)
        return result["text"].lower()
