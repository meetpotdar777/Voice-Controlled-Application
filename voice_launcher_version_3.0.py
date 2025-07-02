import speech_recognition as sr
import pyttsx3
import os
import platform
import subprocess
import webbrowser
import datetime
import psutil
from fuzzywuzzy import process # For fuzzy matching commands
import requests # For API calls like weather

# --- Configuration ---
# You can customize these for your system and preferences
ASSISTANT_NAME = "Jarvis" # Or whatever you want to call your assistant
VOICE_RATE = 170
VOICE_VOLUME = 1.0
LISTEN_TIMEOUT = 5 # seconds
PHRASE_TIME_LIMIT = 5 # seconds
FUZZY_MATCH_THRESHOLD = 75 # Minimum score for fuzzy matching (0-100)

# OpenWeatherMap API Key (REQUIRED for weather features)
# 1. Go to https://openweathermap.org/api
# 2. Sign up for a free account.
# 3. Get your API key from your profile.
# 4. Replace 'YOUR_OPENWEATHERMAP_API_KEY' below with your actual key.
# 5. Get your city name correctly.
OPENWEATHERMAP_API_KEY = "PASTE_YOUR_API_KEY" # <--- REPLACE THIS!
CITY_NAME = "Australia" # Your default city for weather

# --- COMMANDS Mapping ---
# IMPORTANT: Adjust all file paths (e.g., for Spotify, Discord, WordPad, Firefox)
# to their EXACT locations on YOUR system using raw strings (r"C:\...")
COMMANDS = {
    # --- Websites (open_url type) ---
    "open chrome": {"type": "open_url", "target": "https://www.google.com"},
    "open google": {"type": "open_url", "target": "https://www.google.com"},
    "open browser": {"type": "open_url", "target": "https://www.google.com"},
    "open youtube": {"type": "open_url", "target": "https://www.youtube.com"},
    "open wikipedia": {"type": "open_url", "target": "https://www.wikipedia.org"},
    "open github": {"type": "open_url", "target": "https://github.com"},
    "open stack overflow": {"type": "open_url", "target": "https://stackoverflow.com"},
    "open whatsapp web": {"type": "open_url", "target": "https://web.whatsapp.com/"},
    "open whatsapp": {"type": "open_url", "target": "https://web.whatsapp.com/"}, # Alias
    "open amazon": {"type": "open_url", "target": "https://www.amazon.in"},
    "open flipkart": {"type": "open_url", "target": "https://www.flipkart.com"},
    "show me google": {"type": "open_url", "target": "https://www.google.com"}, # Alias
    "go to youtube": {"type": "open_url", "target": "https://www.youtube.com"}, # Alias

    # --- Applications (open_app type) ---
    # Built-in Windows apps (generally work with .exe name)
    "open calculator": {"type": "open_app", "target": "calc.exe", "process_name": "Calculator.exe"},
    "open notepad": {"type": "open_app", "target": "notepad.exe", "process_name": "notepad.exe"},
    "open command prompt": {"type": "open_app", "target": "cmd.exe", "process_name": "cmd.exe"},
    "open powershell": {"type": "open_app", "target": "powershell.exe", "process_name": "powershell.exe"},
    "open files": {"type": "open_app", "target": "explorer.exe", "process_name": "explorer.exe"},
    "open paint": {"type": "open_app", "target": "mspaint.exe", "process_name": "mspaint.exe"},
    "open task manager": {"type": "open_app", "target": "taskmgr.exe", "process_name": "Taskmgr.exe"}, # Note process name
    "open settings": {"type": "open_app", "target": "ms-settings:", "process_name": "SystemSettings.exe"}, # Note process name
    "open setting": {"type": "open_app", "target": "ms-settings:", "process_name": "SystemSettings.exe"}, # Alias

    # Installed Applications (ADJUST PATHS AND PROCESS NAMES!)
    # --- SPOTIFY FIX: Try URI first, then fallback to EXE path ---
    # The 'spotify:' URI is often the most reliable way to open Spotify on Windows.
    # If this fails, then uncomment and set the 'fallback_target_exe' to your *exact* .exe path.
    "open spotify": {
        "type": "open_app",
        "target": "spotify:", # URI scheme for Spotify
        "process_name": "Spotify.exe",
        # "fallback_target_exe": r"C:\Users\Administrator\AppData\Roaming\Spotify\Spotify.exe" # Uncomment and replace if URI fails
    },
    # Other applications (verify paths and process_names)
    "open visual studio code": {"type": "open_app", "target": "code", "process_name": "Code.exe"},
    "open discord": {"type": "open_app", "target": r"C:\Users\Administrator\AppData\Local\Discord\app-0.0.309\Discord.exe", "process_name": "Discord.exe"}, # !!! Check your version number here
    "open zoom": {"type": "open_app", "target": r"C:\Users\Administrator\AppData\Roaming\Zoom\bin\Zoom.exe", "process_name": "Zoom.exe"},
    "open vlc": {"type": "open_app", "target": r"C:\Program Files\VideoLAN\VLC\vlc.exe", "process_name": "vlc.exe"},
    "open firefox": {"type": "open_app", "target": r"C:\Program Files\Mozilla Firefox\firefox.exe", "process_name": "firefox.exe"},
    "open wordpad": {"type": "open_app", "target": r"C:\Program Files\Windows NT\Accessories\wordpad.exe", "process_name": "WordPad.exe"},

    # --- Close Commands (close_app type) ---
    # Target here is the PROCESS NAME (from Task Manager -> Details tab)
    "close chrome": {"type": "close_app", "target": "chrome.exe"},
    "close firefox": {"type": "close_app", "target": "firefox.exe"},
    "close calculator": {"type": "close_app", "target": "Calculator.exe"},
    "close notepad": {"type": "close_app", "target": "notepad.exe"},
    "close command prompt": {"type": "close_app", "target": "cmd.exe"},
    "close powershell": {"type": "close_app", "target": "powershell.exe"},
    "close files": {"type": "close_app", "target": "explorer.exe"},
    "close paint": {"type": "close_app", "target": "mspaint.exe"},
    "close spotify": {"type": "close_app", "target": "Spotify.exe"},
    "close discord": {"type": "close_app", "target": "Discord.exe"},
    "close visual studio code": {"type": "close_app", "target": "Code.exe"},
    "close zoom": {"type": "close_app", "target": "Zoom.exe"},
    "close vlc": {"type": "close_app", "target": "vlc.exe"},
    "close wordpad": {"type": "close_app", "target": "WordPad.exe"},
    "close task manager": {"type": "close_app", "target": "Taskmgr.exe"}, # Added for completeness

    # --- Informational Commands (info_query type) ---
    "what time is it": {"type": "info_query", "target": "time"},
    "tell me the time": {"type": "info_query", "target": "time"},
    "what is the current time": {"type": "info_query", "target": "time"},
    "what is the date today": {"type": "info_query", "target": "date"},
    "what day is it": {"type": "info_query", "target": "day"},
    "what's the weather": {"type": "info_query", "target": "weather"},
    "how is the weather": {"type": "info_query", "target": "weather"},

    # --- Search Commands (dynamic_search type) ---
    "search google": {"type": "dynamic_search", "target": "google"},
    "google search": {"type": "dynamic_search", "target": "google"},
    "search youtube": {"type": "dynamic_search", "target": "youtube"},
    "Youtube": {"type": "dynamic_search", "target": "youtube"},
    "find on wikipedia": {"type": "dynamic_search", "target": "wikipedia"},

    # --- Special Assistant Commands (assistant_command type) ---
    "exit": {"type": "assistant_command", "target": "exit"},
    "stop": {"type": "assistant_command", "target": "exit"},
    "quit": {"type": "assistant_command", "target": "exit"},
    "goodbye": {"type": "assistant_command", "target": "exit"},
    "hello": {"type": "assistant_command", "target": "greet"},
    "hi": {"type": "assistant_command", "target": "greet"},
}

