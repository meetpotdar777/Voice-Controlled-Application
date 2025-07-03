# Voice-Controlled Assistant (Jarvis)

* A personal voice assistant built with Python, capable of performing various tasks through voice commands, including opening applications, browsing the web, providing information, managing notes, and interacting with Google's Gemini AI.

# ✨ Features

## Core Assistant Commands:

* Voice Control: Interact using natural language.

* Application & URL Launching: Open websites (Google, YouTube, GitHub, LinkedIn) and launch desktop applications (Chrome, Firefox, Notepad, Calculator, etc.).

* Application & Window Closing: Close specific applications or the active window (Windows only).

* Information Queries: Get current time, date, day, and weather information for a specified city.

* Dynamic Web Search: Perform searches directly on Google, YouTube, and GitHub.

* AI Integration (Gemini): Ask general questions and receive intelligent responses powered by Google's Gemini AI.

* Personalized Memory: Store, retrieve, categorize, summarize, and delete notes/memories in a JSON file.

* Robust Command Recognition: Utilizes fuzzy matching to understand commands even with slight variations.

* Enhanced Error Handling: Provides more specific feedback for common issues.

* Help Command: Ask Jarvis for "help" or "what can you do" to get an overview of its capabilities, categorized for clarity.

* Command Cancellation: Say "cancel" or "never mind" during multi-step commands to abort the process.

## Enhanced Features (Functional with specific requirements):

* System Volume Control: Adjust, mute, and unmute system volume.

* Windows: Fully functional using pycaw.

* macOS/Linux: Functional for setting specific volume levels, muting, and unmuting using system commands (osascript on macOS, pactl on Linux). Relative volume changes (increase/decrease by X%) now include conceptual logic for getting current volume, which can vary by system setup.

* System Power Control: Safely shutdown, restart, or put your computer to sleep with verbal confirmation.

* Open System Settings: Quickly open your operating system's settings or preferences.

* System Information Queries: Get current CPU usage, RAM usage, and disk space information.

* Spotify Playback Control: Play, pause, skip next/previous song. Requires Spotify API setup and the spotipy library.

* General Music Playback (Basic Local Files): Can play the first .mp3, .wav, or .ogg file found in a configured local music directory, and attempt to play a specific song by name. Requires playsound library. (Note: Direct stopping of playsound is limited; for robust control, a different audio library would be needed).

* Calendar/Reminder Integration (Functional with Local JSON Storage):

* Add Reminders/Events: Add notes for specific dates and times (e.g., "add reminder for meeting tomorrow at 3 PM").

* Set Timers: Set countdown timers (e.g., "set a timer for 5 minutes").

* Set Alarms: Set alarms for specific times (e.g., "set an alarm for 7 AM").

* View Upcoming: List all upcoming reminders and events.

* View for Specific Day: Ask to "show reminders for tomorrow" or "show reminders for next Monday".

* Show Timers/Alarms: List active timers and alarms.

* Mark Complete: Mark a reminder or event as completed by its ID.

* Delete/Cancel: Delete specific reminders/events by ID, or cancel active timers/alarms.

* Clear All: Clear all reminders and events.
#### Note: This uses local JSON storage for demonstration. Full integration with services like Google Calendar requires additional API setup and authentication. Basic date/time parsing is implemented, but for complex phrases, dateparser is recommended.

### Continuous Listening / Hotword Detection (Simulated):

* Activate/Deactivate: Use "start listening" or "enable hotword" to turn on a simulated hotword mode. Use "stop listening" or "disable hotword" to turn it off.

* Hotword Trigger: When enabled, Jarvis will wait for you to say "Hey Jarvis". Once detected, it will then listen for your actual command. After the command, it returns to waiting for the hotword.
#### Note: This is a simulated hotword. True always-on, low-latency hotword detection requires specialized libraries (like Porcupine or PocketSphinx) and often multi-threading, which are beyond simple script integration due to their complex setup and resource usage.

### Advanced Natural Language Processing (NLP) (Basic Sentiment Analysis):

* Sentiment Analysis: Use commands like "analyze text" or "what is the sentiment of this" to get a positive, negative, or neutral sentiment analysis of a phrase you speak.
#### Note: This uses nltk's VADER lexicon. For more complex NLP tasks (like entity extraction, deeper text summarization beyond Gemini's capabilities, or intent recognition), further integration with spaCy or cloud NLP services would be required.

