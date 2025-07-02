import speech_recognition as sr
import pyttsx3
import os
import platform
import subprocess
import webbrowser
import datetime
import psutil
from fuzzywuzzy import process
import requests
import google.generativeai as genai
import time # Import time for sleep
import json # Import json module for structured memory
import threading # For non-blocking operations like playsound

# --- NEW IMPORTS FOR ENHANCED FEATURES ---
# For General Music Playback (basic local file playback)
try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    print("Warning: 'playsound' not installed. General music playback will not work.")
    print("To install: pip install playsound")
    PLAYSOUND_AVAILABLE = False
except Exception as e:
    print(f"Error importing playsound: {e}. General music playback may not work.")
    PLAYSOUND_AVAILABLE = False

# Windows-specific imports for volume and window control
if platform.system() == "Windows":
    try:
        import win32gui
        import win32con
        import win32process
        WINDOWS_GUI_AVAILABLE = True
    except ImportError:
        print("Warning: 'pywin32' not installed. Windows-specific GUI control (close active window) will not work.")
        print("To install: pip install pywin32")
        WINDOWS_GUI_AVAILABLE = False
else:
    WINDOWS_GUI_AVAILABLE = False

# For Volume Control (Windows specific - requires 'pycaw')
# You'll need to install it: pip install pycaw comtypes
try:
    if platform.system() == "Windows":
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
        PYCAW_AVAILABLE = True
    else:
        PYCAW_AVAILABLE = False
except ImportError:
    print("Warning: 'pycaw' not installed. Windows volume control commands will not work.")
    print("To install: pip install pycaw comtypes")
    PYCAW_AVAILABLE = False
except Exception as e:
    print(f"Error importing pycaw: {e}. Windows volume control commands may not work.")
    PYCAW_AVAILABLE = False

# For Spotify Control (Requires 'spotipy')
# You'll need to install it: pip install spotipy
try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    print("Warning: 'spotipy' not installed. Spotify control commands will not work.")
    print("To install: pip install spotipy")
    SPOTIPY_AVAILABLE = False
except Exception as e:
    print(f"Error importing spotipy: {e}. Spotify control commands may not work.")
    SPOTIPY_AVAILABLE = False

# For Advanced NLP (NLTK for sentiment analysis)
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    # You might need to download the 'vader_lexicon' if you run this for the first time
    # Run: nltk.download('vader_lexicon') in your Python environment
    NLTK_AVAILABLE = True
except ImportError:
    print("Warning: 'nltk' not installed. Advanced NLP features will be limited.")
    print("To install: pip install nltk")
    NLTK_AVAILABLE = False
except Exception as e:
    print(f"Error importing nltk: {e}. Advanced NLP features may be limited.")
    NLTK_AVAILABLE = False


# --- GLOBAL CONFIGURATION (IMPORTANT: Customize these values) ---
GLOBAL_CONFIG = {
    "CITY_NAME": "Australia",  # Your city name for weather queries
    "OPENWEATHERMAP_API_KEY": "YOUR_OPENWEATHERMAP_API_KEY", # Get from openweathermap.org
    "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY", # Get from console.cloud.google.com (Generative Language API)
    "GEMINI_MODEL_NAME": "gemini-1.5-flash", # Changed to a commonly supported model. You can try 'gemini-1.5-pro' if preferred.
    "VOICE_GENDER": "male", # Options: "male", "female", or "default"
    "SPEECH_RATE": 170, # Words per minute (adjust as desired)
    "MEMORY_FILE": "jarvis_memory.json", # Changed to JSON file for structured memory
    "CALENDAR_FILE": "jarvis_calendar.json", # File to store calendar events/reminders
    "JARVIS_NAME": "Jarvis", # Define Jarvis's name
    "FUZZY_MATCH_THRESHOLD": 75, # Confidence score for command recognition (0-100)
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
    "HUE_BRIDGE_IP": "192.168.1.100", # Replace with your actual Hue Bridge IP address
    "HUE_USERNAME": "your_hue_username" # Replace with your generated Hue username
}
# --- END GLOBAL CONFIGURATION ---


# --- Initialize Text-to-Speech Engine ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Attempt to set voice based on preference
try:
    if GLOBAL_CONFIG["VOICE_GENDER"].lower() == "male":
        male_voice_found = False
        for voice in voices:
            if "male" in voice.name.lower() or "david" in voice.name.lower() or voice.id.endswith("0"):
                engine.setProperty('voice', voice.id)
                male_voice_found = True
                break
        if not male_voice_found and len(voices) > 0:
            engine.setProperty('voice', voices[0].id)
            print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Male voice not explicitly found or set. Falling back to first available voice.")
        elif not male_voice_found:
             print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] No voices found. Using system default.")

    elif GLOBAL_CONFIG["VOICE_GENDER"].lower() == "female":
        female_voice_found = False
        for voice in voices:
            if "female" in voice.name.lower() or "zira" in voice.name.lower() or voice.id.endswith("1"):
                engine.setProperty('voice', voice.id)
                female_voice_found = True
                break
        if not female_voice_found and len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
            print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Female voice not explicitly found or set. Falling back to second available voice.")
        elif not female_voice_found:
             print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] No female voices found or only one voice. Using system default.")

    else: # Default or invalid setting
        if len(voices) > 0:
            engine.setProperty('voice', voices[0].id)
            print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Using default voice: {voices[0].name}")
        else:
            print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] No voices found. Using system default.")

except IndexError:
    print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Not enough voices found to set specific gender. Using default system voice.")
except Exception as e:
    print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Error setting voice: {e}. Using default system voice.")

engine.setProperty('rate', GLOBAL_CONFIG["SPEECH_RATE"]) # Set speech rate


# --- Configure Gemini API ---
gemini_model = None
if GLOBAL_CONFIG["GEMINI_API_KEY"] and GLOBAL_CONFIG["GEMINI_API_KEY"] != "YOUR_GEMINI_API_KEY":
    try:
        genai.configure(api_key=GLOBAL_CONFIG["GEMINI_API_KEY"])
        
        chosen_model_name = GLOBAL_CONFIG["GEMINI_MODEL_NAME"]
        available_models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        
        if chosen_model_name in available_models:
            gemini_model = genai.GenerativeModel(chosen_model_name)
        elif f"models/{chosen_model_name}" in available_models:
            gemini_model = genai.GenerativeModel(f"models/{chosen_model_name}")
        else:
            print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Error: Configured Gemini model '{chosen_model_name}' not found or does not support 'generateContent'.")
            print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Available models supporting 'generateContent':", available_models)
            if available_models:
                fallback_model = available_models[0]
                speak(f"Falling back to model {fallback_model} for Gemini features.")
                gemini_model = genai.GenerativeModel(fallback_model)
                print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Successfully configured {GLOBAL_CONFIG['JARVIS_NAME']} with fallback model: {fallback_model}")
            else:
                print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] No Gemini models found supporting 'generateContent'. Gemini features will be unavailable.")

        if gemini_model:
            print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Gemini API configured successfully with model: {gemini_model.model_name}.")
        else:
            print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Gemini features will be unavailable.")

    except Exception as e:
        print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Error configuring Gemini API for {GLOBAL_CONFIG['JARVIS_NAME']}: {e}. Gemini features will be unavailable.")
else:
    print(f"[{GLOBAL_CONFIG['JARVIS_NAME']} Setup] Warning: GEMINI_API_KEY not found or is default for {GLOBAL_CONFIG['JARVIS_NAME']}. Gemini features will be unavailable.")


