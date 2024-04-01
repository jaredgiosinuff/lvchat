# LVChat: Enhanced Voice-Activated AI Assistant

LVChat is an enhanced voice-activated AI assistant application that provides advanced speech recognition capabilities with conversation context management. It offers a modular and extensible architecture, allowing for easy customization and integration with various language models and APIs. LVChat supports keyword activation and continuous conversation modes, enabling seamless interaction with the assistant.

## Features

- Voice activation using wake words or continuous conversation mode
- Speech recognition using Whisper or Google Speech Recognition
- Semantic intent recognition using Picovoice Rhino, Rasa, or literal keyword matching
- Integration with Ollama or ChatGPT APIs for generating intelligent responses
- Modular architecture with support for custom extensions
- Configurable settings through a YAML configuration file or command-line arguments
- Conversation history management with configurable timeout
- Streaming or non-streaming response generation
- Verbose mode for detailed logging and debugging
- Preloading of Whisper model for faster initial response time

## Requirements

- Python 3.x
- speechRecognition library
- requests library
- argparse library
- logging library
- platform library
- collections library
- whisper library
- pyyaml library
- pvporcupine library
- pvrhino library (optional, for Picovoice Rhino intent recognition)
- rasa library (optional, for Rasa intent recognition)

## Installation

1. Clone the LVChat repository:

   ```bash
   git clone https://github.com/yourusername/lvchat.git
   ```

2. Change your working directory to the cloned repository:

   ```bash
   cd lvchat
   ```

3. Install the required libraries using pip:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up the configuration:
   - Copy the `config.yaml.example` file to `config.yaml`:

     ```bash
     cp config.yaml.example config.yaml
     ```

   - Modify the `config.yaml` file to set your desired configuration options, such as the language model, speech recognition settings, and extension configurations.

5. (Optional) If you want to use Picovoice Rhino for wake word detection or intent recognition, make sure to set the `porcupine_key` in the `config.yaml` file or as an environment variable.

6. (Optional) If you want to use custom extensions, place your extension folders inside the `extensions` directory. Each extension folder should contain an `extension.py` file and a `config.yaml` file for extension-specific configuration.

## Usage

To run the LVChat app, use the following command:

```bash
python main.py [options]
```

The available command-line options are:

- `--config`: Path to the configuration file. Default is 'config.yaml'.
- `--mode`: Mode of operation. Choose between 'keyword' for keyword activation and 'conversation' for continuous conversation mode.
- `--keyword`: Keyword phrase to listen for in keyword mode.
- `--keyword-timeout`: Timeout (in seconds) for listening for the keyword phrase.
- `--speech-timeout`: Timeout (in seconds) for listening for speech input.
- `--pause-threshold`: Pause threshold (in seconds) for speech recognition.
- `--max-history`: Maximum number of utterances to keep in the conversation history.
- `--use-whisper`: Use Whisper for speech recognition instead of Google Speech Recognition.
- `--whisper-model`: Whisper model to use (tiny, base, small, medium, large).
- `--stream-response`: Stream the response from the language model.
- `--language-model`: Language model to use with Ollama.
- `--verbose`: Show all output from the language model, including JSON data, for debugging purposes.
- `--porcupine-key`: Specify Porcupine activation key.
- `--porcupine-model-path`: Specify the path to the Porcupine model folder.
- `--ollama-url`: URL of the Ollama server.
- `--ollama-port`: Port of the Ollama server.
- `--temperature`: Temperature for the Ollama model. Default is 0.1.

Note: The app is currently configured to use Ollama API with the "dolphin-phi:2.7b-v2.6-q4_K_S" model at "localhost:11434". You can change these settings in the `config.yaml` file or through command-line arguments.

## Customization

- Customize the behavior of LVChat by modifying the `config.yaml` file or providing command-line arguments. Refer to the `config.yaml.example` file for available configuration options.

- Create custom extensions by adding a new folder for each extension inside the `extensions` directory. Each extension folder should contain an `extension.py` file with the necessary functions (`initialize`, `handle_command`, etc.) and a `config.yaml` file for extension-specific configuration. Refer to the existing extensions for examples.

- Use a different intent recognition method by updating the `intent_recognition` setting in the `config.yaml` file and providing the necessary configuration options for the selected method.

## Acknowledgements

LVChat builds upon the work of various open-source libraries and tools, including:

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Picovoice Porcupine](https://github.com/Picovoice/porcupine) for wake word detection
- [Picovoice Rhino](https://github.com/Picovoice/rhino) for intent recognition
- [Rasa](https://rasa.com/) for intent recognition
- [Ollama](https://github.com/OllamaAI/ollama) for language model integration

Special thanks to the developers and contributors of these projects for their excellent work.

## Limitations

- Text-to-speech is only supported on macOS using the built-in `say` command. Other platforms may not support text-to-speech functionality.

## Contributing

Contributions to LVChat are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.

## License

LVChat is released under the [License](LICENSE).