# --- Initialize Speech Recognition and Text-to-Speech ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Configure voice properties (Explicitly try for a male voice)
try:
    voices = engine.getProperty('voices')
    male_voice_found = False
    for voice in voices:
        # Check for gender attribute (if available) or common male voice names
        if hasattr(voice, 'gender') and voice.gender == 'male':
            engine.setProperty('voice', voice.id)
            male_voice_found = True
            break
        elif "david" in voice.name.lower(): # Common male voice on Windows
            engine.setProperty('voice', voice.id)
            male_voice_found = True
            break
    
    if not male_voice_found and len(voices) > 0:
        print("Warning: Could not find an explicit male voice. Falling back to the first available voice.")
        engine.setProperty('voice', voices[0].id) # Fallback to first available voice
    
    # Add this for debugging the voice being used
    current_voice_id = engine.getProperty('voice')
    for voice in voices:
        if voice.id == current_voice_id:
            print(f"Assistant is using voice: {voice.name} (ID: {voice.id})")
            break

except Exception as e:
    print(f"Warning: Could not set voice properties: {e}")

engine.setProperty('rate', VOICE_RATE)
engine.setProperty('volume', VOICE_VOLUME)

def speak(text):
    """Converts text to speech and prints it."""
    print(f"{ASSISTANT_NAME}: {text}")
    engine.say(text)
    engine.runAndWait()