### Graphical User Interface (GUI) (Simulated):

* Launch/Close Interface: Use "open interface" or "show interface" to simulate launching a GUI, and "close interface" to simulate closing it.
#### Note: A visual GUI cannot be rendered directly in this text-based environment. These commands provide verbal and console feedback, indicating where a real GUI would appear and how it would interact. Full GUI implementation requires a dedicated framework like Tkinter, PyQt, or Kivy.

### Smart Home Integration (Simulated Philips Hue):

* Conceptual API Interaction: Includes functions (_hue_send_command, _hue_get_light_status, _hue_set_light) that mimic API calls to a Philips Hue Bridge.

* Commands: "turn on lights", "turn off lights", "turn on all lights", "turn off all lights", "set light brightness to [X] percent", "set [light name] brightness to [X]", "set [light name] color to [color]", "what are the lights doing", "turn on the [light name]", "turn off the [light name]", "get light status [light name]".

* Simulated Devices: The code includes a SIMULATED_HUE_LIGHTS dictionary to demonstrate state changes.
#### Note: This is a simulated integration. To make it control real Philips Hue lights, you would need:

* A Philips Hue Bridge: Connected to your local network.

* Discover Bridge IP: You'd need to find your bridge's IP address (e.g., using a network scanner or the Hue app).