# --- Define the COMMANDS dictionary ---
COMMANDS = {
    # Assistant Commands
    "hello jarvis": {"type": "assistant_command", "target": "greet"},
    "how are you": {"type": "assistant_command", "target": "status"},
    "exit": {"type": "assistant_command", "target": "exit"},
    "quit": {"type": "assistant_command", "target": "exit"},
    "goodbye": {"type": "assistant_command", "target": "exit"},

    # URL Opening Commands
    "open google": {"type": "open_url", "target": "https://www.google.com", "feedback": "Google"},
    "open youtube": {"type": "open_url", "target": "https://www.youtube.com", "feedback": "YouTube"},
    "open github": {"type": "open_url", "target": "https://github.com", "feedback": "GitHub"},
    "open linkedin": {"type": "open_url", "target": "https://www.linkedin.com", "feedback": "LinkedIn"},

    # Application Opening Commands (Windows specific paths or common .exe names)
    "open chrome": {"type": "open_app", "target": "chrome.exe", "fallback_target_exe": "chrome", "feedback": "Chrome"},
    "open firefox": {"type": "open_app", "target": "firefox.exe", "fallback_target_exe": "firefox", "feedback": "Firefox"},
    "open edge": {"type": "open_app", "target": "msedge.exe", "fallback_target_exe": "msedge", "feedback": "Edge"},
    "open outlook": {"type": "open_app", "target": "OUTLOOK.EXE", "fallback_target_exe": "outlook", "feedback": "Outlook"},
    "open spotify": {"type": "open_app", "target": "Spotify.exe", "fallback_target_exe": "spotify", "feedback": "Spotify"},
    "open calculator": {"type": "open_app", "target": "Calculator.exe", "fallback_target_exe": "calc", "feedback": "Calculator"},
    "open notepad": {"type": "open_app", "target": "notepad.exe", "fallback_target_exe": "notepad", "feedback": "Notepad"},
    "open paint": {"type": "open_app", "target": "mspaint.exe", "fallback_target_exe": "mspaint", "feedback": "Paint"},
    "open word": {"type": "open_app", "target": "WINWORD.EXE", "fallback_target_exe": "winword", "feedback": "Microsoft Word"},
    "open excel": {"type": "open_app", "target": "EXCEL.EXE", "fallback_target_exe": "excel", "feedback": "Microsoft Excel"},
    "open powerpoint": {"type": "open_app", "target": "POWERPNT.EXE", "fallback_target_exe": "powerpnt", "feedback": "Microsoft PowerPoint"},
    "open vlc": {"type": "open_app", "target": "vlc.exe", "fallback_target_exe": "vlc", "feedback": "VLC Media Player"},
    "open discord": {"type": "open_app", "target": "Discord.exe", "fallback_target_exe": "discord", "feedback": "Discord"},
    "open vs code": {"type": "open_app", "target": "Code.exe", "fallback_target_exe": "code", "feedback": "VS Code"},

    # Application Closing Commands (Windows specific process names)
    "close chrome": {"type": "close_app", "target": "chrome.exe", "feedback": "Chrome"},
    "close firefox": {"type": "close_app", "target": "firefox.exe", "feedback": "Firefox"},
    "close edge": {"type": "close_app", "target": "msedge.exe", "feedback": "Edge"},
    "close outlook": {"type": "close_app", "target": "OUTLOOK.EXE", "feedback": "Outlook"},
    "close spotify": {"type": "close_app", "target": "Spotify.exe", "feedback": "Spotify"},
    "close calculator": {"type": "close_app", "target": "Calculator.exe", "feedback": "Calculator"},
    "close notepad": {"type": "close_app", "target": "notepad.exe", "feedback": "Notepad"},
    "close paint": {"type": "close_app", "target": "mspaint.exe", "feedback": "Paint"},
    "close word": {"type": "close_app", "target": "WINWORD.EXE", "feedback": "Microsoft Word"},
    "close excel": {"type": "close_app", "target": "EXCEL.EXE", "feedback": "Microsoft Excel"},
    "close powerpoint": {"type": "close_app", "target": "POWERPNT.EXE", "feedback": "Microsoft PowerPoint"},
    "close vlc": {"type": "close_app", "target": "vlc.exe", "feedback": "VLC Media Player"},
    "close discord": {"type": "close_app", "target": "Discord.exe", "feedback": "Discord"},
    "close vs code": {"type": "close_app", "target": "Code.exe", "feedback": "VS Code"},
    "close active window": {"type": "close_active_window", "feedback": "the active window"}, # New command

    # System Control Commands (Volume - now handled by set_cross_platform_volume)
    "set volume to": {"type": "volume_control", "action": "set"},
    "increase volume": {"type": "volume_control", "action": "increase"},
    "decrease volume": {"type": "volume_control", "action": "decrease"},
    "mute volume": {"type": "volume_control", "action": "mute"},
    "unmute volume": {"type": "volume_control", "action": "unmute"},

    # Information Queries
    "time": {"type": "info_query", "target": "time", "feedback": "current time"},
    "date": {"type": "info_query", "target": "date", "feedback": "today's date"},
    "day": {"type": "info_query", "target": "day", "feedback": "today's day"},
    "weather": {"type": "info_query", "target": "weather", "feedback": "weather information"},

    # Dynamic Search Commands
    "search google for": {"type": "dynamic_search", "engine": "google"},
    "search youtube for": {"type": "dynamic_search", "engine": "youtube"},
    "find on google": {"type": "dynamic_search", "engine": "google"},
    "find on youtube": {"type": "dynamic_search", "engine": "youtube"},
    "search github for": {"type": "dynamic_search", "engine": "github"},

    # Gemini AI Queries (general knowledge/chat)
    "what is": {"type": "gemini_query"},
    "who is": {"type": "gemini_query"},
    "tell me about": {"type": "gemini_query"},
    "ask gemini": {"type": "gemini_query"},
    "ask jarvis": {"type": "gemini_query"},
    "when is": {"type": "gemini_query"},
    "where is": {"type": "gemini_query"},
    "why is": {"type": "gemini_query"},
    "how to": {"type": "gemini_query"},
    "explain": {"type": "gemini_query"},

    # Memory Commands (JSON-based)
    "remember this": {"type": "memory_command", "action": "add"},
    "take a note": {"type": "memory_command", "action": "add"},
    "store this": {"type": "memory_command", "action": "add"},
    "what do you remember": {"type": "memory_command", "action": "read_all"},
    "read my notes": {"type": "memory_command", "action": "read_all"},
    "show my notes": {"type": "memory_command", "action": "read_all"},
    "summarize my memories": {"type": "memory_command", "action": "summarize"},
    "forget note": {"type": "memory_command", "action": "delete"},
    "delete note": {"type": "memory_command", "action": "delete"},
    "clear all notes": {"type": "memory_command", "action": "clear_all"},
    "show notes in category": {"type": "memory_command", "action": "read_category"},
    "show me my notes": {"type": "memory_command", "action": "read_all"}, # More natural phrasing
    "list my memories": {"type": "memory_command", "action": "read_all"}, # More natural phrasing
    "what are my ideas": {"type": "memory_command", "action": "read_category", "category_hint": "idea"}, # Category hint
    "what are my tasks": {"type": "memory_command", "action": "read_category", "category_hint": "task"},
    "what is on my shopping list": {"type": "memory_command", "action": "read_category", "category_hint": "shopping list"},

    # Spotify Control Commands
    "play music": {"type": "spotify_control", "action": "play"},
    "resume music": {"type": "spotify_control", "action": "play"},
    "pause music": {"type": "spotify_control", "action": "pause"},
    "next song": {"type": "spotify_control", "action": "next"},
    "skip song": {"type": "spotify_control", "action": "next"},
    "previous song": {"type": "spotify_control", "action": "previous"},

    # --- Hotword Detection (Simulated) ---
    "hey jarvis": {"type": "hotword_trigger"}, # This is the hotword itself
    "start listening": {"type": "hotword_control", "action": "start"},
    "stop listening": {"type": "hotword_control", "action": "stop"},
    "enable hotword": {"type": "hotword_control", "action": "enable"},
    "disable hotword": {"type": "hotword_control", "action": "disable"},

    # Advanced NLP
    "analyze text": {"type": "nlp_control", "action": "analyze_text"},
    "what is the sentiment of this": {"type": "nlp_control", "action": "analyze_text"}, # New NLP command
    "summarize document": {"type": "nlp_control", "action": "summarize_document"},

    # Graphical User Interface (GUI) (Simulated)
    "open interface": {"type": "gui_control", "action": "open"},
    "show interface": {"type": "gui_control", "action": "open"},
    "close interface": {"type": "gui_control", "action": "close"},

    # Calendar/Reminder Integration (Functional with local JSON storage)
    "add reminder": {"type": "calendar_reminder", "action": "add_reminder"},
    "set reminder": {"type": "calendar_reminder", "action": "add_reminder"},
    "show reminders": {"type": "calendar_reminder", "action": "show_reminders"},
    "what are my appointments": {"type": "calendar_reminder", "action": "show_appointments"},
    "add event": {"type": "calendar_reminder", "action": "add_event"},
    "delete reminder": {"type": "calendar_reminder", "action": "delete_reminder"},
    "clear all reminders": {"type": "calendar_reminder", "action": "clear_all_reminders"},


    # Smart Home Integration (Simulated Philips Hue)
    "turn on lights": {"type": "smart_home_control", "action": "lights_on", "target": "all"},
    "turn off lights": {"type": "smart_home_control", "action": "lights_off", "target": "all"},
    "turn on all lights": {"type": "smart_home_control", "action": "lights_on", "target": "all"},
    "turn off all lights": {"type": "smart_home_control", "action": "lights_off", "target": "all"},
    "set light brightness to": {"type": "smart_home_control", "action": "set_brightness"},
    "set light color to": {"type": "smart_home_control", "action": "set_color"},
    "what are the lights doing": {"type": "smart_home_control", "action": "get_light_status"},
    "turn on the": {"type": "smart_home_control", "action": "lights_on_specific"}, # Needs follow up for light name
    "turn off the": {"type": "smart_home_control", "action": "lights_off_specific"}, # Needs follow up for light name
    "set thermostat to": {"type": "smart_home_control", "action": "set_thermostat"},
    "lock doors": {"type": "smart_home_control", "action": "lock_doors"},
    "unlock doors": {"type": "smart_home_control", "action": "unlock_doors"},

    # Music Playback Control (General - now includes basic local file playback)
    "play local music": {"type": "general_music_control", "action": "play_local"},
    "open music player": {"type": "general_music_control", "action": "open_player"},
    "play song": {"type": "general_music_control", "action": "play_specific"}, # Needs a follow-up for song name
    "stop music": {"type": "general_music_control", "action": "stop_playback"}, # Basic stop for playsound
}

# --- Speech Functions ---
def speak(text):
    """Converts text to speech using the initialized engine."""
    print(f"[{GLOBAL_CONFIG['JARVIS_NAME']}]: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Speech Error] Could not synthesize speech: {e}")

def listen_command(prompt="Listening...", timeout_seconds=5, phrase_time_limit_seconds=5):
    """Listens for a command from the microphone."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(prompt)
        r.pause_threshold = 0.8
        r.energy_threshold = 4000 # Adjust this value if it's too sensitive or not sensitive enough
        r.dynamic_energy_threshold = True
        try:
            audio = r.listen(source, timeout=timeout_seconds, phrase_time_limit=phrase_time_limit_seconds)
        except sr.WaitTimeoutError:
            print("[Speech Recognition] No speech detected within timeout.")
            return ""
        except Exception as e:
            print(f"[Microphone Error] An error occurred with the microphone: {e}")
            speak(f"I encountered an issue with your microphone. Please check its connection.")
            return ""

    try:
        command = r.recognize_google(audio, language='en-in').lower()
        print(f"[You Said]: {command}")
        return command
    except sr.UnknownValueError:
        print("[Speech Recognition] Sorry, I could not understand the audio.")
        # speak("Sorry, I couldn't understand that. Could you please repeat?") # Too frequent, remove for fluency
        return ""
    except sr.RequestError as e:
        print(f"[Speech Recognition] Could not request results from Google Speech Recognition service; {e}")
        speak(f"I'm sorry, I cannot connect to the speech recognition service at the moment. Please check your internet connection.")
        return ""

def listen_for_hotword(hotword_phrase, timeout_seconds=3, phrase_time_limit_seconds=2):
    """
    Listens specifically for the hotword.
    Returns True if hotword is detected, False otherwise.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"Listening for hotword '{hotword_phrase}'...")
        r.pause_threshold = 0.5 # Shorter pause for hotword
        r.energy_threshold = 3000 # Slightly less sensitive for hotword
        r.dynamic_energy_threshold = True
        try:
            audio = r.listen(source, timeout=timeout_seconds, phrase_time_limit=phrase_time_limit_seconds)
        except sr.WaitTimeoutError:
            return False # No speech detected
        except Exception as e:
            print(f"[Microphone Error] An error occurred with the microphone during hotword detection: {e}")
            return False

    try:
        recognized_phrase = r.recognize_google(audio, language='en-in').lower()
        print(f"[Hotword Listener] Heard: '{recognized_phrase}'")
        if hotword_phrase in recognized_phrase: # Use 'in' for flexibility
            return True
        return False
    except sr.UnknownValueError:
        return False # Did not understand speech
    except sr.RequestError as e:
        print(f"[Speech Recognition] Could not request results from Google Speech Recognition service during hotword detection; {e}")
        return False


def find_best_command(user_input):
    """
    Finds the best fuzzy match for the user's input against predefined commands.
    Returns the matched command key if confidence is above a threshold, otherwise None.
    """
    command_phrases = list(COMMANDS.keys())
    best_match, score = process.extractOne(user_input, command_phrases)

    if score > GLOBAL_CONFIG["FUZZY_MATCH_THRESHOLD"]:
        print(f"[Command Recognition] Best fuzzy match for '{user_input}': '{best_match}' with score {score}")
        return best_match
    else:
        print(f"[Command Recognition] No strong command match found for '{user_input}' (score: {score}). Threshold: {GLOBAL_CONFIG['FUZZY_MATCH_THRESHOLD']}")
        return None

# --- Core Action Functions ---
def open_url(url, feedback_name):
    """Opens a URL in the default web browser."""
    try:
        speak(f"Opening {feedback_name} for you.")
        webbrowser.open(url)
        print(f"[Action] Successfully opened URL: {url}")
    except webbrowser.Error as e:
        speak(f"I'm sorry, I couldn't open {feedback_name}. Your default web browser might not be configured correctly.")
        print(f"[Error] Webbrowser error opening {url}: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred while trying to open {feedback_name}.")
        print(f"[Error] Unexpected error opening {url}: {e}")

def open_application(app_target, feedback_name, fallback_exe=None):
    """
    Opens an application. Tries direct execution, then common system commands.
    `app_target` can be an exact process name (e.g., "chrome.exe") or a full path.
    `fallback_exe` is a common alias for `start` command.
    """
    speak(f"Opening {feedback_name}...")
    try:
        if platform.system() == "Windows":
            subprocess.Popen(app_target, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        else: # For Linux/macOS, direct subprocess.Popen is usually fine
            subprocess.Popen([app_target])
        print(f"[Action] Successfully started: {app_target}")
        speak(f"{feedback_name} opened.")
    except FileNotFoundError:
        print(f"[Error] Application '{app_target}' not found directly.")
        if fallback_exe:
            try:
                speak(f"Trying to open {feedback_name} using a common system command.")
                if platform.system() == "Windows":
                    subprocess.Popen(['start', fallback_exe], shell=True, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
                elif platform.system() == "Linux":
                    subprocess.Popen(['xdg-open', fallback_exe])
                elif platform.system() == "Darwin": # macOS
                    subprocess.Popen(['open', '-a', fallback_exe])
                print(f"[Action] Attempted to start '{fallback_exe}' via system command.")
                speak(f"{feedback_name} opened.")
            except Exception as e:
                speak(f"I'm sorry, I couldn't open {feedback_name}. Error: {e}")
                print(f"[Error] Failed to open {feedback_name} via fallback: {e}")
        else:
            speak(f"I'm sorry, I couldn't find {feedback_name} to open and there's no fallback option.")
            print(f"[Error] No fallback provided for {app_target}.")
    except Exception as e:
        speak(f"An unexpected error occurred while {GLOBAL_CONFIG['JARVIS_NAME']} was trying to open {feedback_name}.")
        print(f"[Error] Unexpected error opening {app_target}: {e}")


def close_application(process_name_to_close, feedback_name):
    """
    Closes applications more robustly on Windows by first sending a WM_CLOSE message
    for graphical applications, then by terminating/killing processes.
    """
    if platform.system() != "Windows":
        speak("This close command is optimized for Windows and may not work as expected on this operating system.")
        print("[Info] Note: close_application is primarily for Windows.")
        found_and_attempted = False
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'].lower() == process_name_to_close.lower():
                    speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} is attempting to terminate {feedback_name} (PID: {proc.pid}).")
                    proc.terminate()
                    proc.wait(timeout=3)
                    if proc.is_running():
                        proc.kill()
                    found_and_attempted = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"[Error] Access or process error during close attempt for {process_name_to_close}: {e}")
                pass # Continue searching
        if found_and_attempted:
            speak(f"{feedback_name} close attempt completed by {GLOBAL_CONFIG['JARVIS_NAME']}.")
        else:
            speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} could not find any running instances of {feedback_name} to close.")
        return

    speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} is attempting to close {feedback_name}...")
    closed_any = False
    process_name_to_close_lower = process_name_to_close.lower()
    
    if WINDOWS_GUI_AVAILABLE:
        def enum_windows_callback(hwnd, extra):
            try:
                pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                proc_info = psutil.Process(pid)
                if proc_info.name().lower() == process_name_to_close_lower:
                    if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                        print(f"[Action] Found window for {proc_info.name()} (PID: {pid}). Sending WM_CLOSE.")
                        win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                        nonlocal closed_any
                        closed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"[Error] Window enumeration error: {e}")
                pass

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            print(f"[Error] Error during EnumWindows call: {e}")
            speak(f"An error occurred while {GLOBAL_CONFIG['JARVIS_NAME']} was trying to find windows to close.")

        if closed_any:
            time.sleep(2) # Give some time for graceful close

    still_running_pids = []
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if proc.info['name'].lower() == process_name_to_close_lower:
                if proc.is_running():
                    still_running_pids.append(proc.info['pid'])
                    
                    speak(f"Found {proc.info['name']} (PID: {proc.pid}). {GLOBAL_CONFIG['JARVIS_NAME']} is attempting graceful termination...")
                    proc.terminate()
                    proc.wait(timeout=3)
                    
                    if proc.is_running():
                        proc.kill()
                    
                    closed_any = True

        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            speak(f"Access denied to close {proc.info['name']}. Please try running {GLOBAL_CONFIG['JARVIS_NAME']} as administrator for this command.")
            print(f"[Error] AccessDenied: Could not terminate process {proc.info['name']} (PID: {proc.pid}).")
            closed_any = True
            continue
        except Exception as e:
            print(f"[Error] Error while {GLOBAL_CONFIG['JARVIS_NAME']} was trying to close {proc.info['name']} (PID: {proc.pid}): {e}")
            continue

    if closed_any:
        speak(f"{feedback_name} close attempt completed by {GLOBAL_CONFIG['JARVIS_NAME']}.")
        final_check_running = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == process_name_to_close_lower:
                final_check_running = True
                break
        
        if final_check_running:
            speak(f"Some instances of {feedback_name} might still be running.")
            print(f"[Info] Some instances of {process_name_to_close} might still be running.")
        else:
            speak(f"{feedback_name} closed successfully.")
            print(f"[Action] Successfully closed: {process_name_to_close}")
    else:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} could not find any running instances of {feedback_name} to close, or it's a non-closable system process.")
        print(f"[Info] No running instances found or not closable for: {process_name_to_close}")

