# ollama_client.py
import requests
import json
import re
import logging
import threading
import time

class OllamaClient:
    def __init__(self, config):
        self.config = config
        self.ollama_url = config.ollama_url
        self.ollama_port = config.ollama_port

    def send_to_ollama_and_respond(self, text, conversation_manager, prompt=None):
        if text is None:
            logging.info("No text to send for processing.")
            return
        conversation_manager.conversation_history.append(f"User: {text}")
        prompt_text = "\n".join(conversation_manager.conversation_history)
        ollama_url = f"{self.ollama_url}:{self.ollama_port}/api/generate"
        payload = {"model": self.config.language_model, "prompt": prompt_text, "stream": self.config.stream_response}

        # Start a new thread for the verbal response
        response_thread = threading.Thread(target=conversation_manager.processing_model_response)
        response_thread.start()

        # Wait for the verbal response thread to complete
        response_thread.join()

        logging.info("Sending text to language model for processing...")
        try:
            response = requests.post(ollama_url, json=payload, stream=self.config.stream_response)
            sentence_buffer = ""
            if self.config.stream_response:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if self.config.verbose:
                            logging.info(f"Streamed JSON data: {data}")
                        if 'response' in data:
                            sentence_buffer += data['response']
                            if any(sentence_buffer.endswith(punc) for punc in '.!?'):
                                if sentence_buffer.strip():
                                    if conversation_manager.speak_sentence(sentence_buffer):
                                        return
                                    conversation_manager.conversation_history.append(f"Ollama: {sentence_buffer}")
                                    sentence_buffer = ""
                            if data.get("done", False):
                                break
                if sentence_buffer.strip():
                    if conversation_manager.speak_sentence(sentence_buffer):
                        return
                    conversation_manager.conversation_history.append(f"Ollama: {sentence_buffer}")
            else:
                data = response.json()
                if 'response' in data:
                    sentences = re.split('(?<=[.!?]) +', data['response'])
                    for sentence in sentences:
                        if sentence:
                            if conversation_manager.speak_sentence(sentence):
                                return
                            conversation_manager.conversation_history.append(f"Ollama: {sentence}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending request to Ollama API: {e}")