def listen_command(prompt="Listening for command...", timeout=LISTEN_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT):
    """Listens for a voice command and returns the recognized text."""
    with sr.Microphone() as source:
        print(f"\n{prompt}")
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            print("No speech detected within the timeout.")
            return ""

    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I could not understand your audio.")
        speak("Sorry, I didn't catch that. Please say that again.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        speak("My speech recognition service is currently unavailable. Please check your internet connection.")
        return ""

def find_best_command(user_input):
    """Uses fuzzy matching to find the best matching command from COMMANDS."""
    command_phrases = list(COMMANDS.keys())
    
    best_match = process.extractOne(user_input, command_phrases)
    
    if best_match and best_match[1] >= FUZZY_MATCH_THRESHOLD:
        print(f"Fuzzy matched '{user_input}' to '{best_match[0]}' with score {best_match[1]}")
        return best_match[0] # Return the exact command phrase from COMMANDS
    else:
        return None # No sufficiently good match found

def open_url(target_url, command_name_for_feedback):
    """Opens a URL in the default web browser."""
    speak(f"Opening {command_name_for_feedback}...")
    try:
        webbrowser.open(target_url)
        print(f"Successfully attempted to open: {target_url}")
    except Exception as e:
        speak(f"An error occurred while trying to open {command_name_for_feedback}. Please check the URL.")
        print(f"Error opening URL {target_url}: {e}")

def open_application(app_target, command_name_for_feedback, fallback_target_exe=None):
    """Opens an application based on the operating system, handling URIs and optional fallbacks."""
    speak(f"Opening {command_name_for_feedback}...")
    
    # Try opening as a URI first (e.g., "spotify:", "ms-settings:")
    # This is generally more reliable for apps that register URI schemes.
    if ":" in app_target and platform.system() == "Windows":
        try:
            subprocess.Popen(['start', app_target], shell=True)
            print(f"Successfully attempted to open URI: {app_target}")
            return
        except Exception as e:
            print(f"Failed to open as URI '{app_target}': {e}. Attempting as executable...")
            # If URI fails, try the fallback or original target as a direct executable path
            if fallback_target_exe:
                app_target = fallback_target_exe # Use the explicit fallback path
            # else: app_target remains the same if no fallback is provided and URI fails

    # If not a URI (or URI failed), try opening as a direct executable path/command
    try:
        current_os = platform.system()
        if current_os == "Windows":
            subprocess.Popen(app_target, shell=True)
        elif current_os == "Darwin": # macOS
            subprocess.Popen(["open", "-a", app_target])
        elif current_os == "Linux":
            subprocess.Popen([app_target])
        else:
            speak("Unsupported operating system for opening applications.")
            print(f"Error: Unsupported OS {current_os}")
            return
        print(f"Successfully attempted to open: {app_target}")

    except FileNotFoundError:
        speak(f"Sorry, I couldn't find the application '{command_name_for_feedback}'. Please ensure it's installed or in your system's PATH, or provide its full path in the configuration.")
        print(f"FileNotFoundError: Target '{app_target}' not found.")
    except Exception as e:
        speak(f"An error occurred while trying to open {command_name_for_feedback}. Please check the command configuration.")
        print(f"Error opening {command_name_for_feedback} ({app_target}): {e}")

def close_application(process_name_to_close, command_name_for_feedback):
    """Closes applications based on their process name."""
    speak(f"Attempting to close {command_name_for_feedback}...")
    closed_any = False
    process_name_to_close_lower = process_name_to_close.lower() # Ensure case-insensitive matching

    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() == process_name_to_close_lower:
                speak(f"Found {proc.info['name']} (PID: {proc.pid}). Terminating...")
                proc.terminate() # Try graceful termination first
                proc.wait(timeout=3) # Wait for a few seconds for it to close
                if proc.is_running():
                    speak(f"Still running. Force killing {proc.info['name']} (PID: {proc.pid}).")
                    proc.kill() # If still running, force kill
                closed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            print(f"Could not access or process {proc.info['name']} due to permissions or it no longer exists.")
            continue
        except Exception as e:
            print(f"Error while trying to close {proc.info['name']}: {e}")
            continue

    if closed_any:
        speak(f"{command_name_for_feedback} closed successfully.")
        print(f"Successfully closed: {process_name_to_close}")
    else:
        speak(f"Could not find any running instances of {command_name_for_feedback} to close.")
        print(f"No running instances found for: {process_name_to_close}")

def get_weather(city):
    """Fetches current weather information from OpenWeatherMap."""
    if not OPENWEATHERMAP_API_KEY or OPENWEATHERMAP_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
        speak("I cannot fetch weather information. My OpenWeatherMap API key is not configured. Please get a free API key from OpenWeatherMap.org and update the script.")
        print("Error: OpenWeatherMap API key not set. Please update OPENWEATHERMAP_API_KEY in the script.")
        return

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric" # units=metric for Celsius

    try:
        response = requests.get(complete_url)
        data = response.json()

        if data["cod"] == 200: # Check for successful response code
            main = data["main"]
            weather = data["weather"][0]
            temperature = main["temp"]
            humidity = main["humidity"]
            weather_description = weather["description"]

            speak(f"The weather in {city} is {weather_description}, with a temperature of {temperature:.1f} degrees Celsius and {humidity}% humidity.")
        elif data["cod"] == "404":
            speak(f"Sorry, I couldn't find weather information for {city}. Please check the city name.")
            print(f"Weather API error: City '{city}' not found.")
        else:
            speak(f"An error occurred while fetching weather data: {data.get('message', 'Unknown error')}")
            print(f"Weather API response error: {data}")
    except requests.exceptions.RequestException as e:
        speak("I'm having trouble connecting to the weather service. Please check your internet connection.")
        print(f"Network error while fetching weather: {e}")
    except Exception as e:
        speak("An unexpected error occurred while getting the weather.")
        print(f"General error fetching weather: {e}")

def main():
    # Initial greeting with context
    current_time_str = datetime.datetime.now().strftime("%I:%M %p")
    current_date_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Hello! I am {ASSISTANT_NAME}. It's {current_time_str} on {current_date_str}. How can I assist you today?")

    while True:
        user_command_raw = listen_command()
        if not user_command_raw:
            continue # If no command was recognized or timeout, listen again

        # Use fuzzy matching to find the best possible command
        matched_command_key = find_best_command(user_command_raw)

        if matched_command_key:
            action = COMMANDS[matched_command_key]
            action_type = action["type"]
            target = action["target"]

            # General feedback name (removes "open " or "close " prefix)
            command_name_for_feedback = user_command_raw.replace("open ", "").replace("close ", "").strip()

            if action_type == "assistant_command":
                if target == "exit":
                    speak(f"Exiting {ASSISTANT_NAME}. Goodbye!")
                    break
                elif target == "greet":
                    speak(f"Hello there! How can I help you, boss?")
            
            elif action_type == "open_url":
                open_url(target, command_name_for_feedback)

            elif action_type == "open_app":
                # Check for an explicit fallback executable path for the app
                fallback_exe = action.get("fallback_target_exe")
                open_application(target, command_name_for_feedback, fallback_exe)

            elif action_type == "close_app":
                close_application(target, command_name_for_feedback)
            
            elif action_type == "info_query":
                if target == "time":
                    current_time_str = datetime.datetime.now().strftime("%I:%M %p")
                    speak(f"The current time is {current_time_str}")
                elif target == "date":
                    current_date_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
                    speak(f"Today's date is {current_date_str}")
                elif target == "day":
                    current_day_str = datetime.datetime.now().strftime("%A")
                    speak(f"Today is {current_day_str}")
                elif target == "weather":
                    get_weather(CITY_NAME)

            elif action_type == "dynamic_search":
                speak(f"What would you like me to search for on {target}?")
                search_query = listen_command(prompt="Listening for search query...")
                if search_query:
                    search_query_formatted = search_query.replace(' ', '+')
                    if target == "google":
                        search_url = f"https://www.google.com/search?q={search_query_formatted}"
                    elif target == "youtube":
                        # Note: This is an older Youtube URL. Modern Youtube is usually
                        # "https://www.youtube.com/results?search_query="
                        # Let's update it for better results.
                        search_url = f"https://www.youtube.com/results?search_query={search_query_formatted}"
                    elif target == "wikipedia":
                        search_url = f"https://en.wikipedia.org/wiki/Special:Search?search={search_query_formatted}"
                    else:
                        search_url = f"https://www.google.com/search?q={search_query_formatted}" # Fallback
                    
                    speak(f"Searching {target} for {search_query}...")
                    webbrowser.open(search_url)
                else:
                    speak("No search query provided. Aborting search.")

        else:
            speak("I didn't quite understand that. Could you please rephrase your command or try something else?")

if __name__ == "__main__":
    main()