def close_active_window():
    """Closes the currently active window on Windows."""
    if not WINDOWS_GUI_AVAILABLE:
        speak("This command is only available on Windows with 'pywin32' installed.")
        print("[Info] close_active_window is Windows-specific and requires pywin32.")
        return

    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            window_title = win32gui.GetWindowText(hwnd)
            speak(f"Attempting to close '{window_title}'.")
            win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            speak("Active window closed.")
            print(f"[Action] Active window '{window_title}' closed.")
        else:
            speak("No active window found to close.")
            print("[Info] No active window found.")
    except Exception as e:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} could not close the active window. Error: {e}")
        print(f"[Error] Error closing active window: {e}")

def set_system_volume_windows(level=None, change_by=None, mute=False, unmute=False):
    """Controls system volume (Windows only using pycaw)."""
    if not PYCAW_AVAILABLE:
        speak("I'm sorry, Windows volume control via pycaw is not available.")
        print("[Info] Windows volume control unavailable: pycaw not installed.")
        return False # Indicate failure

    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        if mute:
            if volume.GetMute() == 0:
                volume.SetMute(1, None)
                speak("Volume muted.")
                print("[Action] Volume muted.")
            else:
                speak("Volume is already muted.")
        elif unmute:
            if volume.GetMute() == 1:
                volume.SetMute(0, None)
                speak("Volume unmuted.")
                print("[Action] Volume unmuted.")
            else:
                speak("Volume is not muted.")
        elif level is not None:
            scalar_level = max(0.0, min(1.0, float(level) / 100.0))
            volume.SetMasterVolumeLevelScalar(scalar_level, None)
            speak(f"Volume set to {int(scalar_level * 100)} percent.")
            print(f"[Action] Volume set to {int(scalar_level * 100)}%.")
        elif change_by is not None:
            current_scalar_volume = volume.GetMasterVolumeLevelScalar()
            new_scalar_volume = current_scalar_volume + (float(change_by) / 100.0)
            new_scalar_volume = max(0.0, min(1.0, new_scalar_volume))
            volume.SetMasterVolumeLevelScalar(new_scalar_volume, None)
            speak(f"Volume adjusted. Current volume is now {int(new_scalar_volume * 100)} percent.")
            print(f"[Action] Volume changed by {change_by}%. Current: {int(new_scalar_volume * 100)}%.")
        return True # Indicate success
    except Exception as e:
        speak(f"I encountered an error trying to control the volume on Windows. Error: {e}")
        print(f"[Error] Windows volume control error: {e}")
        return False # Indicate failure

# --- Cross-Platform Volume Control (Enhanced Implementation) ---
def set_cross_platform_volume(level=None, change_by=None, mute=False, unmute=False):
    """
    Controls system volume across platforms (Windows, macOS, Linux).
    """
    current_os = platform.system()
    try:
        if current_os == "Windows":
            # Delegate to existing Windows-specific pycaw function
            if set_system_volume_windows(level=level, change_by=change_by, mute=mute, unmute=unmute):
                return # If Windows specific function handled it, we are done
            else:
                # If pycaw failed, try generic method (less reliable)
                print("[Info] pycaw failed or not available, attempting generic Windows volume control.")
                if level is not None:
                    # Use nircmd or similar if available, or simulate key presses
                    # This is a very basic fallback and might not work everywhere
                    try:
                        # nircmd needs to be in system PATH or full path provided
                        subprocess.run(['nircmd', 'setsysvolume', str(int(level * 655.35))]) # 0-65535 range
                        speak(f"Volume set to {level} percent using generic method.")
                        print(f"[Action] Generic Windows volume set to {level}%.")
                        return
                    except FileNotFoundError:
                        print("[Error] nircmd not found. Generic Windows volume control failed.")
                    except Exception as e:
                        print(f"[Error] Generic Windows volume control error: {e}")
                speak("Windows volume control failed. Please check pycaw installation or try manually.")
                return

        elif current_os == "Darwin": # macOS
            if mute:
                subprocess.run(['osascript', '-e', 'set volume with output muted'])
                speak("Volume muted on macOS.")
            elif unmute:
                subprocess.run(['osascript', '-e', 'set volume without output muted'])
                speak("Volume unmuted on macOS.")
            elif level is not None:
                # macOS volume is 0-100, so direct mapping is fine
                subprocess.run(['osascript', '-e', f'set volume output volume {level}'])
                speak(f"Volume set to {level} percent on macOS.")
            elif change_by is not None:
                # To implement relative change, you need to get the current volume first.
                # This is a conceptual implementation of getting current volume and setting.
                try:
                    result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], capture_output=True, text=True, check=True)
                    current_volume = int(result.stdout.strip())
                    new_volume = max(0, min(100, current_volume + change_by))
                    subprocess.run(['osascript', '-e', f'set volume output volume {new_volume}'], check=True)
                    speak(f"Volume adjusted by {change_by} percent on macOS. Current volume is now {new_volume} percent.")
                    print(f"[Action] macOS volume changed by {change_by}%. Current: {new_volume}%.")
                except FileNotFoundError:
                    speak("osascript command not found. Cannot adjust volume on macOS.")
                    print("[Error] osascript not found for macOS volume control.")
                except subprocess.CalledProcessError as e:
                    speak(f"Error adjusting volume on macOS: {e}. Check permissions or system settings.")
                    print(f"[Error] osascript error: {e}")
                except ValueError:
                    speak("Could not parse current volume on macOS. Please try setting a specific level.")
                    print("[Error] Could not parse macOS volume output.")
            print(f"[Action] macOS volume control attempted.")

        elif current_os == "Linux":
            # Assumes PulseAudio is in use (most common modern Linux setup)
            # For ALSA directly, 'amixer set Master 50%' might work without '-D pulse'
            if mute:
                subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '1'])
                speak("Volume muted on Linux.")
            elif unmute:
                subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '0'])
                speak("Volume unmuted on Linux.")
            elif level is not None:
                subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{level}%'])
                speak(f"Volume set to {level} percent on Linux.")
            elif change_by is not None:
                # To implement relative change, you need to get the current volume first.
                # This is a conceptual implementation of getting current volume and setting.
                try:
                    result = subprocess.run(['pactl', 'get-sink-volume', '@DEFAULT_SINK@'], capture_output=True, text=True, check=True)
                    output_lines = result.stdout.splitlines()
                    current_volume_line = [line for line in output_lines if "Volume:" in line and "%" in line]
                    if current_volume_line:
                        current_volume_str = current_volume_line[0].split('/')[-2].strip().replace('%', '')
                        current_volume = int(current_volume_str)
                        new_volume = max(0, min(100, current_volume + change_by))
                        subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{new_volume}%'], check=True)
                        speak(f"Volume adjusted by {change_by} percent on Linux. Current volume is now {new_volume} percent.")
                        print(f"[Action] Linux volume changed by {change_by}%. Current: {new_volume}%.")
                    else:
                        speak("Could not parse current volume on Linux. Please try setting a specific level.")
                        print("[Error] Could not parse Linux volume output.")
                except FileNotFoundError:
                    speak("pactl command not found. Cannot adjust volume on Linux.")
                    print("[Error] pactl not found for Linux volume control.")
                except subprocess.CalledProcessError as e:
                    speak(f"Error adjusting volume on Linux: {e}. Check permissions or system settings.")
                    print(f"[Error] pactl error: {e}")
                except ValueError:
                    speak("Could not parse current volume on Linux. Please try setting a specific level.")
                    print("[Error] Could not parse Linux volume output.")
            print(f"[Action] Linux volume control attempted.")
        else:
            speak(f"Cross-platform volume control is not implemented for your operating system ({current_os}).")
            print(f"[Info] Unsupported OS for cross-platform volume: {current_os}")

    except FileNotFoundError:
        speak(f"System command for volume control not found on {current_os}. Please ensure necessary audio utilities are installed (e.g., 'osascript' on macOS, 'pactl' or 'amixer' on Linux).")
        print(f"[Error] Volume control command not found for {current_os}.")
    except Exception as e:
        speak(f"An error occurred during cross-platform volume control: {e}.")
        print(f"[Error] Cross-platform volume control error: {e}")


