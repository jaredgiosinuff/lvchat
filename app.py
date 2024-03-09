import speech_recognition as sr
import subprocess
import requests
import argparse
import logging
from collections import deque
import threading
import whisper
import io
import tempfile
import soundfile as sf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Speech recognition with conversation context management.")
parser.add_argument('--mode', type=str, default='keyword', choices=['keyword', 'conversation'],
                    help='Mode of operation: "keyword" for keyword activation, "conversation" for continuous conversation mode.')
parser.add_argument('--keyword', type=str, default="hey assistant", help='Keyword phrase to listen for in keyword mode.')
parser.add_argument('--keyword-timeout', type=float, default=5.0, help='Timeout (in seconds) for listening for the keyword phrase.')
parser.add_argument('--speech-timeout', type=float, default=5.0, help='Timeout (in seconds) for listening for speech input.')
parser.add_argument('--pause-threshold', type=float, default=0.8, help='Pause threshold (in seconds) for speech recognition.')
parser.add_argument('--max-history', type=int, default=10, help='Maximum number of utterances to keep in the conversation history.')
parser.add_argument('--use-whisper', action='store_true', help='Use Whisper for speech recognition instead of Google Speech Recognition.')
parser.add_argument('--whisper-model', type=str, default='tiny', choices=['tiny', 'base', 'small', 'medium', 'large'], help='Whisper model to use.')
args = parser.parse_args()

# Initialize Whisper model if needed
if args.use_whisper:
    model = whisper.load_model(args.whisper_model)

# Initialize the recognizer
r = sr.Recognizer()
r.pause_threshold = args.pause_threshold

# Initialize conversation history
conversation_history = deque(maxlen=args.max_history)

def transcribe_with_whisper(audio_buffer, model):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmpfile:
        audio_buffer.seek(0)
        tmpfile.write(audio_buffer.read())
        tmpfile.flush()
        result = model.transcribe(tmpfile.name)
    return result["text"].lower()

def listen_for_keyword(source):
    logging.info("Listening for keyword...")
    if args.use_whisper:
        with sr.Microphone() as mic:
            r.adjust_for_ambient_noise(mic)
            audio_data = r.record(mic, duration=args.keyword_timeout)
            audio_buffer = io.BytesIO(audio_data.get_wav_data())
            audio_text = transcribe_with_whisper(audio_buffer, model)
            if args.keyword in audio_text:
                logging.info("Keyword detected. Ready for speech...")
                return True
    else:
        try:
            audio = r.listen(source, timeout=args.keyword_timeout)
            detected_text = r.recognize_google(audio).lower()
            if args.keyword in detected_text:
                logging.info("Keyword detected. Ready for speech...")
                return True
        except sr.WaitTimeoutError:
            logging.warning("Listening timed out while waiting for keyword to start.")
        except sr.UnknownValueError:
            logging.warning("Could not understand audio.")
        except sr.RequestError as e:
            logging.error(f"Could not request results; {e}")
    logging.info("Keyword not detected.")
    return False

def listen_for_speech(source):
    logging.info("Listening for speech...")
    if args.use_whisper:
        with sr.Microphone() as mic:
            r.adjust_for_ambient_noise(mic, duration=0.5)
            audio_data = r.record(mic, duration=args.speech_timeout)
            audio_buffer = io.BytesIO(audio_data.get_wav_data())
            audio_text = transcribe_with_whisper(audio_buffer, model)
            logging.info(f"User said: {audio_text}")
            return audio_text
    else:
        try:
            audio_data = r.listen(source, timeout=args.speech_timeout)
            text = r.recognize_google(audio_data).lower()
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

def send_to_ollama_and_respond(text):
    if text is None:
        return
    conversation_history.append(f"User: {text}")
    prompt_text = "\n".join(conversation_history)
    ollama_url = "http://localhost:11434/api/generate"
    payload = {"model": "openhermes:7b-mistral-v2.5-q4_K_M", "prompt": prompt_text, "stream": False}
    try:
        response = requests.post(ollama_url, json=payload).json()["response"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending request to Ollama API: {e}")
        return
    conversation_history.append(f"Ollama: {response}")
    logging.info(f"Ollama said: {response}")
    subprocess.call(['say', response])

def main_loop(mode):
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        while True:
            if mode == "keyword":
                if not listen_for_keyword(source):
                    continue
                text = listen_for_speech(source)
                if text in ["goodbye", "goodbye assistant"]:
                    logging.info("Goodbye!")
                    subprocess.call(['say', "Goodbye!"])
                    break
                if text:
                    send_to_ollama_and_respond(text)
            elif mode == "conversation":
                text = listen_for_speech(source)
                if text in ["goodbye", "goodbye assistant"]:
                    logging.info("Goodbye!")
                    subprocess.call(['say', "Goodbye!"])
                    break
                if text:
                    send_to_ollama_and_respond(text)

if __name__ == "__main__":
    main_loop(args.mode)

