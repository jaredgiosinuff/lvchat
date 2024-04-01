# conversation_manager.py
from collections import deque
import random
import subprocess
import logging
import threading
import select
import termios
import tty
import sys
import time

class ConversationManager:
    def __init__(self, config):
        self.config = config
        self.conversation_history = deque(maxlen=config.max_history)
        self.history_timeout = config.history_timeout
        self.last_interaction_time = time.time()

    def update_last_interaction_time(self):
        self.last_interaction_time = time.time()

    def check_history_timeout(self):
        current_time = time.time()
        if current_time - self.last_interaction_time > self.history_timeout:
            logging.info("Conversation history timed out. Clearing history.")
            self.conversation_history.clear()
            self.last_interaction_time = current_time

    def greet_user(self):
        greetings = ["Hello.. how can I help you?", "Hey there.. what can I do for you?", "Hi.. ready to assist you.", "Hello"]
        greeting = random.choice(greetings)
        subprocess.call(['say', greeting])

    def processing_model_response(self):
        responses = ["Give me a moment to ponder that.", "just a moment, while I consider what you have said"]
        response = random.choice(responses)
        subprocess.call(['say', response])

    def speak_sentence(self, sentence):
        if self.check_for_spacebar_input_non_blocking():
            logging.info("Interrupted by user before speaking. Listening for keyword...")
            return True
        subprocess.call(['say', sentence])
        if self.check_for_spacebar_input_non_blocking():
            logging.info("Interrupted by user after speaking. Listening for keyword...")
            return True
        self.update_last_interaction_time()
        return False

    def say_goodbye(self):
        logging.info("Goodbye!")
        if self.speak_sentence("Goodbye!"):
            return

    def check_for_spacebar_input_non_blocking(self):
        self.flush_input()
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

    def flush_input(self):
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