def get_weather(city_name):
    """Fetches and speaks the current weather for the given city."""
    api_key = GLOBAL_CONFIG["OPENWEATHERMAP_API_KEY"]
    if not api_key or api_key == "YOUR_OPENWEATHERMAP_API_KEY":
        speak(f"My OpenWeatherMap API key is not configured. {GLOBAL_CONFIG['JARVIS_NAME']} cannot fetch weather information.")
        print("[Config Error] OpenWeatherMap API key not set.")
        return

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city_name}&appid={api_key}&units=metric"
    try:
        response = requests.get(complete_url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data["cod"] == 200:
            main_data = data["main"]
            weather_data = data["weather"][0]
            temperature = main_data["temp"]
            humidity = main_data["humidity"]
            description = weather_data["description"]
            
            speak(f"The weather in {city_name} is currently {description}, with a temperature of {temperature:.1f} degrees Celsius and humidity of {humidity} percent.")
            print(f"[Action] Weather fetched for {city_name}: {description}, {temperature}°C, {humidity}% humidity.")
        else:
            speak(f"Sorry, {GLOBAL_CONFIG['JARVIS_NAME']} could not retrieve weather information for {city_name} at this time.")
            print(f"[API Error] OpenWeatherMap API error for {city_name}: {data.get('message', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        speak(f"I cannot connect to the internet to get weather information. Please check your connection.")
        print("[Network Error] No internet connection for OpenWeatherMap.")
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            speak(f"It seems my OpenWeatherMap API key is invalid. Please check its configuration.")
            print(f"[API Error] OpenWeatherMap API key invalid (401 error).")
        elif http_err.response.status_code == 404:
            speak(f"Sorry, {GLOBAL_CONFIG['JARVIS_NAME']} could not find weather information for {city_name}. Please check the city name.")
            print(f"[API Error] City not found (404 error) for {city_name}.")
        else:
            speak(f"An HTTP error occurred while fetching weather information: {http_err}.")
            print(f"[API Error] HTTP error fetching weather: {http_err}")
    except requests.exceptions.RequestException as req_err:
        speak(f"A general request error occurred while trying to get weather information: {req_err}.")
        print(f"[Network Error] General request error for OpenWeatherMap: {req_err}")
    except json.JSONDecodeError:
        speak(f"I received an unreadable response from the weather service.")
        print(f"[JSON Error] Could not decode JSON from OpenWeatherMap.")
    except Exception as e:
        speak(f"An unexpected error occurred while {GLOBAL_CONFIG['JARVIS_NAME']} was fetching weather information: {e}.")
        print(f"[Error] Weather fetching unexpected error: {e}")

def ask_gemini(query):
    """Sends a query to the Gemini model and speaks the response."""
    if not gemini_model:
        speak(f"I cannot connect to the Gemini AI. My API key is not configured or an error occurred during setup.")
        print("[Config Error] Gemini model not initialized.")
        return

    speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} is thinking...")
    try:
        response = gemini_model.generate_content(query)
        gemini_text_response = response.text
        speak(gemini_text_response)
        print(f"[Gemini Response] Query: '{query}' -> Response: '{gemini_text_response}'")
    except Exception as e:
        speak(f"I'm sorry, {GLOBAL_CONFIG['JARVIS_NAME']} encountered an error trying to process your request with Gemini.")
        print(f"[Gemini API Error] {e}")
        if "Blocked" in str(e):
            speak("My response was blocked due to safety concerns. Please try a different query.")
        elif "quota" in str(e).lower():
            speak("I've reached my usage limit for the Gemini API. Please try again later.")
        elif "API key" in str(e):
            speak("There's an issue with my Gemini API key. Please check its configuration.")
        elif "empty" in str(e).lower() or "no candidates" in str(e).lower():
            speak("I received an empty response from Gemini. It might not have an answer for that, or the request was too complex.")
        elif "404" in str(e) and "models/" in str(e):
            speak("The specific Gemini model I was trying to use is not available or supported. Please check the model name in the configuration.")
        else:
            speak("A general error occurred with the Gemini API. Please check your internet connection or the API status.")


def perform_dynamic_search(user_command_raw, search_engine_type):
    """Performs a dynamic search on Google, YouTube, or GitHub."""
    try:
        command_phrase_end = ""
        # Prioritize exact command phrases for parsing
        if f" {search_engine_type} for" in user_command_raw:
            command_phrase_end = f" {search_engine_type} for"
        elif f" on {search_engine_type}" in user_command_raw:
            command_phrase_end = f" on {search_engine_type}"
        # Specific check for "search github for"
        elif search_engine_type == "github" and user_command_raw.startswith("search github for"):
            command_phrase_end = "search github for"
        
        command_end_index = user_command_raw.find(command_phrase_end)

        if command_end_index != -1:
            query = user_command_raw[command_end_index + len(command_phrase_end):].strip()
        else:
            # Fallback for less precise commands, though fuzzy matching should help
            # Try to remove the matched command part from the start
            temp_command_phrase = " ".join(matched_command_key.split()[:-1]) # e.g., "search google"
            if user_command_raw.startswith(temp_command_phrase):
                query = user_command_raw[len(temp_command_phrase):].strip()
            else:
                query = user_command_raw.replace("search", "").replace("find", "").replace(search_engine_type, "").replace("on", "").replace("for", "").strip()


    except Exception as e:
        print(f"[Parsing Error] Error extracting search query: {e}")
        query = user_command_raw.replace("search", "").replace("find", "").replace(search_engine_type, "").replace("on", "").replace("for", "").strip()

    if not query:
        speak(f"What exactly do you want {GLOBAL_CONFIG['JARVIS_NAME']} to search on {search_engine_type}?")
        follow_up_query = listen_command(prompt=f"Listening for your {search_engine_type} query...")
        if follow_up_query:
            query = follow_up_query
        else:
            speak(f"No search query provided. {GLOBAL_CONFIG['JARVIS_NAME']} is aborting search.")
            print(f"[Info] Search aborted: no query provided for {search_engine_type}.")
            return

    try:
        if search_engine_type == "google":
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            speak(f"Searching Google for {query}.")
        elif search_engine_type == "youtube":
            search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}" # Corrected YouTube URL
            speak(f"Searching YouTube for {query}.")
        elif search_engine_type == "github":
            search_url = f"https://github.com/search?q={requests.utils.quote(query)}"
            speak(f"Searching GitHub for {query}.")
        else:
            speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} can only search on Google, YouTube, or GitHub at the moment.")
            print(f"[Info] Unsupported search engine requested: {search_engine_type}.")
            return

        webbrowser.open(search_url)
        print(f"[Action] Opened search URL: {search_url}")
    except webbrowser.Error as e:
        speak(f"I'm sorry, I couldn't open the search page. Your default web browser might be an issue.")
        print(f"[Error] Webbrowser error during search for '{query}' on {search_engine_type}: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred during the search operation.")
        print(f"[Error] Unexpected error during search for '{query}' on {search_engine_type}: {e}")

# --- JSON Memory Functions ---
def load_memory_data():
    """Loads memory data from the JSON file."""
    memory_file = GLOBAL_CONFIG["MEMORY_FILE"]
    if not os.path.exists(memory_file) or os.stat(memory_file).st_size == 0:
        print(f"[Memory] Memory file '{memory_file}' not found or empty. Initializing empty memory.")
        return []
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"[Memory] Memory loaded successfully from '{memory_file}'.")
            return data
    except json.JSONDecodeError:
        print(f"[Memory Error] Warning: {GLOBAL_CONFIG['JARVIS_NAME']} detected corrupted or empty JSON in memory file. Starting with empty memory.")
        speak(f"My memory file seems corrupted. I'm starting with a fresh memory. Apologies for the inconvenience.")
        return []
    except Exception as e:
        print(f"[Memory Error] Error loading memory data for {GLOBAL_CONFIG['JARVIS_NAME']}: {e}")
        speak(f"An error occurred while loading my memories. Some data might be inaccessible.")
        return []

def save_memory_data(data):
    """Saves memory data to the JSON file."""
    memory_file = GLOBAL_CONFIG["MEMORY_FILE"]
    try:
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"[Memory] Memory saved successfully to '{memory_file}'.")
    except Exception as e:
        speak(f"Sorry, {GLOBAL_CONFIG['JARVIS_NAME']} could not save the memory data due to an error.")
        print(f"[Memory Error] Error saving memory data: {e}")

def add_to_memory(note, category=None):
    """Adds a timestamped and categorized note to the memory file."""
    memory_data = load_memory_data()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate a unique ID (simple increment for now)
    new_id = 1
    if memory_data:
        # Ensure 'id' exists and is numeric for max()
        existing_ids = [item.get("id", 0) for item in memory_data if isinstance(item.get("id"), int)]
        if existing_ids:
            new_id = max(existing_ids) + 1

    if not category:
        speak(f"What category does this note belong to? For example: idea, task, shopping list, or personal.")
        spoken_category = listen_command(prompt=f"Listening for category...")
        if spoken_category:
            category = spoken_category.lower().strip()
        else:
            speak(f"No category provided. {GLOBAL_CONFIG['JARVIS_NAME']} will save it as 'uncategorized'.")
            category = "uncategorized"

    new_entry = {
        "id": new_id,
        "timestamp": timestamp,
        "note": note,
        "category": category
    }
    memory_data.append(new_entry)
    save_memory_data(memory_data)
    speak(f"Understood. {GLOBAL_CONFIG['JARVIS_NAME']} has remembered that as a '{category}' note with ID {new_id}.")
    print(f"[Memory Action] Added to memory (ID {new_id}, Category '{category}'): {note}")

def read_memory(category=None, summarize=False):
    """Reads and speaks the contents of the memory file, optionally by category or summarized."""
    memory_data = load_memory_data()

    if not memory_data:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} doesn't have anything in memory yet.")
        print("[Memory Action] No memory entries to read.")
        return

    filtered_notes = []
    if category:
        for entry in memory_data:
            if entry.get("category", "uncategorized").lower() == category.lower():
                filtered_notes.append(entry)
        
        if not filtered_notes:
            speak(f"I found no notes in the '{category}' category.")
            print(f"[Memory Action] No notes found in category '{category}'.")
            return
        speak(f"Here are your notes in the '{category}' category:")
        print(f"[Memory Action] Reading notes in category: '{category}'.")
    else:
        speak(f"Here is everything {GLOBAL_CONFIG['JARVIS_NAME']} has in memory:")
        filtered_notes = memory_data
        print("[Memory Action] Reading all memory entries.")

    notes_text_for_display = ""
    for entry in filtered_notes:
        notes_text_for_display += f"ID: {entry.get('id', 'N/A')} | [{entry['timestamp']}] | Category: {entry.get('category', 'Uncategorized').capitalize()}\n"
        notes_text_for_display += f"  Note: {entry['note']}\n\n"

    print(f"\n--- {GLOBAL_CONFIG['JARVIS_NAME']}'s Memory ---")
    print(notes_text_for_display)
    print("----------------------------------\n")

    if summarize and gemini_model:
        if len(filtered_notes) > 1: # Only summarize if there's more than one relevant note
            speak(f"Since there are multiple entries, {GLOBAL_CONFIG['JARVIS_NAME']} will provide a summary for you.")
            prompt = f"Please summarize the following memory entries concisely, highlighting key information and actionable items. Present it as if you are a helpful AI assistant named {GLOBAL_CONFIG['JARVIS_NAME']}:\n\n{notes_text_for_display}"
            ask_gemini(prompt)
        else:
            speak(f"There is only one relevant entry. {GLOBAL_CONFIG['JARVIS_NAME']} will read it directly.")
            speak(f"Note: {filtered_notes[0]['note']}")
    elif len(notes_text_for_display) < 1000 and len(filtered_notes) < 5: # Adjust character/count limit for speaking all
        speak(f"Here are the notes: {notes_text_for_display.replace('ID:', 'ID').replace('Category:', 'Category')}") # Speak cleaner version
    else:
        speak(f"Your memory contains many entries. {GLOBAL_CONFIG['JARVIS_NAME']} has printed them to the console for your review.")
        print(f"[Info] Memory too long to speak, printed to console.")


def forget_note(note_identifier=None):
    """Deletes a specific note by ID or a keyword/phrase."""
    memory_data = load_memory_data()

    if not memory_data:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} has no notes to forget.")
        print("[Memory Action] No notes to delete.")
        return

    if not note_identifier:
        speak(f"Which note would you like {GLOBAL_CONFIG['JARVIS_NAME']} to forget? Please tell me the ID number or a keyword from the note.")
        note_identifier = listen_command(prompt="Listening for note ID or keyword...")
        if not note_identifier:
            speak(f"No identifier provided. {GLOBAL_CONFIG['JARVIS_NAME']} cannot forget a note without knowing which one.")
            print("[Memory Action] Delete aborted: no identifier provided.")
            return

    initial_memory_count = len(memory_data)
    updated_memory_data = []
    found_notes = []

    try:
        # Try to delete by ID first
        note_id = int(note_identifier)
        for entry in memory_data:
            if entry.get("id") == note_id:
                found_notes.append(entry)
            else:
                updated_memory_data.append(entry)
        
        if found_notes:
            save_memory_data(updated_memory_data)
            speak(f"Understood. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten note with ID {note_id}.")
            print(f"[Memory Action] Deleted note with ID {note_id}: {found_notes[0]['note']}")
            return

    except ValueError:
        # Not an ID, try to delete by keyword/phrase
        speak(f"Searching for notes containing '{note_identifier}' to forget.")
        
        matching_entries = []
        # Create a copy to safely iterate while building updated_memory_data
        temp_memory_data = list(memory_data) 
        
        for entry in temp_memory_data:
            # Use partial_ratio to find if the identifier is part of the note
            if process.extractOne(note_identifier, [entry['note']], scorer=process.fuzz.partial_ratio)[1] > 80: # Adjust threshold
                matching_entries.append(entry)
            else:
                updated_memory_data.append(entry) # Keep notes that don't match strongly

        if not matching_entries:
            speak(f"I found no notes strongly matching '{note_identifier}' to forget.")
            print(f"[Memory Action] No strong match found for '{note_identifier}'. No notes deleted.")
            updated_memory_data = memory_data # Restore original if no match
        elif len(matching_entries) == 1:
            # If only one strong match, delete it
            save_memory_data(updated_memory_data)
            speak(f"Understood. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten the note: '{matching_entries[0]['note']}'.")
            print(f"[Memory Action] Deleted note by keyword: {matching_entries[0]['note']}")
        else:
            # Multiple matches, ask for clarification
            speak(f"I found multiple notes containing '{note_identifier}'. Please clarify which one you'd like {GLOBAL_CONFIG['JARVIS_NAME']} to forget by saying its ID:")
            for i, entry in enumerate(matching_entries):
                speak(f"Note {i+1}: ID {entry.get('id', 'N/A')}, '{entry['note']}'")
            
            clarification = listen_command(prompt="Listening for ID to delete...")
            try:
                clarification_id = int(clarification)
                final_updated_memory = []
                deleted_one = False
                for entry in memory_data: # Iterate original data to ensure correct deletion
                    if entry.get("id") == clarification_id:
                        found_notes.append(entry) # Keep track of what was found/deleted
                        deleted_one = True
                    else:
                        final_updated_memory.append(entry)
                
                if deleted_one:
                    save_memory_data(final_updated_memory)
                    speak(f"Understood. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten note with ID {clarification_id}.")
                    print(f"[Memory Action] Deleted note with ID {clarification_id}: {found_notes[0]['note'] if found_notes else ''}")
                else:
                    speak(f"I could not find a note with ID {clarification_id}. No notes were deleted.")
                    print(f"[Memory Action] No note found with ID {clarification_id}. Reverting changes.")
                    save_memory_data(memory_data) # Revert if no deletion
            except ValueError:
                speak(f"That was not a valid ID. No notes were deleted.")
                print("[Memory Action] Invalid ID provided for deletion.")
                save_memory_data(memory_data) # Revert if no deletion
            except Exception as e:
                speak(f"An error occurred during deletion. {e}")
                print(f"[Memory Error] Error during multi-match deletion: {e}")
                save_memory_data(memory_data) # Revert if error

    if len(memory_data) == initial_memory_count and not found_notes: # Final check if anything was actually deleted
        speak(f"I could not find any notes matching '{note_identifier}' to forget.")
        print(f"[Memory Action] No notes deleted after full attempt for '{note_identifier}'.")


