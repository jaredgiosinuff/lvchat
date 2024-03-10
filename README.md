LVChat: Speech Recognition Local Voice Chat with Ollama
==============================================================

LVChat is an application that provides speech recognition capabilities with conversation context management. It supports two modes of operation: keyword activation and continuous conversation mode. The app uses Google Speech Recognition API for speech-to-text conversion and Ollama API for generating responses based on the conversation context.  Remember, in Settings->Accessibility->Spoken Content you can change the voice used by the Say command to a Siri voice that does decent fast tts generation.

Requirements
------------

* Ollama running on your local system, with the openhermes:7b-mistral-v2.5-q4_K_M model running.   You can change this inside the script if you do not have that model.  This will soon be customizable.

* Python 3.x
* speech\_recognition library
* requests library
* argparse library
* logging library
* platform library
* collections library
* whisper library


Installation
------------

1. Install the required libraries using pip:
```
pip install speechRecognition requests
```
1. Clone this repository:
```bash
git clone https://github.com/jaredgiosinuff/lvchat.git
```
1. Change your working directory to the cloned repository:
```bash
cd lvchat
```
Usage
-----

To run the LVChat app, use the following command:
```bash
python app.py [options]
```
The available command-line options are:

* `--mode`: Mode of operation. Choose between 'keyword' for keyword activation and 'conversation' for continuous conversation mode. Default is 'keyword'.
* `--keyword`: Keyword phrase to listen for in keyword mode. Default is "hey assistant".
* `--keyword-timeout`: Timeout (in seconds) for listening for the keyword phrase. Default is 3.0.
* `--speech-timeout`: Timeout (in seconds) for listening for speech input. Default is 2.0.
* `--pause-threshold`: Pause threshold (in seconds) for speech recognition. Default is 0.8.
* `--max-history`: Maximum number of utterances to keep in the conversation history. Default is 10.
* `--use-whisper`: This will use whisper instead of Google's speech recognition library for speech-to-text.
* `--whisper-model`: The choices for the whisper model are 'tiny', 'base', 'small', 'medium' or 'large'.  For CPU inferencing tiny is recommended.
* `--stream-response`: This will stream and buffer the response from ollama.  This will start speaking the response sooner, one sentence at a time.

Note: The app is currently configured to use Ollama API with the "openhermes:7b-mistral-v2.5-q4\_K\_M" model at "localhost:11434". You can change these settings in the script if needed.

Example
-------

To run LVChat in keyword mode with the default settings, use the following command:
```bash
python app.py --mode keyword
```
To run LVChat in continuous conversation mode with a custom keyword phrase, use the following command:
```bash
python app.py --mode conversation --keyword "hello assistant"
```
License
-------

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

Acknowledgements
----------------

* Google Speech Recognition API: <https://cloud.google.com/speech-to-text>
* Ollama API: <https://github.com/ollama-ai/ollama>

Limitations
-----------

* Text-to-speech is only supported on macOS using the built-in `say` command. Other platforms may not support text-to-speech functionality.