* Generate a Username: Press the physical button on your Hue Bridge and then make a specific API call (e.g., POST http://<bridge_ip>/api with {"devicetype":"my_app#jarvis"}). This generates the HUE_USERNAME.

* Update GLOBAL_CONFIG: Replace "YOUR_HUE_BRIDGE_IP" and "your_hue_username" with your actual values.

* Network Access: Ensure your computer running Jarvis can reach the Hue Bridge on your local network.

* Real API Calls: Replace the _hue_send_command simulation with actual requests.get() and requests.put() calls to the Hue Bridge API.

#### The following advanced features are currently implemented as conceptual frameworks in the code. They include command recognition and verbal acknowledgments of what they would do, along with detailed comments outlining the significant additional development, external library installations, and API configurations required for full functionality.

#### Smart Home Integration (Other Devices - Conceptual): Commands like "set thermostat to", "lock doors", "unlock doors". These are still conceptual as they would require integration with other specific smart home platform APIs (e.g., Google Home, Home Assistant, smart locks, smart thermostats) beyond Philips Hue.

# 🚀 Requirements

* Python 3.7+

* Operating System: Primarily tested on Windows. Cross-platform compatibility for core functions is handled.

# 🛠️ Installation
####  Clone the repository (or download the script):
```
git clone https://github.com/your-username/voice-controlled-assistant.git
cd voice-controlled-assistant
```
#### (Replace your-username with your actual GitHub username if you create a repo, otherwise just download the .py file).

#### Create a virtual environment (recommended):
```
python -m venv venv
```
#### Activate the virtual environment:

#### Windows:
```
.\venv\Scripts\activate
```
#### macOS/Linux:
```
source venv/bin/activate
```
#### Install the required Python packages:
```
pip install -r requirements.txt
```
#### Note for pyaudio: If pip install pyaudio fails on Windows, you might need to download a pre-compiled wheel file from Unofficial Windows Binaries for Python Extensions and install it manually:

#### Example for Python 3.9 on 64-bit Windows:
```
pip install C:\path\to\PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl
```
#### Note for nltk data: After installing nltk, you might need to download the vader_lexicon for sentiment analysis. Run the following command in your Python environment once:
```
import nltk
nltk.download('vader_lexicon')
```
# ⚙️ Configuration

#### Open the voice_launcher_version_11.0.py file (or whatever you named your main script) in a text editor and customize the GLOBAL_CONFIG dictionary:
```
GLOBAL_CONFIG = {
    "CITY_NAME": "Australia",  # Your city name for weather queries
    "OPENWEATHERMAP_API_KEY": "YOUR_OPENWEATHERMAP_API_KEY", # Get your API key from openweathermap.org
    "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY", # Get your API key from Google Cloud Console (Generative Language API)
    "GEMINI_MODEL_NAME": "gemini-1.5-flash", # Recommended: 'gemini-1.5-flash' or 'gemini-1.5-pro'
    "VOICE_GENDER": "male", # Options: "male", "female", or "default"
    "SPEECH_RATE": 170, # Words per minute (adjust as desired)
    "MEMORY_FILE": "jarvis_memory.json", # File to store notes/memories
    "CALENDAR_FILE": "jarvis_calendar.json", # File to store calendar events/reminders
    "JARVIS_NAME": "Jarvis", # The name your assistant uses
    "FUZZY_MATCH_THRESHOLD": 75, # Confidence score for command recognition (0-100, higher = stricter)
    "HOTWORD": "hey jarvis", # The hotword to listen for
    # Spotify API Configuration (Requires Spotify Developer Account & App Setup)
    # UNCOMMENT AND FILL THESE FOR SPOTIFY FUNCTIONALITY:
    "SPOTIFY_CLIENT_ID": "YOUR_SPOTIFY_CLIENT_ID", # Replace with your Spotify App Client ID
    "SPOTIFY_CLIENT_SECRET": "YOUR_SPOTIFY_CLIENT_SECRET", # Replace with your Spotify App Client Secret
    "SPOTIFY_REDIRECT_URI": "http://localhost:8888/callback", # Must match your Spotify App settings exactly
    "SPOTIPY_SCOPE": "user-read-playback-state user-modify-playback-state", # Required permissions for playback control
    # Path to your local music directory for general music playback
    "LOCAL_MUSIC_DIRECTORY": os.path.join(os.path.expanduser("~"), "Music"), # Example: C:\Users\YourUser\Music or /home/YourUser/Music
    # Philips Hue Smart Home Integration (Simulated)
    # For a REAL implementation, you would need to find your Hue Bridge IP and generate a username.
    # See README.md for instructions.
    "HUE_BRIDGE_IP": "145.155.1.300", # Replace with your actual Hue Bridge IP address
    "HUE_USERNAME": "your_hue_username" # Replace with your generated Hue username
}
```
#### OPENWEATHERMAP_API_KEY: Obtain a free API key from OpenWeatherMap.

#### GEMINI_API_KEY: Obtain an API key for the Generative Language API from the Google Cloud Console. Enable the "Generative Language API" for your project.

#### CITY_NAME: Set this to your local city for accurate weather reports.

#### Spotify API Keys: To enable Spotify control, you must create a developer account and an application on the Spotify Developer Dashboard. Fill in SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI in the GLOBAL_CONFIG. You will also need to uncomment the authenticate_spotify() call in the main function (around line 600 in the provided code) if you want it to try authenticating on startup.

#### LOCAL_MUSIC_DIRECTORY: Set this to the path where your local music files (.mp3, .wav, .ogg) are stored.

#### Philips Hue Integration (HUE_BRIDGE_IP, HUE_USERNAME): These are placeholder values. For a real integration, follow the instructions in the README.md under "Smart Home Integration (Simulated Philips Hue)" to find your bridge IP and generate a username.

# 🚀 Usage

### Run the script:
```
python voice_launcher_version_11.0.py
```
#### (Replace voice_launcher_version_11.0.py with your script's actual filename if different).

### Speak your commands:

#### Jarvis will greet you and then start listening. When it says "Listening...", speak your command clearly.

### Example Commands:

#### "Hello Jarvis"

#### "How are you"

#### "Help" / "What can you do" / "List commands"

#### "Open Google"

#### "Open Notepad"

#### "Close Chrome"

#### "Close active window"

#### "Open settings"

#### "Shutdown computer" (Requires confirmation)

#### "Restart computer" (Requires confirmation)

#### "Put computer to sleep" (Requires confirmation)

#### "What time is it"

#### "What is today's date"

#### "What is the weather in Australia"

#### "What is my CPU usage"

#### "How much RAM is used"

#### "Check disk space"

#### "Search Google for Python programming"

#### "Search YouTube for latest music"

#### "Ask Jarvis what is artificial intelligence"

#### "Remember this: Buy milk and eggs"

#### "What do you remember"

#### "Show notes in category task"

#### "Search my notes for important"

#### "Edit note ID 3"

#### "Forget note ID 5" (or "Forget note about milk")

#### "Clear all notes"

#### "Set volume to 50" (or "Set volume to 50 percent")

#### "Increase volume by 10"

#### "Decrease volume by 20"

#### "Mute volume"

#### "Unmute volume"

#### "Play music" (for Spotify)

#### "Pause music" (for Spotify)

#### "Next song" (for Spotify)

#### "Previous song" (for Spotify)

#### "Play local music" (Plays the first music file found in LOCAL_MUSIC_DIRECTORY)

#### "Play song Billie Jean" (Attempts to find and play "Billie Jean" in LOCAL_MUSIC_DIRECTORY)

#### "Stop music" (Conceptual stop for local playback, as playsound has limitations)

#### "Open music player" (Attempts to open default music player)

#### "Add reminder for meeting tomorrow at 3 PM" (or "Add event for dinner next Friday at 7 PM")

#### "Set a timer for 5 minutes" (or "Set a timer for 1 hour 30 minutes")

#### "Set an alarm for 7 AM" (or "Set an alarm for 8:30 PM")

#### "Show reminders" (or "What are my appointments")

#### "Show reminders for tomorrow" (or "Show reminders for next Tuesday")

#### "Show timers"

#### "Show alarms"

#### "Mark reminder complete ID 1"

#### "Delete reminder ID 1"

#### "Cancel timer ID 2"

#### "Cancel alarm ID 3"

#### "Clear all reminders"

"Start listening" (Activates simulated hotword detection)

"Hey Jarvis" (To trigger a command while hotword detection is active)

"Stop listening" (Deactivates simulated hotword detection)

"Analyze text" (Prompts for text, then performs sentiment analysis)

"What is the sentiment of this" (Prompts for text, then performs sentiment analysis)

"Summarize document" (Prompts for text, then uses Gemini for summarization)

"Open interface" (Simulates launching a GUI)

"Show interface" (Simulates launching a GUI)

"Close interface" (Simulates closing a GUI)

"Turn on lights" (Simulates turning on all Hue lights)

"Turn off lights" (Simulates turning off all Hue lights)

"Turn on all lights" (Simulates turning on all Hue lights)

"Turn off all lights" (Simulates turning off all Hue lights)

"Turn on the living room lamp" (Simulates turning on a specific Hue light)

"Turn off the kitchen spotlight" (Simulates turning off a specific Hue light)

"Set living room lamp brightness to 50 percent" (Simulates setting brightness for a Hue light)

"Set bedroom light color to blue" (Simulates setting color for a Hue light)

"What are the lights doing" (Simulates getting status of all Hue lights)

"What is the living room lamp doing" (Simulates getting status of a specific Hue light)

"Set thermostat to 22 degrees" (for Smart Home - conceptual)

"Lock doors" (for Smart Home - conceptual)

"Unlock doors" (for Smart Home - conceptual)

"Exit" / "Goodbye" / "Quit"

# ⚠️ Troubleshooting

"Microphone Error" / "Could not understand audio":

Ensure your microphone is properly connected and configured as the default input device in your system settings.

Check microphone privacy settings on Windows.

Speak clearly and reduce background noise.

Adjust r.energy_threshold in listen_command (increase if too sensitive, decrease if not picking up speech).

"Could not request results from Google Speech Recognition service":

Verify your internet connection.

The Google Speech Recognition API (used by speech_recognition) might have temporary issues or rate limits.

"API key not configured" / "Error configuring Gemini API":

Double-check that you've correctly entered your OPENWEATHERMAP_API_KEY and GEMINI_API_KEY in the GLOBAL_CONFIG section.

Ensure the respective APIs are enabled in your Google Cloud project for Gemini.

"Application not found" / "Access denied":

Ensure the application's executable name (e.g., chrome.exe) is correct and the application is installed.

For some commands (like closing certain processes or system power actions), you might need to run the Python script as an administrator.

Volume control issues (Windows):

If pycaw fails, ensure it's installed correctly (pip install pycaw comtypes).

A very basic fallback using nircmd (if installed and in PATH) is attempted, but pycaw is preferred.

Volume control issues (macOS/Linux):

Ensure necessary system utilities are installed and in your PATH (osascript on macOS, pactl or amixer for PulseAudio/ALSA on Linux).

Relative volume changes (increase/decrease by X%) now include conceptual logic to get current volume, but real-world reliability depends on system setup.

Spotify commands not working:

You must configure your Spotify API credentials in GLOBAL_CONFIG and uncomment the authenticate_spotify() call in main.

Ensure you have installed spotipy (pip install spotipy).

Spotify needs an active device (e.g., the Spotify desktop app open and playing music, or a Spotify Connect device selected) for the commands to work.

Local music playback not working:

Ensure playsound is installed (pip install playsound).

Verify that LOCAL_MUSIC_DIRECTORY in GLOBAL_CONFIG points to a valid directory containing .mp3, .wav, or .ogg files.

playsound can sometimes have issues with specific audio formats or system configurations. Note that playsound does not offer robust stop/pause functionality; for that, a different audio library would be needed.

Calendar/Reminder date/time parsing issues:

The built-in parser is basic. For more flexible natural language date/time input, consider installing dateparser (pip install dateparser) and modifying _parse_datetime_from_speech to use it.

NLP Sentiment Analysis not working:

Ensure nltk is installed (pip install nltk).

Make sure you have downloaded the vader_lexicon by running import nltk; nltk.download('vader_lexicon') in your Python environment.

Smart Home (Philips Hue) commands not working (beyond simulation):

This is expected in this environment. To make it real, you need a physical Philips Hue Bridge, configure its IP and username in GLOBAL_CONFIG, and replace the _hue_send_command simulation with actual requests calls to your bridge. Refer to the "Smart Home Integration (Simulated Philips Hue)" section in Features and the "Future Enhancements" section.

# 💡 Future Enhancements (Roadmap for Further Development)

Continuous Listening / Hotword Detection (Full Implementation):

Concept: True always-on, low-latency listening for a specific "wake word" (e.g., "Hey Jarvis") without needing you to press a key or manually trigger listening, and with minimal resource consumption.

Implementation: Requires specialized libraries like Porcupine (more accurate, but often requires a free account for custom hotwords) or PocketSphinx (offline, less accurate, but no external accounts). This typically involves running a dedicated audio processing thread or process in the background that continuously monitors the microphone for the hotword. Upon detection, it would signal the main application to start full speech recognition.

Challenge: Resource intensive if not implemented efficiently, complex to set up due to audio stream management, and requires careful handling of multi-threading/multi-processing for responsiveness.

Advanced Natural Language Processing (NLP) (Deeper Analysis):

Concept: Moving beyond basic sentiment analysis to truly understand the meaning and intent of more complex or nuanced commands, including tasks like named entity recognition (NER), topic modeling, or more sophisticated text summarization (beyond what Gemini can provide as a general LLM).

Implementation: Involves deeper integration with libraries like spaCy (for NER, dependency parsing, etc.) or exploring more advanced summarization algorithms. For complex intent recognition, integrating with cloud-based conversational AI services like Google's Dialogflow would be a next step.

Challenge: Requires deeper understanding of NLP concepts and potentially more complex model training or API integrations.

Graphical User Interface (GUI) (Full Implementation):

Concept: Transforming Jarvis from a command-line application into a visual desktop application with buttons, text displays, and other interactive elements.

Implementation: Requires choosing a Python GUI framework such as Tkinter (built-in, simpler), PyQt / PySide (more powerful, feature-rich, cross-platform), or Kivy (designed for multi-touch applications). This involves a complete redesign of the user interaction flow from text-based to event-driven. This would likely involve running the voice recognition and command processing in a separate thread to keep the GUI responsive.

Challenge: A complete rewrite of the user interaction part of the application, managing GUI event loops, and proper threading for background tasks.

Smart Home Integration (Other Devices - Full Implementation):

Concept: Control other smart home devices (thermostats, smart locks, etc.) through voice commands, beyond just Philips Hue lights.

Implementation: Similar to Philips Hue, this would require integrating with the specific APIs of those devices or their central smart home hubs (e.g., Google Home API, Home Assistant API, specific smart lock APIs). Each integration would involve its own authentication, device discovery, and command structure.

Challenge: Requires specific API knowledge for each device/platform, handling authentication securely, and robust error handling for device communication.