def clear_all_memory():
    """Clears all notes from the memory file after confirmation."""
    speak(f"Are you sure you want {GLOBAL_CONFIG['JARVIS_NAME']} to clear all your memories? This action cannot be undone.")
    confirmation = listen_command(prompt="Say 'yes' to confirm or 'no' to cancel.")
    if "yes" in confirmation:
        save_memory_data([]) # Save an empty list
        speak(f"All memories have been cleared. {GLOBAL_CONFIG['JARVIS_NAME']} has an empty slate.")
        print("[Memory Action] All memory cleared.")
    else:
        speak(f"Understood. {GLOBAL_CONFIG['JARVIS_NAME']} will keep your memories intact.")
        print("[Memory Action] Memory clear action cancelled.")

# --- Spotify Control Functions ---
sp = None # Global spotipy client instance

def authenticate_spotify():
    global sp
    if not SPOTIPY_AVAILABLE:
        speak("The 'spotipy' library is not installed, so Spotify control is unavailable.")
        print("[Config Error] 'spotipy' not available for Spotify authentication.")
        return False

    # Check if credentials are set (not default placeholders)
    if not all([
        GLOBAL_CONFIG.get("SPOTIFY_CLIENT_ID") and GLOBAL_CONFIG["SPOTIFY_CLIENT_ID"] != "YOUR_SPOTIFY_CLIENT_ID",
        GLOBAL_CONFIG.get("SPOTIFY_CLIENT_SECRET") and GLOBAL_CONFIG["SPOTIFY_CLIENT_SECRET"] != "YOUR_SPOTIFY_CLIENT_SECRET",
        GLOBAL_CONFIG.get("SPOTIFY_REDIRECT_URI") and GLOBAL_CONFIG["SPOTIFY_REDIRECT_URI"] != "http://localhost:8888/callback"
    ]):
        speak("Spotify API credentials are NOT fully configured. Please set them in the GLOBAL_CONFIG.")
        print("[Config Error] Spotify API credentials missing or are default placeholders.")
        return False

    try:
        scope = GLOBAL_CONFIG["SPOTIPY_SCOPE"] # Corrected to use SPOTIPY_SCOPE
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=GLOBAL_CONFIG["SPOTIFY_CLIENT_ID"],
            client_secret=GLOBAL_CONFIG["SPOTIFY_CLIENT_SECRET"],
            redirect_uri=GLOBAL_CONFIG["SPOTIFY_REDIRECT_URI"],
            scope=scope
        ))
        speak("Spotify authenticated successfully.")
        print("[Action] Spotify authenticated.")
        return True
    except Exception as e:
        speak(f"Failed to authenticate Spotify: {e}. Please check your credentials and internet connection.")
        print(f"[Spotify Error] Authentication failed: {e}")
        sp = None
        return False

def play_spotify_music():
    """Plays/resumes Spotify music."""
    if not sp:
        speak("Spotify is not authenticated. Please authenticate Spotify first.")
        if authenticate_spotify(): # Try to authenticate if not already
            play_spotify_music() # Retry after authentication
        return
    try:
        sp.start_playback()
        speak("Playing music on Spotify.")
        print("[Spotify Action] Play/Resume.")
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404 and "No active device found" in str(e):
            speak("No active Spotify device found. Please open Spotify on a device and play something first.")
        else:
            speak(f"Could not play music on Spotify: {e}. Ensure Spotify is running and you have an active device.")
        print(f"[Spotify Error] Playback failed: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred while trying to play Spotify music: {e}.")
        print(f"[Spotify Error] Unexpected error during play: {e}")


def pause_spotify_music():
    """Pauses Spotify music."""
    if not sp:
        speak("Spotify is not authenticated. Please authenticate Spotify first.")
        return
    try:
        sp.pause_playback()
        speak("Music paused on Spotify.")
        print("[Spotify Action] Pause.")
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404 and "No active device found" in str(e):
            speak("No active Spotify device found. Please open Spotify on a device and play something first.")
        else:
            speak(f"Could not pause music on Spotify: {e}. Ensure Spotify is running and you have an active device.")
        print(f"[Spotify Error] Pause failed: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred while trying to pause Spotify music: {e}.")
        print(f"[Spotify Error] Unexpected error during pause: {e}")

def next_spotify_song():
    """Skips to the next Spotify song."""
    if not sp:
        speak("Spotify is not authenticated. Please authenticate Spotify first.")
        return
    try:
        sp.next_track()
        speak("Skipping to the next song.")
        print("[Spotify Action] Next track.")
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404 and "No active device found" in str(e):
            speak("No active Spotify device found. Please open Spotify on a device and play something first.")
        else:
            speak(f"Could not skip song on Spotify: {e}. Ensure Spotify is running and you have an active device.")
        print(f"[Spotify Error] Next track failed: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred while trying to skip Spotify song: {e}.")
        print(f"[Spotify Error] Unexpected error during next track: {e}")

def previous_spotify_song():
    """Plays the previous Spotify song."""
    if not sp:
        speak("Spotify is not authenticated. Please authenticate Spotify first.")
        return
    try:
        sp.previous_track()
        speak("Playing the previous song.")
        print("[Spotify Action] Previous track.")
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404 and "No active device found" in str(e):
            speak("No active Spotify device found. Please open Spotify on a device and play something first.")
        else:
            speak(f"Could not play previous song on Spotify: {e}. Ensure Spotify is running and you have an active device.")
        print(f"[Spotify Error] Previous track failed: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred while trying to play previous Spotify song: {e}.")
        print(f"[Spotify Error] Unexpected error during previous track: {e}")

# --- Continuous Listening / Hotword Detection (Simulated) ---
hotword_enabled = False
hotword_detected_in_session = False # Flag to indicate if hotword was just detected in current session

def start_hotword_listening():
    global hotword_enabled, hotword_detected_in_session
    if hotword_enabled:
        speak("Hotword detection is already enabled.")
        return
    speak(f"Starting hotword detection. Say '{GLOBAL_CONFIG['HOTWORD']}' to activate me.")
    print(f"[Hotword] Hotword detection initiated. (Simulated - requires 'Porcupine' or 'PocketSphinx' for true always-on detection)")
    hotword_enabled = True
    hotword_detected_in_session = False # Reset on start

def stop_hotword_listening():
    global hotword_enabled, hotword_detected_in_session
    if not hotword_enabled:
        speak("Hotword detection is not currently enabled.")
        return
    speak("Stopping hotword detection. I will now listen for commands directly.")
    print("[Hotword] Hotword detection stopped.")
    hotword_enabled = False
    hotword_detected_in_session = False # Reset on stop

# --- Advanced Natural Language Processing (NLP) ---
sid = None # SentimentIntensityAnalyzer instance

def initialize_sentiment_analyzer():
    global sid
    if NLTK_AVAILABLE:
        try:
            # Attempt to download the VADER lexicon if not already present
            nltk.data.find('sentiment/vader_lexicon.zip')
        except nltk.downloader.DownloadError:
            speak("I need to download some data for sentiment analysis. Please wait a moment.")
            print("[NLTK] Downloading 'vader_lexicon' for sentiment analysis...")
            try:
                nltk.download('vader_lexicon')
                print("[NLTK] 'vader_lexicon' downloaded successfully.")
            except Exception as e:
                print(f"[NLTK Error] Failed to download 'vader_lexicon': {e}. Sentiment analysis will be unavailable.")
                speak("I couldn't download the necessary data for sentiment analysis. Please check your internet connection and try again.")
                return False
        sid = SentimentIntensityAnalyzer()
        print("[NLP] SentimentIntensityAnalyzer initialized.")
        return True
    return False

def analyze_sentiment(text):
    """Performs sentiment analysis on the given text."""
    if not NLTK_AVAILABLE or sid is None:
        speak("Sentiment analysis is not available. Please ensure NLTK is installed and the VADER lexicon is downloaded.")
        return

    try:
        scores = sid.polarity_scores(text)
        compound_score = scores['compound']

        if compound_score >= 0.05:
            sentiment = "positive"
        elif compound_score <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        speak(f"The sentiment of that text is {sentiment}. The compound score is {compound_score:.2f}.")
        print(f"[NLP Action] Sentiment analysis for '{text}': {sentiment} (Compound: {compound_score})")

    except Exception as e:
        speak(f"An error occurred during sentiment analysis: {e}")
        print(f"[NLP Error] Sentiment analysis failed: {e}")


def process_nlp_query(action_type, text_input=None):
    if action_type == "analyze_text":
        if not NLTK_AVAILABLE or sid is None:
            if not initialize_sentiment_analyzer():
                return # Stop if initialization failed
        
        speak("What text would you like me to analyze for sentiment?")
        text_to_analyze = listen_command("Listening for text...")
        if text_to_analyze:
            analyze_sentiment(text_to_analyze)
        else:
            speak("No text provided for analysis.")
    elif action_type == "summarize_document":
        speak("What document or text should I summarize?")
        document_text = listen_command("Listening for document/text...")
        if document_text:
            # This part still relies on Gemini for summarization as a more advanced NLP task
            if gemini_model:
                speak(f"Sending the document to Gemini for summarization.")
                prompt = f"Please summarize the following text concisely:\n\n{document_text}"
                ask_gemini(prompt)
            else:
                speak("I cannot summarize documents without the Gemini AI configured.")
                print("[NLP] Gemini model not available for summarization.")
        else:
            speak("No document or text provided for summarization.")
    else:
        speak("I'm not sure how to perform that NLP action.")


# --- Graphical User Interface (GUI) (Simulated) ---
gui_running = False
def launch_gui():
    global gui_running
    if gui_running:
        speak("The graphical interface is already open.")
        print("[GUI] GUI is already 'open'.")
        return
    
    speak("Opening the graphical interface for you.")
    print("[GUI] Simulating GUI launch. A visual interface would appear here in a real application.")
    gui_running = True
    speak("The graphical interface is now open.")
    # In a real application, you would initialize and show your Tkinter/PyQt/Kivy window here.
    # Example (Tkinter - conceptual, would block main loop):
    # import tkinter as tk
    # root = tk.Tk()
    # root.title("Jarvis GUI")
    # tk.Label(root, text="Welcome to Jarvis GUI!").pack()
    # root.mainloop()

def close_gui():
    global gui_running
    if not gui_running:
        speak("The graphical interface is not currently open.")
        print("[GUI] GUI is not 'open'.")
        return
    
    speak("Closing the graphical interface.")
    print("[GUI] Simulating GUI closure. A visual interface would close here in a real application.")
    gui_running = False
    speak("The graphical interface is now closed.")
    # In a real application, you would destroy your Tkinter/PyQt/Kivy window here.
    # Example (Tkinter - conceptual):
    # if 'root' in globals() and root.winfo_exists(): # Check if root window exists
    #     root.destroy()


# --- Calendar/Reminder Integration (Functional with local JSON storage) ---

