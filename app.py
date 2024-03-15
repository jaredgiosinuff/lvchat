import speech_recognition as sr
import subprocess
import requests
import argparse
import logging
from collections import deque
import whisper
import io
import tempfile
import random
import re
import json
import nltk
import select
import sys
import termios
import tty

# Ensure nltk punkt tokenizer is downloaded
nltk.download('punkt', quiet=True)

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
parser.add_argument('--stream-response', action='store_true', default=True, help='Stream the response from the language model. Default is True.')
parser.add_argument('--language-model', type=str, default='openhermes:7b-mistral-v2.5-q4_K_M', help='Language model to use with Ollama.')
parser.add_argument('--verbose', action='store_true', help='Show all output from the language model, including JSON data, for debugging purposes.')
args = parser.parse_args()

# Initialize Whisper model if needed
if args.use_whisper:
    model = whisper.load_model(args.whisper_model)

# Initialize the recognizer
r = sr.Recognizer()
r.pause_threshold = args.pause_threshold

# Initialize conversation history
conversation_history = deque(maxlen=args.max_history)

def flush_input():
    """Flush any pending input from stdin to ensure fresh read for spacebar."""
    termios.tcflush(sys.stdin, termios.TCIFLUSH)

def check_for_spacebar_input_non_blocking():
    """Non-blocking check for spacebar input, returns True if spacebar was pressed."""
    flush_input()
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        [i, o, e] = select.select([sys.stdin], [], [], 0.1)
        if i:
            input_char = sys.stdin.read(1)
            return input_char == ' '
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    return False

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
                greet_user()
                return True
    else:
        try:
            audio = r.listen(source, timeout=args.keyword_timeout)
            detected_text = r.recognize_google(audio).lower()
            if args.keyword in detected_text:
                logging.info("Keyword detected. Ready for speech...")
                greet_user()
                return True
        except sr.WaitTimeoutError:
            logging.warning("Listening timed out while waiting for keyword to start.")
        except sr.UnknownValueError:
            logging.warning("Could not understand audio.")
        except sr.RequestError as e:
            logging.error(f"Could not request results; {e}")
    logging.info("Keyword not detected.")
    return False

def greet_user():
    greetings = ["Hello.. how can I help you?", "Hey there.. what can I do for you?", "Hi.. ready to assist you.", "Hello"]
    greeting = random.choice(greetings)
    subprocess.call(['say', greeting])

def processing_model_response():
    responses = ["Give me a moment to ponder that.", "just a moment, while I consider what you have said"]
    response = random.choice(responses)
    subprocess.call(['say', response])

def listen_for_speech(source):
    logging.info("Listening for speech...")
    if args.use_whisper:
        with sr.Microphone() as mic:
            r.adjust_for_ambient_noise(mic, duration=0.5)
            audio_data = r.record(mic, duration=args.speech_timeout)
            audio_buffer = io.BytesIO(audio_data.get_wav_data())
            audio_text = transcribe_with_whisper(audio_buffer, model)
            logging.info(f"User said: {audio_text}")
            processing_model_response()
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

def speak_sentence(sentence):
    """Speak a single sentence, checking for spacebar input before and after speaking."""
    if check_for_spacebar_input_non_blocking():
        logging.info("Interrupted by user before speaking. Listening for keyword...")
        return True
    subprocess.call(['say', sentence])  # Speak the sentence
    if check_for_spacebar_input_non_blocking():
        logging.info("Interrupted by user after speaking. Listening for keyword...")
        return True
    return False

def send_to_ollama_and_respond(text):
    if text is None:
        logging.info("No text to send for processing.")
        return
    conversation_history.append(f"User: {text}")
    prompt_text = "\n".join(conversation_history)
    ollama_url = "http://localhost:11434/api/generate"
    payload = {"model": args.language_model, "prompt": prompt_text, "stream": args.stream_response}

    logging.info("Sending text to language model for processing...")
    try:
        response = requests.post(ollama_url, json=payload, stream=args.stream_response)
        sentence_buffer = ""
        if args.stream_response:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if args.verbose:
                        logging.info(f"Streamed JSON data: {data}")
                    if 'response' in data:
                        sentence_buffer += data['response']
                        if any(sentence_buffer.endswith(punc) for punc in '.!?'):
                            if sentence_buffer.strip():
                                if speak_sentence(sentence_buffer):
                                    return
                                conversation_history.append(f"Ollama: {sentence_buffer}")
                                sentence_buffer = ""  # Reset buffer after speaking
                        if data.get("done", False):
                            break
            if sentence_buffer.strip():
                if speak_sentence(sentence_buffer):
                    return
                conversation_history.append(f"Ollama: {sentence_buffer}")
        else:
            data = response.json()
            if 'response' in data:
                sentences = re.split('(?<=[.!?]) +', data['response'])
                for sentence in sentences:
                    if sentence:
                        if speak_sentence(sentence):
                            return
                        conversation_history.append(f"Ollama: {sentence}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending request to Ollama API: {e}")

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
                    if speak_sentence("Goodbye!"):
                        return
                    break
                if text:
                    send_to_ollama_and_respond(text)
            elif mode == "conversation":
                text = listen_for_speech(source)
                if text in ["goodbye", "goodbye assistant"]:
                    logging.info("Goodbye!")
                    if speak_sentence("Goodbye!"):
                        return
                    break
                if text:
                    send_to_ollama_and_respond(text)

if __name__ == "__main__":
    main_loop(args.mode)

