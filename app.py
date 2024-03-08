import speech_recognition as sr
import subprocess
import requests
import argparse
import sys
import logging
import platform
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Speech recognition with conversation context management.")
parser.add_argument('--mode', type=str, default='keyword', choices=['keyword', 'conversation'],
                    help='Mode of operation: "keyword" for keyword activation, "conversation" for continuous conversation mode.')
parser.add_argument('--keyword', type=str, default="hey assistant", help='Keyword phrase to listen for in keyword mode.')
parser.add_argument('--keyword-timeout', type=float, default=3.0, help='Timeout (in seconds) for listening for the keyword phrase.')
parser.add_argument('--speech-timeout', type=float, default=2.0, help='Timeout (in seconds) for listening for speech input.')
parser.add_argument('--pause-threshold', type=float, default=0.8, help='Pause threshold (in seconds) for speech recognition.')
parser.add_argument('--max-history', type=int, default=10, help='Maximum number of utterances to keep in the conversation history.')
args = parser.parse_args()

# Set up Ollama API configuration
OLLAMA_IP = "localhost"
OLLAMA_PORT = 11434
OLLAMA_MODEL = "openhermes:7b-mistral-v2.5-q4_K_M"

# Initialize the recognizer
r = sr.Recognizer()
r.pause_threshold = args.pause_threshold

# Initialize conversation history
conversation_history = deque(maxlen=args.max_history)

def listen_for_keyword(source):
    logging.info("Listening for keyword...")
    try:
        audio = r.listen(source, timeout=args.keyword_timeout)
        detected_text = r.recognize_google(audio).lower()
        if args.keyword in detected_text:
            logging.info("Keyword detected. Ready for speech...")
            return True
        else:
            logging.info("Keyword not detected.")
            return False
    except sr.UnknownValueError:
        logging.warning("Could not understand audio.")
    except sr.RequestError as e:
        logging.error(f"Could not request results; {e}")
    return False

def listen_for_speech(source):
    try:
        audio_data = r.listen(source, timeout=args.speech_timeout)
        text = r.recognize_google(audio_data).lower()
        logging.info(f"User said: {text}")
        return text
    except sr.UnknownValueError:
        logging.warning("Could not understand audio.")
    except sr.RequestError as e:
        logging.error(f"Could not request results; {e}")

def send_to_ollama_and_respond(text, use_openai=False):
    conversation_history.append(f"User: {text}")
    prompt_text = "\n".join(conversation_history)
    if use_openai:
        # Placeholder for OpenAI API call
        response = "Response from OpenAI using conversation history."
    else:
        ollama_url = f"http://{OLLAMA_IP}:{OLLAMA_PORT}/api/generate"
        payload = {"model": OLLAMA_MODEL, "prompt": prompt_text, "stream": False}
        try:
            response = requests.post(ollama_url, json=payload).json()["response"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending request to Ollama API: {e}")
            return

    conversation_history.append(f"Ollama: {response}")
    logging.info(f"Ollama said: {response}")
    if platform.system() == "Darwin":
        subprocess.call(['say', response])
    else:
        logging.warning("Text-to-speech not supported on this platform.")

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
                    if platform.system() == "Darwin":
                        subprocess.call(['say', "Goodbye!"])
                    break
                if text:
                    send_to_ollama_and_respond(text)
            elif mode == "conversation":
                text = listen_for_speech(source)
                if text in ["goodbye", "goodbye assistant"]:
                    logging.info("Goodbye!")
                    if platform.system() == "Darwin":
                        subprocess.call(['say', "Goodbye!"])
                    break
                if text:
                    send_to_ollama_and_respond(text)

if __name__ == "__main__":
    main_loop(args.mode)