def _load_calendar_data():
    """Loads calendar data from the JSON file."""
    calendar_file = GLOBAL_CONFIG["CALENDAR_FILE"]
    if not os.path.exists(calendar_file) or os.stat(calendar_file).st_size == 0:
        print(f"[Calendar] Calendar file '{calendar_file}' not found or empty. Initializing empty calendar.")
        return []
    try:
        with open(calendar_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Convert ISO strings back to datetime objects for easier manipulation
            for entry in data:
                entry['datetime'] = datetime.datetime.fromisoformat(entry['datetime'])
            print(f"[Calendar] Calendar loaded successfully from '{calendar_file}'.")
            return data
    except json.JSONDecodeError:
        print(f"[Calendar Error] Warning: {GLOBAL_CONFIG['JARVIS_NAME']} detected corrupted or empty JSON in calendar file. Starting with empty calendar.")
        speak(f"My calendar file seems corrupted. I'm starting with a fresh calendar. Apologies for the inconvenience.")
        return []
    except Exception as e:
        print(f"[Calendar Error] Error loading calendar data for {GLOBAL_CONFIG['JARVIS_NAME']}: {e}")
        speak(f"An error occurred while loading my calendar. Some data might be inaccessible.")
        return []

def _save_calendar_data(data):
    """Saves calendar data to the JSON file."""
    calendar_file = GLOBAL_CONFIG["CALENDAR_FILE"]
    try:
        # Convert datetime objects to ISO strings for JSON serialization
        serializable_data = []
        for entry in data:
            temp_entry = entry.copy()
            temp_entry['datetime'] = temp_entry['datetime'].isoformat()
            serializable_data.append(temp_entry)

        with open(calendar_file, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=4)
        print(f"[Calendar] Calendar saved successfully to '{calendar_file}'.")
    except Exception as e:
        speak(f"Sorry, {GLOBAL_CONFIG['JARVIS_NAME']} could not save the calendar data due to an error.")
        print(f"[Calendar Error] Error saving calendar data: {e}")

def _parse_datetime_from_speech(text):
    """
    A simplified parser for dates/times from speech.
    For robust parsing, use 'dateparser' library.
    """
    now = datetime.datetime.now()
    today = now.date()
    target_date = today
    target_time = None # Default to no specific time, or current time if only date is given

    text_lower = text.lower()

    # --- Date Parsing ---
    if "today" in text_lower:
        target_date = today
    elif "tomorrow" in text_lower:
        target_date = today + datetime.timedelta(days=1)
    elif "next monday" in text_lower:
        days_until_monday = (0 - today.weekday() + 7) % 7 # 0 is Monday
        if days_until_monday == 0: # If today is Monday, get next Monday
            days_until_monday = 7
        target_date = today + datetime.timedelta(days=days_until_monday)
    elif "next tuesday" in text_lower:
        days_until_tuesday = (1 - today.weekday() + 7) % 7
        if days_until_tuesday == 0: days_until_tuesday = 7
        target_date = today + datetime.timedelta(days=days_until_tuesday)
    elif "next wednesday" in text_lower:
        days_until_wednesday = (2 - today.weekday() + 7) % 7
        if days_until_wednesday == 0: days_until_wednesday = 7
        target_date = today + datetime.timedelta(days=days_until_wednesday)
    elif "next thursday" in text_lower:
        days_until_thursday = (3 - today.weekday() + 7) % 7
        if days_until_thursday == 0: days_until_thursday = 7
        target_date = today + datetime.timedelta(days=days_until_thursday)
    elif "next friday" in text_lower:
        days_until_friday = (4 - today.weekday() + 7) % 7
        if days_until_friday == 0: days_until_friday = 7
        target_date = today + datetime.timedelta(days=days_until_friday)
    elif "next saturday" in text_lower:
        days_until_saturday = (5 - today.weekday() + 7) % 7
        if days_until_saturday == 0: days_until_saturday = 7
        target_date = today + datetime.timedelta(days=days_until_saturday)
    elif "next sunday" in text_lower:
        days_until_sunday = (6 - today.weekday() + 7) % 7
        if days_until_sunday == 0: days_until_sunday = 7
        target_date = today + datetime.timedelta(days=days_until_sunday)
    
    # --- Time Parsing (basic) ---
    # Look for "at X (am/pm)"
    time_match = None
    for i in range(1, 13): # 1 to 12
        if f"at {i} am" in text_lower:
            time_match = (i, 0, "am")
            break
        if f"at {i} p m" in text_lower or f"at {i} pm" in text_lower:
            time_match = (i, 0, "pm")
            break
        if f"at {i} o'clock" in text_lower:
            time_match = (i, 0, "am") # Assume AM if not specified
            break
    
    # Handle specific minutes if present (e.g., "at 3:30 pm") - very basic
    if "at" in text_lower and ":" in text_lower:
        try:
            parts = text_lower.split("at")[1].strip().split(" ")
            time_part = parts[0]
            hour, minute = map(int, time_part.split(':'))
            ampm = ""
            if len(parts) > 1:
                ampm = parts[1]
            
            if "pm" in ampm and hour < 12:
                hour += 12
            elif "am" in ampm and hour == 12: # 12 AM is midnight
                hour = 0
            target_time = datetime.time(hour, minute)
        except ValueError:
            pass # Failed to parse time, proceed without specific time
    
    if time_match:
        hour, minute, ampm_str = time_match
        if ampm_str == "pm" and hour < 12:
            hour += 12
        elif ampm_str == "am" and hour == 12: # 12 AM is midnight
            hour = 0
        target_time = datetime.time(hour, minute)

    if target_time:
        return datetime.datetime.combine(target_date, target_time)
    else:
        # If only date is specified, use a default time (e.g., start of day)
        return datetime.datetime.combine(target_date, datetime.time(9, 0)) # Default to 9 AM

def manage_calendar_event(action_type):
    calendar_data = _load_calendar_data()

    if action_type == "add_reminder" or action_type == "add_event":
        speak("What is the reminder or event for?")
        event_text = listen_command("Listening for event text...")
        if not event_text:
            speak("No event text provided. Aborting.")
            return

        speak("When should I add this? For example, 'tomorrow at 3 PM', 'next Monday', or 'today'.")
        time_text = listen_command("Listening for date and time...")
        if not time_text:
            speak("No date or time provided. Aborting.")
            return

        parsed_datetime = _parse_datetime_from_speech(time_text)
        if not parsed_datetime:
            speak("I couldn't understand the date and time. Please try again with a clearer phrase.")
            print(f"[Calendar Error] Failed to parse datetime from: '{time_text}'")
            return

        new_id = 1
        if calendar_data:
            existing_ids = [item.get("id", 0) for item in calendar_data if isinstance(item.get("id"), int)]
            if existing_ids:
                new_id = max(existing_ids) + 1

        new_entry = {
            "id": new_id,
            "type": "reminder" if action_type == "add_reminder" else "event",
            "text": event_text,
            "datetime": parsed_datetime # Stored as datetime object, converted to ISO string on save
        }
        calendar_data.append(new_entry)
        _save_calendar_data(calendar_data)
        speak(f"Okay, I've added your {new_entry['type']} for '{event_text}' on {parsed_datetime.strftime('%A, %B %d at %I:%M %p')}.")
        print(f"[Calendar Action] Added {new_entry['type']} (ID {new_id}): '{event_text}' at {parsed_datetime}")

    elif action_type == "show_reminders" or action_type == "show_appointments":
        upcoming_events = sorted([
            e for e in calendar_data if e['datetime'] >= datetime.datetime.now()
        ], key=lambda x: x['datetime'])

        if not upcoming_events:
            speak("You have no upcoming reminders or appointments.")
            print("[Calendar Action] No upcoming events found.")
            return

        speak("Here are your upcoming reminders and appointments:")
        print("\n--- Upcoming Calendar Entries ---")
        for event in upcoming_events:
            event_time_str = event['datetime'].strftime('%A, %B %d at %I:%M %p')
            speak(f"ID {event['id']}: {event['text']} on {event_time_str}.")
            print(f"ID {event['id']} ({event['type'].capitalize()}): '{event['text']}' on {event_time_str}")
        print("-----------------------------------\n")

    elif action_type == "delete_reminder":
        speak("Which reminder or event would you like to delete? Please tell me the ID number.")
        id_text = listen_command("Listening for ID...")
        try:
            event_id_to_delete = int(id_text.strip())
            
            initial_count = len(calendar_data)
            calendar_data = [e for e in calendar_data if e.get('id') != event_id_to_delete]
            
            if len(calendar_data) < initial_count:
                _save_calendar_data(calendar_data)
                speak(f"Reminder or event with ID {event_id_to_delete} has been deleted.")
                print(f"[Calendar Action] Deleted event with ID: {event_id_to_delete}")
            else:
                speak(f"I could not find a reminder or event with ID {event_id_to_delete}.")
                print(f"[Calendar Info] No event found with ID: {event_id_to_delete}")
        except ValueError:
            speak("That was not a valid ID. Please provide a numeric ID.")
            print(f"[Calendar Error] Invalid ID provided for deletion: {id_text}")
        except Exception as e:
            speak(f"An error occurred while trying to delete the reminder: {e}")
            print(f"[Calendar Error] Error deleting reminder: {e}")

    elif action_type == "clear_all_reminders":
        speak(f"Are you sure you want {GLOBAL_CONFIG['JARVIS_NAME']} to clear all your reminders and events? This action cannot be undone.")
        confirmation = listen_command(prompt="Say 'yes' to confirm or 'no' to cancel.")
        if "yes" in confirmation:
            _save_calendar_data([]) # Save an empty list
            speak(f"All reminders and events have been cleared.")
            print("[Calendar Action] All calendar entries cleared.")
        else:
            speak(f"Understood. {GLOBAL_CONFIG['JARVIS_NAME']} will keep your reminders intact.")
            print("[Calendar Action] Calendar clear action cancelled.")

# --- Smart Home Integration (Simulated Philips Hue) ---
# This dictionary will simulate the state of your Hue lights
# In a real scenario, this would be fetched from the Hue Bridge API
SIMULATED_HUE_LIGHTS = {
    "1": {"name": "Living Room Lamp", "state": {"on": False, "bri": 128, "hue": 0, "sat": 0}},
    "2": {"name": "Kitchen Spotlight", "state": {"on": True, "bri": 200, "hue": 10000, "sat": 150}},
    "3": {"name": "Bedroom Light", "state": {"on": False, "bri": 254, "hue": 0, "sat": 0}},
}

def _hue_api_base_url():
    """Constructs the base URL for the Hue Bridge API."""
    ip = GLOBAL_CONFIG["HUE_BRIDGE_IP"]
    username = GLOBAL_CONFIG["HUE_USERNAME"]
    if ip == "YOUR_HUE_BRIDGE_IP" or username == "your_hue_username":
        speak("Hue Bridge IP or username is not configured. Please set them in GLOBAL_CONFIG.")
        print("[Hue Error] Hue Bridge IP or username not configured.")
        return None
    return f"http://{ip}/api/{username}"

def _hue_send_command(method, endpoint, data=None):
    """
    Simulates sending a command to the Hue Bridge API.
    In a real implementation, this would use `requests`.
    """
    base_url = _hue_api_base_url()
    if not base_url:
        return {"error": "Configuration missing"}
    
    url = f"{base_url}{endpoint}"
    print(f"[Hue Simulated API Call] {method} {url} with data: {data}")

    # Simulate success/failure and update SIMULATED_HUE_LIGHTS
    try:
        if "/lights" in endpoint and "/state" in endpoint:
            light_id = endpoint.split('/')[2] # e.g., /lights/1/state -> 1
            if light_id in SIMULATED_HUE_LIGHTS:
                for key, value in data.items():
                    SIMULATED_HUE_LIGHTS[light_id]["state"][key] = value
                print(f"[Hue Simulated Response] Light {SIMULATED_HUE_LIGHTS[light_id]['name']} updated: {data}")
                return [{"success": {f"{endpoint}/{key}": value for key, value in data.items()}}]
            else:
                return {"error": f"Light ID {light_id} not found."}
        elif "/lights" == endpoint and method == "GET":
            # Simulate getting all lights
            return SIMULATED_HUE_LIGHTS
        elif "/lights" in endpoint and method == "GET":
            light_id = endpoint.split('/')[2]
            if light_id in SIMULATED_HUE_LIGHTS:
                return SIMULATED_HUE_LIGHTS[light_id]
            else:
                return {"error": f"Light ID {light_id} not found."}
        else:
            return {"success": "Command simulated successfully."}
    except Exception as e:
        print(f"[Hue Simulated API Error] Error processing simulated command: {e}")
        return {"error": str(e)}

def _hue_find_light_id(light_name):
    """Finds a light ID by its name using fuzzy matching."""
    light_names = {light_id: light_data["name"].lower() for light_id, light_data in SIMULATED_HUE_LIGHTS.items()}
    best_match, score = process.extractOne(light_name.lower(), list(light_names.values()))

    if score > 80: # High threshold for light names
        for light_id, name in light_names.items():
            if name == best_match:
                return light_id
    return None

def _hue_get_light_status(light_id=None):
    """Gets and speaks the status of a specific light or all lights."""
    if not _hue_api_base_url(): return # Configuration check handled by base_url func

    if light_id:
        response = _hue_send_command("GET", f"/lights/{light_id}")
        if response and "error" not in response:
            light_name = response["name"]
            state = response["state"]
            status = "on" if state.get("on") else "off"
            brightness = state.get("bri", 0)
            speak(f"The {light_name} is currently {status}.")
            if status == "on":
                speak(f"Its brightness is at {int((brightness / 254) * 100)} percent.")
            print(f"[Hue Status] {light_name} is {status}, brightness: {brightness}")
        else:
            speak(f"I couldn't get the status for that light. It might not exist or there's a connection issue.")
            print(f"[Hue Error] Failed to get status for light ID {light_id}: {response.get('error', 'Unknown')}")
    else:
        response = _hue_send_command("GET", "/lights")
        if response and "error" not in response:
            if not response:
                speak("No Philips Hue lights are configured or found.")
                print("[Hue Status] No lights found in simulated data.")
                return
            
            speak("Here are the statuses of your Philips Hue lights:")
            for lid, light_data in response.items():
                name = light_data["name"]
                state = light_data["state"]
                status = "on" if state.get("on") else "off"
                brightness = int((state.get("bri", 0) / 254) * 100)
                speak(f"The {name} is {status}, at {brightness} percent brightness.")
                print(f"[Hue Status] {name}: {status}, {brightness}% brightness.")
        else:
            speak(f"I couldn't get the status of your lights. There might be a connection issue with the Hue Bridge.")
            print(f"[Hue Error] Failed to get all light statuses: {response.get('error', 'Unknown')}")


def _hue_set_light(light_id, on=None, brightness=None, color_name=None):
    """Sets the state of a Philips Hue light."""
    if not _hue_api_base_url(): return # Configuration check handled by base_url func

    data = {}
    if on is not None:
        data["on"] = on
    if brightness is not None:
        # Hue brightness is 0-254
        data["bri"] = int(min(254, max(0, brightness * 2.54)))
    if color_name:
        # Simplified color mapping for demonstration (Hue uses XY or HSL)
        if color_name == "red":
            data["hue"] = 0 # Example hue value for red
            data["sat"] = 254 # Max saturation
        elif color_name == "blue":
            data["hue"] = 46920 # Example hue value for blue
            data["sat"] = 254
        elif color_name == "green":
            data["hue"] = 25500 # Example hue value for green
            data["sat"] = 254
        elif color_name == "white":
            data["hue"] = 0
            data["sat"] = 0 # No saturation for white
        else:
            speak(f"I can't set the light to '{color_name}'. Try basic colors like red, blue, green, or white.")
            print(f"[Hue Info] Unsupported color: {color_name}")
            return

    if not data:
        speak("No specific light state provided to set.")
        return

    response = _hue_send_command("PUT", f"/lights/{light_id}/state", data)
    if response and "success" in response[0]:
        light_name = SIMULATED_HUE_LIGHTS.get(light_id, {}).get("name", "the light")
        status_msg = f"set {light_name}"
        if on is not None: status_msg += f" {'on' if on else 'off'}"
        if brightness is not None: status_msg += f" to {brightness}% brightness"
        if color_name: status_msg += f" to {color_name} color"
        speak(f"Okay, I have {status_msg}.")
        print(f"[Hue Action] {status_msg} for ID {light_id}.")
    else:
        speak(f"I couldn't control that light. There might be an issue with the Hue Bridge or the light ID.")
        print(f"[Hue Error] Failed to set light state for ID {light_id}: {response.get('error', 'Unknown')}")


def control_smart_device(action_type, user_command_raw, target_value=None):
    """
    Controls smart home devices (currently simulated Philips Hue lights).
    This function acts as a dispatcher for smart home commands.
    """
    if action_type == "lights_on":
        if target_value == "all":
            speak("Turning on all Philips Hue lights.")
            for light_id in SIMULATED_HUE_LIGHTS.keys():
                _hue_set_light(light_id, on=True)
        else: # Specific light, will prompt for name
            speak("Which light would you like me to turn on?")
            light_name = listen_command("Listening for light name...")
            if light_name:
                light_id = _hue_find_light_id(light_name)
                if light_id:
                    _hue_set_light(light_id, on=True)
                else:
                    speak(f"I couldn't find a light named '{light_name}'.")
            else:
                speak("No light name provided. Aborting.")

    elif action_type == "lights_off":
        if target_value == "all":
            speak("Turning off all Philips Hue lights.")
            for light_id in SIMULATED_HUE_LIGHTS.keys():
                _hue_set_light(light_id, on=False)
        else: # Specific light, will prompt for name
            speak("Which light would you like me to turn off?")
            light_name = listen_command("Listening for light name...")
            if light_name:
                light_id = _hue_find_light_id(light_name)
                if light_id:
                    _hue_set_light(light_id, on=False)
                else:
                    speak(f"I couldn't find a light named '{light_name}'.")
            else:
                speak("No light name provided. Aborting.")

    elif action_type == "lights_on_specific": # Triggered by "turn on the..."
        # Extract light name from the rest of the command
        light_name_query = user_command_raw.replace("turn on the", "").strip()
        if light_name_query:
            light_id = _hue_find_light_id(light_name_query)
            if light_id:
                _hue_set_light(light_id, on=True)
            else:
                speak(f"I couldn't find a light named '{light_name_query}'.")
        else:
            speak("Please tell me which light to turn on.")

    elif action_type == "lights_off_specific": # Triggered by "turn off the..."
        # Extract light name from the rest of the command
        light_name_query = user_command_raw.replace("turn off the", "").strip()
        if light_name_query:
            light_id = _hue_find_light_id(light_name_query)
            if light_id:
                _hue_set_light(light_id, on=False)
            else:
                speak(f"I couldn't find a light named '{light_name_query}'.")
        else:
            speak("Please tell me which light to turn off.")

    elif action_type == "set_brightness":
        # Example: "set light brightness to 50 percent" or "set living room light brightness to 75"
        speak("Which light's brightness would you like to set, and to what percentage?")
        brightness_query = listen_command("Listening for light name and brightness...")
        
        # Try to parse light name and percentage
        light_name = None
        brightness_percent = None

        # Simple parsing for "light_name to X percent" or "X percent light_name"
        parts = brightness_query.split(" to ")
        if len(parts) == 2:
            light_name = parts[0].replace("light brightness", "").replace("light", "").strip()
            num_part = ''.join(filter(str.isdigit, parts[1]))
            if num_part: brightness_percent = int(num_part)
        else: # Try to find a number first
            numbers = [int(s) for s in brightness_query.split() if s.isdigit()]
            if numbers:
                brightness_percent = numbers[0]
                # Remove the number and "percent" from the query to find light name
                temp_query = brightness_query.replace(str(brightness_percent), "").replace("percent", "").strip()
                light_name = temp_query.replace("light brightness", "").replace("light", "").strip()
            
        if not light_name:
            # Fallback if parsing failed, try to get light name separately
            speak("I didn't catch the light name. Which light?")
            light_name = listen_command("Listening for light name...")
        
        if not brightness_percent:
            speak("And to what percentage brightness?")
            brightness_str = listen_command("Listening for brightness percentage...")
            num_part = ''.join(filter(str.isdigit, brightness_str))
            if num_part: brightness_percent = int(num_part)

        if light_name and brightness_percent is not None:
            light_id = _hue_find_light_id(light_name)
            if light_id:
                _hue_set_light(light_id, brightness=brightness_percent)
            else:
                speak(f"I couldn't find a light named '{light_name}'.")
        else:
            speak("I need both the light name and the brightness percentage. Please try again.")

    elif action_type == "set_color":
        # Example: "set living room light to red"
        speak("Which light's color would you like to set, and to what color?")
        color_query = listen_command("Listening for light name and color...")

        light_name = None
        color_name = None

        # Simple parsing for "light_name to color"
        parts = color_query.split(" to ")
        if len(parts) == 2:
            light_name = parts[0].replace("light color", "").replace("light", "").strip()
            color_name = parts[1].strip()
        
        if not light_name:
            speak("I didn't catch the light name. Which light?")
            light_name = listen_command("Listening for light name...")
        
        if not color_name:
            speak("And to what color?")
            color_name = listen_command("Listening for color...")

        if light_name and color_name:
            light_id = _hue_find_light_id(light_name)
            if light_id:
                _hue_set_light(light_id, color_name=color_name)
            else:
                speak(f"I couldn't find a light named '{light_name}'.")
        else:
            speak("I need both the light name and the color. Please try again.")

    elif action_type == "get_light_status":
        speak("Which light's status would you like to know, or should I tell you about all lights?")
        status_query = listen_command("Listening for light name or 'all'...")
        if "all" in status_query or "every" in status_query:
            _hue_get_light_status(light_id=None) # Get status of all lights
        elif status_query:
            light_id = _hue_find_light_id(status_query)
            if light_id:
                _hue_get_light_status(light_id=light_id)
            else:
                speak(f"I couldn't find a light named '{status_query}'.")
        else:
            speak("No light specified. Please try again.")

    elif action_type == "set_thermostat":
        # This remains conceptual as it's not Hue-specific
        if target_value:
            speak(f"Setting the thermostat to {target_value} degrees. This remains conceptual and requires knowing your thermostat's device ID and API commands.")
            print(f"[Smart Home Conceptual] Setting thermostat to {target_value} degrees.")
        else:
            speak("What temperature should I set the thermostat to?")
            temp_str = listen_command("Listening for temperature...")
            cleaned_temp_str = ''.join(filter(str.isdigit, temp_str))
            if cleaned_temp_str:
                speak(f"Setting thermostat to {cleaned_temp_str} degrees. (Conceptual)")
                print(f"[Smart Home Conceptual] Setting thermostat to {cleaned_temp_str} degrees.")
            else:
                speak("I didn't get a valid temperature.")
    elif action_type == "lock_doors":
        speak("Locking the doors. This remains conceptual and requires integration with a smart lock system.")
        print("[Smart Home Conceptual] Locking doors.")
    elif action_type == "unlock_doors":
        speak("Unlocking the doors. This remains conceptual and requires integration with a smart lock system.")
        print("[Smart Home Conceptual] Unlocking doors.")
    else:
        speak("I'm not sure how to perform that smart home action.")


# 7. Music Playback Control (General - beyond Spotify) (Enhanced with basic local playback)
current_music_thread = None # To manage playsound in a non-blocking way

def _play_music_blocking(file_path):
    """Helper function to play music in a blocking manner."""
    try:
        playsound(file_path, block=True) # block=True ensures it plays fully
    except Exception as e:
        print(f"[Error] Error playing local music in thread: {e}")

def control_general_music_player(action_type, song_name=None):
    global current_music_thread
    speak(f"Initiating general music playback control.")
    print(f"[General Music] Action: {action_type}, Song: {song_name}")

    if action_type == "play_local":
        if not PLAYSOUND_AVAILABLE:
            speak("The 'playsound' library is not installed, so I cannot play local music.")
            print("[Error] playsound not available.")
            return

        music_dir = GLOBAL_CONFIG["LOCAL_MUSIC_DIRECTORY"]
        if not os.path.isdir(music_dir):
            speak(f"My local music directory '{music_dir}' is not found. Please configure it in the GLOBAL_CONFIG.")
            print(f"[Config Error] Local music directory not found: {music_dir}")
            return

        music_files = [f for f in os.listdir(music_dir) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
        if not music_files:
            speak(f"No music files found in your configured directory: {music_dir}.")
            print(f"[Info] No music files found in {music_dir}")
            return

        # Stop any currently playing music
        if current_music_thread and current_music_thread.is_alive():
            # playsound doesn't have a direct stop. This is a limitation.
            # In a real app, you'd use a different audio library (e.g., pygame.mixer)
            # or manage the subprocess created by playsound more directly.
            # For now, we'll just indicate we're starting new music.
            speak("Stopping current music to play new one.")
            # This is where you'd put logic to terminate the playsound process/thread if possible.

        # For simplicity, play the first found music file
        file_to_play = os.path.join(music_dir, music_files[0])
        speak(f"Playing '{music_files[0]}' from your local library.")
        print(f"[Action] Playing local music: {file_to_play}")
        
        # Run playsound in a separate thread to avoid blocking Jarvis
        current_music_thread = threading.Thread(target=_play_music_blocking, args=(file_to_play,))
        current_music_thread.start()
        speak("Music started.")

    elif action_type == "open_player":
        speak("Opening your default music player. (Conceptual)")
        print("[Action] Opening default music player.")
        # Example: Try to open Windows Media Player or VLC
        if platform.system() == "Windows":
            open_application("wmplayer.exe", "Windows Media Player", fallback_exe="vlc")
        elif platform.system() == "Darwin": # macOS
            open_application("Music", "Apple Music", fallback_exe="vlc")
        elif platform.system() == "Linux":
            open_application("rhythmbox", "Rhythmbox", fallback_exe="vlc") # Common Linux player
        else:
            speak("I don't know how to open a music player on your operating system.")

    elif action_type == "play_specific":
        if not PLAYSOUND_AVAILABLE:
            speak("The 'playsound' library is not installed, so I cannot play specific local music.")
            print("[Error] playsound not available.")
            return

        music_dir = GLOBAL_CONFIG["LOCAL_MUSIC_DIRECTORY"]
        if not os.path.isdir(music_dir):
            speak(f"My local music directory '{music_dir}' is not found. Please configure it in the GLOBAL_CONFIG.")
            print(f"[Config Error] Local music directory not found: {music_dir}")
            return

        if not song_name:
            speak("What song would you like me to play?")
            requested_song = listen_command("Listening for song name...")
            if not requested_song:
                speak("No song name provided. Aborting.")
                return
            song_name = requested_song

        found_song_path = None
        for root, _, files in os.walk(music_dir):
            for file in files:
                if song_name.lower() in file.lower() and file.lower().endswith(('.mp3', '.wav', '.ogg')):
                    found_song_path = os.path.join(root, file)
                    break
            if found_song_path:
                break
        
        if found_song_path:
            # Stop any currently playing music
            if current_music_thread and current_music_thread.is_alive():
                speak("Stopping current music to play new one.")
                # Logic to stop the previous playsound thread/process would go here.

            speak(f"Playing '{os.path.basename(found_song_path)}' from your local library.")
            print(f"[Action] Playing specific local music: {found_song_path}")
            try:
                current_music_thread = threading.Thread(target=_play_music_blocking, args=(found_song_path,))
                current_music_thread.start()
                speak("Music started.")
            except Exception as e:
                speak(f"Could not play '{os.path.basename(found_song_path)}': {e}. Ensure the file is valid and playsound is correctly installed.")
                print(f"[Error] Error playing specific local music: {e}")
        else:
            speak(f"Sorry, I could not find a song named '{song_name}' in your music directory.")
            print(f"[Info] Song '{song_name}' not found in {music_dir}.")

    elif action_type == "stop_playback":
        # playsound doesn't offer a direct stop via its API.
        # To truly stop, you'd need to manage the subprocess that playsound creates,
        # or use a different audio playback library like 'pygame.mixer' or 'pydub'.
        speak("Attempting to stop local music playback. Note: Direct stopping of playsound is limited and may require terminating the script or using a different audio library.")
        print("[Info] Stopping local music playback (conceptual for playsound).")
        # If current_music_thread was a subprocess, you could do current_music_process.terminate() here.
        # For playsound, it's more complex.


# --- Main Logic ---
def main():
    global hotword_detected_in_session # Declare global to modify

    speak(f"Hello. {GLOBAL_CONFIG['JARVIS_NAME']} at your service.")
    speak("What can I do for you today?")

    # Optional: Authenticate Spotify at startup if credentials are provided
    # UNCOMMENT THE LINE BELOW TO ATTEMPT SPOTIFY AUTHENTICATION ON STARTUP
    if GLOBAL_CONFIG.get("SPOTIFY_CLIENT_ID") != "YOUR_SPOTIFY_CLIENT_ID":
        authenticate_spotify()
    
    # Initialize NLP sentiment analyzer on startup
    if NLTK_AVAILABLE:
        initialize_sentiment_analyzer()

    while True:
        user_command_raw = ""
        if hotword_enabled and not hotword_detected_in_session:
            # If hotword is enabled and not yet detected in this session, listen for hotword
            if listen_for_hotword(GLOBAL_CONFIG["HOTWORD"]):
                hotword_detected_in_session = True
                speak("Yes?") # Acknowledge hotword
                # Now listen for the actual command
                user_command_raw = listen_command(prompt="Listening for your command...")
            else:
                continue # Keep listening for hotword
        else:
            # If hotword is not enabled, or if it was just detected, listen for a command
            user_command_raw = listen_command()
            # After processing the command, if hotword is enabled, reset the detection flag
            if hotword_enabled:
                hotword_detected_in_session = False # Go back to waiting for hotword

        if not user_command_raw:
            continue # Loop again if nothing was heard

        # It's important to define matched_command_key here as it's used in perform_dynamic_search
        matched_command_key = find_best_command(user_command_raw)

        if matched_command_key:
            action = COMMANDS[matched_command_key]
            action_type = action["type"]
            target = action.get("target")
            feedback_name = action.get("feedback", matched_command_key) # Use specific feedback name if available

            if action_type == "assistant_command":
                if target == "greet":
                    speak(f"Hello. How can {GLOBAL_CONFIG['JARVIS_NAME']} assist you today?")
                elif target == "status":
                    speak(f"I am fine, thank you. {GLOBAL_CONFIG['JARVIS_NAME']} is ready to assist.")
                elif target == "exit":
                    speak(f"Goodbye! Have a great day from {GLOBAL_CONFIG['JARVIS_NAME']}!")
                    break # Exit the loop
            
            elif action_type == "open_url":
                open_url(target, feedback_name)

            elif action_type == "open_app":
                fallback_exe = action.get("fallback_target_exe")
                open_application(target, feedback_name, fallback_exe)

            elif action_type == "close_app":
                close_application(target, feedback_name)
            
            elif action_type == "close_active_window":
                close_active_window()

            elif action_type == "volume_control":
                volume_action = action["action"]
                if volume_action == "set":
                    try:
                        speak("To what percentage would you like to set the volume?")
                        vol_str = listen_command(prompt="Listening for volume percentage...")
                        
                        # Remove non-digit characters (like '%', 'percent')
                        cleaned_vol_str = ''.join(filter(str.isdigit, vol_str))

                        if cleaned_vol_str: # Check if there are digits after cleaning
                            vol_level = int(cleaned_vol_str)
                            if 0 <= vol_level <= 100:
                                # Now calls the cross-platform function
                                set_cross_platform_volume(level=vol_level)
                            else:
                                speak("Please provide a percentage between 0 and 100.")
                        else:
                            speak("I didn't catch a valid volume percentage.")
                    except Exception as e:
                        speak(f"An error occurred trying to set volume: {e}.")
                elif volume_action == "increase":
                    speak("By how much should I increase the volume? For example, by 10 or 20 percent.")
                    change_str = listen_command(prompt="Listening for volume increase amount...")
                    
                    cleaned_change_str = ''.join(filter(str.isdigit, change_str))

                    if cleaned_change_str: # Check if there are digits after cleaning
                        change_amount = int(cleaned_change_str)
                        # Now calls the cross-platform function
                        set_cross_platform_volume(change_by=change_amount)
                    else:
                        speak("I didn't catch a valid increase amount.")
                elif volume_action == "decrease":
                    speak("By how much should I decrease the volume? For example, by 10 or 20 percent.")
                    change_str = listen_command(prompt="Listening for volume decrease amount...")
                    
                    cleaned_change_str = ''.join(filter(str.isdigit, change_str))

                    if cleaned_change_str: # Check if there are digits after cleaning
                        change_amount = -int(cleaned_change_str) # Negative for decrease
                        # Now calls the cross-platform function
                        set_cross_platform_volume(change_by=change_amount)
                    else:
                        speak("I didn't catch a valid decrease amount.")
                elif volume_action == "mute":
                    # Now calls the cross-platform function
                    set_cross_platform_volume(mute=True)
                elif volume_action == "unmute":
                    # Now calls the cross-platform function
                    set_cross_platform_volume(unmute=True)


            elif action_type == "info_query":
                if target == "time":
                    current_time_str = datetime.datetime.now().strftime("%I:%M %p")
                    speak(f"The current time is {current_time_str}.")
                elif target == "date":
                    current_date_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
                    speak(f"Today's date is {current_date_str}.")
                elif target == "day":
                    current_day_str = datetime.datetime.now().strftime("%A")
                    speak(f"Today is {current_day_str}.")
                elif target == "weather":
                    get_weather(GLOBAL_CONFIG["CITY_NAME"])

            elif action_type == "dynamic_search":
                # Pass matched_command_key here to help with precise query extraction
                perform_dynamic_search(user_command_raw, action["engine"])

            elif action_type == "gemini_query":
                query_for_gemini = user_command_raw.replace(matched_command_key, "").strip()
                if query_for_gemini:
                    ask_gemini(query_for_gemini)
                else:
                    speak(f"What would you like to ask {GLOBAL_CONFIG['JARVIS_NAME']}?")
                    follow_up_query = listen_command(prompt="Listening for your question...")
                    if follow_up_query:
                        ask_gemini(follow_up_query)
                    else:
                        speak(f"No question provided. {GLOBAL_CONFIG['JARVIS_NAME']} is aborting Gemini query.")
            
            elif action_type == "memory_command":
                memory_action = action["action"]
                if memory_action == "add":
                    speak(f"What do you want {GLOBAL_CONFIG['JARVIS_NAME']} to remember?")
                    note_to_add = listen_command(prompt="Listening for your note...")
                    if note_to_add:
                        add_to_memory(note_to_add)
                    else:
                        speak(f"No note provided. Nothing added to {GLOBAL_CONFIG['JARVIS_NAME']}'s memory.")
                elif memory_action == "read_all":
                    read_memory()
                elif memory_action == "summarize":
                    read_memory(summarize=True)
                elif memory_action == "delete":
                    forget_note() # Will prompt for ID/keyword
                elif memory_action == "clear_all":
                    clear_all_memory()
                elif memory_action == "read_category":
                    category_to_read = action.get("category_hint")
                    if not category_to_read: # If no hint, ask the user
                        speak(f"Which category of notes would you like {GLOBAL_CONFIG['JARVIS_NAME']} to read?")
                        category_to_read = listen_command(prompt="Listening for category...")
                    
                    if category_to_read:
                        read_memory(category=category_to_read)
                    else:
                        speak(f"No category provided. {GLOBAL_CONFIG['JARVIS_NAME']} cannot filter notes without a category.")
            
            elif action_type == "spotify_control":
                spotify_action = action["action"]
                if spotify_action == "play":
                    play_spotify_music()
                elif spotify_action == "pause":
                    pause_spotify_music()
                elif spotify_action == "next":
                    next_spotify_song()
                elif spotify_action == "previous":
                    previous_spotify_song()

            # --- NEW FEATURE HANDLERS ---
            elif action_type == "hotword_control":
                hotword_action = action["action"]
                if hotword_action == "start" or hotword_action == "enable":
                    start_hotword_listening()
                elif hotword_action == "stop" or hotword_action == "disable":
                    stop_hotword_listening()
            
            elif action_type == "nlp_control":
                nlp_action = action["action"]
                process_nlp_query(nlp_action)

            elif action_type == "gui_control":
                gui_action = action["action"]
                if gui_action == "open":
                    launch_gui()
                elif gui_action == "close":
                    close_gui()
            
            elif action_type == "calendar_reminder":
                calendar_action = action["action"]
                manage_calendar_event(calendar_action) # This function will handle sub-actions
            
            elif action_type == "smart_home_control":
                smart_home_action = action["action"]
                # Pass the raw command for more complex parsing within the smart home function
                control_smart_device(smart_home_action, user_command_raw, action.get("target"))
            
            elif action_type == "general_music_control":
                music_action = action["action"]
                if music_action == "play_specific":
                    # Extract song name from command
                    song_query = user_command_raw.replace("play song", "").strip()
                    control_general_music_player(music_action, song_name=song_query)
                elif music_action == "stop_playback":
                    control_general_music_player(music_action)
                else:
                    control_general_music_player(music_action)
            
        else:
            # Fallback: If no specific command is fuzzy-matched,
            # send the raw user input to Gemini for a general answer.
            speak(f"I didn't recognize '{user_command_raw}' specifically. Let {GLOBAL_CONFIG['JARVIS_NAME']} try asking Gemini.")
            ask_gemini(user_command_raw)

# Entry point of the script
if __name__ == "__main__":
    main()
