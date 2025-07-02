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
import win32gui
import win32con
import win32process
import time # Import time for sleep
import json # Import json module for structured memory

# --- GLOBAL CONFIGURATION (IMPORTANT: Customize these values) ---
GLOBAL_CONFIG = {
    "CITY_NAME": "Australia",  # Your city name for weather queries
    "OPENWEATHERMAP_API_KEY": "YOUR_OPENWEATHERMAP_API_KEY", # Get from openweathermap.org
    "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY", # Get from console.cloud.google.com (Generative Language API)
    "GEMINI_MODEL_NAME": "gemini-1.5-flash", # Changed to a commonly supported model. You can try 'gemini-1.5-pro' if preferred.
    "VOICE_GENDER": "male", # Options: "male", "female", or "default"
    "SPEECH_RATE": 170, # Words per minute (adjust as desired)
    "MEMORY_FILE": "jarvis_memory.json", # Changed to JSON file for structured memory
    "JARVIS_NAME": "Jarvis" # Define Jarvis's name
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
            print("Male voice not explicitly found or set. Falling back to first available voice.")
        elif not male_voice_found:
             print("No voices found. Using system default.")

    elif GLOBAL_CONFIG["VOICE_GENDER"].lower() == "female":
        female_voice_found = False
        for voice in voices:
            if "female" in voice.name.lower() or "zira" in voice.name.lower() or voice.id.endswith("1"):
                engine.setProperty('voice', voice.id)
                female_voice_found = True
                break
        if not female_voice_found and len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
            print("Female voice not explicitly found or set. Falling back to second available voice.")
        elif not female_voice_found:
             print("No female voices found or only one voice. Using system default.")

    else: # Default or invalid setting
        if len(voices) > 0:
            engine.setProperty('voice', voices[0].id)
            print(f"Using default voice: {voices[0].name}")
        else:
            print("No voices found. Using system default.")

except IndexError:
    print("Not enough voices found to set specific gender. Using default system voice.")
except Exception as e:
    print(f"Error setting voice: {e}. Using default system voice.")

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
            print(f"Error: Configured Gemini model '{chosen_model_name}' not found or does not support 'generateContent'.")
            print("Available models supporting 'generateContent':", available_models)
            if available_models:
                fallback_model = available_models[0]
                speak(f"Falling back to model {fallback_model} for Gemini features.")
                gemini_model = genai.GenerativeModel(fallback_model)
                print(f"Successfully configured {GLOBAL_CONFIG['JARVIS_NAME']} with fallback model: {fallback_model}")
            else:
                print("No Gemini models found supporting 'generateContent'. Gemini features will be unavailable.")

        if gemini_model:
            print(f"{GLOBAL_CONFIG['JARVIS_NAME']} Gemini API configured successfully with model: {gemini_model.model_name}.")
        else:
            print(f"{GLOBAL_CONFIG['JARVIS_NAME']} Gemini features will be unavailable.")

    except Exception as e:
        print(f"Error configuring Gemini API for {GLOBAL_CONFIG['JARVIS_NAME']}: {e}. Gemini features will be unavailable.")
else:
    print(f"Warning: GEMINI_API_KEY not found or is default for {GLOBAL_CONFIG['JARVIS_NAME']}. Gemini features will be unavailable.")


# --- Define the COMMANDS dictionary ---
COMMANDS = {
    # Assistant Commands
    "hello jarvis": {"type": "assistant_command", "target": "greet"},
    "how are you": {"type": "assistant_command", "target": "status"},
    "exit": {"type": "assistant_command", "target": "exit"},
    "quit": {"type": "assistant_command", "target": "exit"},
    "goodbye": {"type": "assistant_command", "target": "exit"},

    # URL Opening Commands
    "open google": {"type": "open_url", "target": "https://www.google.com"},
    "open youtube": {"type": "open_url", "target": "http://youtube.com"}, # Corrected YouTube URL
    "open github": {"type": "open_url", "target": "https://github.com"},
    "open linkedin": {"type": "open_url", "target": "https://www.linkedin.com"},

    # Application Opening Commands (Windows specific paths or common .exe names)
    "open chrome": {"type": "open_app", "target": "chrome.exe", "fallback_target_exe": "chrome"},
    "open firefox": {"type": "open_app", "target": "firefox.exe", "fallback_target_exe": "firefox"},
    "open edge": {"type": "open_app", "target": "msedge.exe", "fallback_target_exe": "msedge"},
    "open outlook": {"type": "open_app", "target": "OUTLOOK.EXE", "fallback_target_exe": "outlook"},
    "open spotify": {"type": "open_app", "target": "Spotify.exe", "fallback_target_exe": "spotify"},
    "open calculator": {"type": "open_app", "target": "Calculator.exe", "fallback_target_exe": "calc"},
    "open notepad": {"type": "open_app", "target": "notepad.exe", "fallback_target_exe": "notepad"},
    "open paint": {"type": "open_app", "target": "mspaint.exe", "fallback_target_exe": "mspaint"},
    "open word": {"type": "open_app", "target": "WINWORD.EXE", "fallback_target_exe": "winword"},
    "open excel": {"type": "open_app", "target": "EXCEL.EXE", "fallback_target_exe": "excel"},
    "open powerpoint": {"type": "open_app", "target": "POWERPNT.EXE", "fallback_target_exe": "powerpnt"},
    "open vlc": {"type": "open_app", "target": "vlc.exe", "fallback_target_exe": "vlc"},
    "open discord": {"type": "open_app", "target": "Discord.exe", "fallback_target_exe": "discord"},
    "open vs code": {"type": "open_app", "target": "Code.exe", "fallback_target_exe": "code"},

    # Application Closing Commands (Windows specific process names)
    "close chrome": {"type": "close_app", "target": "chrome.exe"},
    "close firefox": {"type": "close_app", "target": "firefox.exe"},
    "close edge": {"type": "close_app", "target": "msedge.exe"},
    "close outlook": {"type": "close_app", "target": "OUTLOOK.EXE"},
    "close spotify": {"type": "close_app", "target": "Spotify.exe"},
    "close calculator": {"type": "close_app", "target": "Calculator.exe"},
    "close notepad": {"type": "close_app", "target": "notepad.exe"},
    "close paint": {"type": "close_app", "target": "mspaint.exe"},
    "close word": {"type": "close_app", "target": "WINWORD.EXE"},
    "close excel": {"type": "close_app", "target": "EXCEL.EXE"},
    "close powerpoint": {"type": "close_app", "target": "POWERPNT.EXE"},
    "close vlc": {"type": "close_app", "target": "vlc.exe"},
    "close discord": {"type": "close_app", "target": "Discord.exe"},
    "close vs code": {"type": "close_app", "target": "Code.exe"},
    "close active window": {"type": "close_active_window"}, # New command

    # Information Queries
    "time": {"type": "info_query", "target": "time"},
    "date": {"type": "info_query", "target": "date"},
    "day": {"type": "info_query", "target": "day"},
    "weather": {"type": "info_query", "target": "weather"},

    # Dynamic Search Commands
    "search google for": {"type": "dynamic_search", "engine": "google"},
    "search youtube for": {"type": "dynamic_search", "engine": "youtube"},
    "find on google": {"type": "dynamic_search", "engine": "google"},
    "find on youtube": {"type": "dynamic_search", "engine": "youtube"},
    "search github for": {"type": "dynamic_search", "engine": "github"}, # <--- ADDED GITHUB SEARCH HERE

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
}

# --- Speech Functions ---
def speak(text):
    """Converts text to speech using the initialized engine."""
    print(f"{GLOBAL_CONFIG['JARVIS_NAME']}: {text}")
    engine.say(text)
    engine.runAndWait()

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
            print("No speech detected.")
            return ""
        except Exception as e:
            print(f"Microphone error: {e}")
            return ""

    try:
        command = r.recognize_google(audio, language='en-in').lower()
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""

def find_best_command(user_input):
    """
    Finds the best fuzzy match for the user's input against predefined commands.
    Returns the matched command key if confidence is above a threshold, otherwise None.
    """
    command_phrases = list(COMMANDS.keys())
    best_match, score = process.extractOne(user_input, command_phrases)

    if score > 75: # Adjust this threshold as needed
        print(f"Best fuzzy match for '{user_input}': '{best_match}' with score {score}")
        return best_match
    else:
        print(f"No strong command match found for '{user_input}' (score: {score})")
        return None

# --- Core Action Functions ---
def open_url(url, command_name_for_feedback):
    """Opens a URL in the default web browser."""
    speak(f"Opening {command_name_for_feedback} for you, Sir.")
    webbrowser.open(url)

def open_application(app_target, command_name_for_feedback, fallback_exe=None):
    """
    Opens an application. Tries direct execution, then common system commands.
    `app_target` can be an exact process name (e.g., "chrome.exe") or a full path.
    `fallback_exe` is a common alias for `start` command.
    """
    speak(f"Opening {command_name_for_feedback}...")
    try:
        if platform.system() == "Windows":
            subprocess.Popen(app_target)
        else:
            subprocess.Popen([app_target])
        print(f"Successfully started: {app_target}")
        speak(f"{command_name_for_feedback} opened, Sir.")
    except FileNotFoundError:
        print(f"Application '{app_target}' not found directly.")
        if fallback_exe:
            try:
                if platform.system() == "Windows":
                    subprocess.Popen(['start', fallback_exe], shell=True)
                elif platform.system() == "Linux":
                    subprocess.Popen(['xdg-open', fallback_exe])
                elif platform.system() == "Darwin": # macOS
                    subprocess.Popen(['open', '-a', fallback_exe])
                print(f"Attempted to start '{fallback_exe}' via system command.")
                speak(f"{command_name_for_feedback} opened, Sir.")
            except Exception as e:
                speak(f"I couldn't open {command_name_for_feedback}, Sir. Error: {e}")
                print(f"Failed to open {command_name_for_feedback} via fallback: {e}")
        else:
            speak(f"I'm sorry, Sir, I couldn't find {command_name_for_feedback} to open.")
            print(f"No fallback provided for {app_target}.")
    except Exception as e:
        speak(f"An error occurred while {GLOBAL_CONFIG['JARVIS_NAME']} was trying to open {command_name_for_feedback}.")
        print(f"Error opening {app_target}: {e}")


def close_application(process_name_to_close, command_name_for_feedback):
    """
    Closes applications more robustly on Windows by first sending a WM_CLOSE message
    for graphical applications, then by terminating/killing processes.
    """
    if platform.system() != "Windows":
        speak("This close command is optimized for Windows and may not work as expected on this operating system.")
        print("Note: close_application is primarily for Windows.")
        found_and_attempted = False
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'].lower() == process_name_to_close.lower():
                    speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} is attempting to terminate {command_name_for_feedback} (PID: {proc.pid}).")
                    proc.terminate()
                    proc.wait(timeout=3)
                    if proc.is_running():
                        proc.kill()
                    found_and_attempted = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if found_and_attempted:
            speak(f"{command_name_for_feedback} close attempt completed by {GLOBAL_CONFIG['JARVIS_NAME']}.")
        else:
            speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} could not find any running instances of {command_name_for_feedback} to close.")
        return

    speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} is attempting to close {command_name_for_feedback}...")
    closed_any = False
    process_name_to_close_lower = process_name_to_close.lower()
    
    def enum_windows_callback(hwnd, extra):
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        try:
            proc_info = psutil.Process(pid)
            if proc_info.name().lower() == process_name_to_close_lower:
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                    print(f"Found window for {proc_info.name()} (PID: {pid}). Sending WM_CLOSE.")
                    win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    nonlocal closed_any
                    closed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    win32gui.EnumWindows(enum_windows_callback, None)
    
    if closed_any:
        time.sleep(2)

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
                        speak(f"Still running. {GLOBAL_CONFIG['JARVIS_NAME']} is force killing {proc.info['name']} (PID: {proc.pid}).")
                        proc.kill()
                    
                    closed_any = True

        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            speak(f"Access denied to close {proc.info['name']}, Sir. Please try running {GLOBAL_CONFIG['JARVIS_NAME']} as administrator for this command.")
            print(f"AccessDenied: Could not terminate process {proc.info['name']} (PID: {proc.pid}).")
            closed_any = True
            continue
        except Exception as e:
            print(f"Error while {GLOBAL_CONFIG['JARVIS_NAME']} was trying to close {proc.info['name']} (PID: {proc.pid}): {e}")
            continue

    if closed_any:
        speak(f"{command_name_for_feedback} close attempt completed by {GLOBAL_CONFIG['JARVIS_NAME']}.")
        final_check_running = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == process_name_to_close_lower:
                final_check_running = True
                break
        
        if final_check_running:
            speak(f"Some instances of {command_name_for_feedback} might still be running, Sir.")
        else:
            speak(f"{command_name_for_feedback} closed successfully, Sir.")
            print(f"Successfully closed: {process_name_to_close}")
    else:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} could not find any running instances of {command_name_for_feedback} to close, or it's a non-closable system process, Sir.")
        print(f"No running instances found or not closable for: {process_name_to_close}")

def close_active_window():
    """Closes the currently active window on Windows."""
    if platform.system() != "Windows":
        speak("This command is only available on Windows, Sir.")
        return

    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            speak("Active window closed, Sir.")
            print("Active window closed.")
        else:
            speak("No active window found to close, Sir.")
            print("No active window found.")
    except Exception as e:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} could not close the active window. Error: {e}")
        print(f"Error closing active window: {e}")

def get_weather(city_name):
    """Fetches and speaks the current weather for the given city."""
    api_key = GLOBAL_CONFIG["OPENWEATHERMAP_API_KEY"]
    if not api_key or api_key == "YOUR_OPENWEATHERMAP_API_KEY":
        speak(f"My OpenWeatherMap API key is not configured, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} cannot fetch weather information.")
        print("Error: OpenWeatherMap API key not set.")
        return

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city_name}&appid={api_key}&units=metric"
    try:
        response = requests.get(complete_url)
        data = response.json()

        if data["cod"] == 200:
            main_data = data["main"]
            weather_data = data["weather"][0]
            temperature = main_data["temp"]
            humidity = main_data["humidity"]
            description = weather_data["description"]
            
            speak(f"The weather in {city_name} is currently {description}, with a temperature of {temperature:.1f} degrees Celsius and humidity of {humidity} percent, Sir.")
        elif data["cod"] == "404":
            speak(f"Sorry, Sir, {GLOBAL_CONFIG['JARVIS_NAME']} could not find weather information for {city_name}. Please check the city name.")
        else:
            speak(f"Sorry, Sir, {GLOBAL_CONFIG['JARVIS_NAME']} could not retrieve weather information at this time.")
            print(f"OpenWeatherMap API error: {data.get('message', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        speak(f"I cannot connect to the internet to get weather information, Sir. Please check your connection.")
    except Exception as e:
        speak(f"An error occurred while {GLOBAL_CONFIG['JARVIS_NAME']} was fetching weather information.")
        print(f"Weather error: {e}")

def ask_gemini(query):
    """Sends a query to the Gemini model and speaks the response."""
    if not gemini_model:
        speak(f"I cannot connect to the Gemini AI, Sir. My API key is not configured or an error occurred during setup.")
        return

    speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} is thinking...")
    try:
        response = gemini_model.generate_content(query)
        gemini_text_response = response.text
        speak(gemini_text_response)
    except Exception as e:
        speak(f"I'm sorry, Sir, {GLOBAL_CONFIG['JARVIS_NAME']} encountered an error trying to process your request with Gemini.")
        print(f"Gemini API Error: {e}")
        if "Blocked" in str(e):
            speak("My response was blocked due to safety concerns. Please try a different query.")
        elif "quota" in str(e).lower():
            speak("I've reached my usage limit for the Gemini API. Please try again later.")
        elif "API key" in str(e):
            speak("There's an issue with my Gemini API key. Please check its configuration.")
        elif "empty" in str(e).lower() or "no candidates" in str(e).lower():
            speak("I received an empty response from Gemini. It might not have an answer for that.")
        elif "404" in str(e) and "models/" in str(e):
            speak("The specific Gemini model I was trying to use is not available or supported. Please check the model name in the configuration.")


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
            query = user_command_raw.replace("search", "").replace("find", "").replace(search_engine_type, "").replace("on", "").replace("for", "").strip()

    except Exception:
        # Generic fallback in case of unexpected parsing issues
        query = user_command_raw.replace("search", "").replace("find", "").replace(search_engine_type, "").replace("on", "").replace("for", "").strip()

    if not query:
        speak(f"What do you want {GLOBAL_CONFIG['JARVIS_NAME']} to search on {search_engine_type}, Sir?")
        follow_up_query = listen_command(prompt=f"Listening for your {search_engine_type} query...")
        if follow_up_query:
            query = follow_up_query
        else:
            speak(f"No search query provided, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} is aborting search.")
            return

    if search_engine_type == "google":
        search_url = f"https://www.google.com/search?q={query}"
        speak(f"Searching Google for {query}, Sir.")
    elif search_engine_type == "youtube":
        search_url = f"https://www.youtube.com/results?search_query={query}" # Corrected Youtube URL
        speak(f"Searching YouTube for {query}, Sir.")
    elif search_engine_type == "github": # <--- ADDED GITHUB SEARCH LOGIC HERE
        search_url = f"https://github.com/search?q={query}"
        speak(f"Searching GitHub for {query}, Sir.")
    else:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} can only search on Google, YouTube, or GitHub at the moment, Sir.")
        return

    webbrowser.open(search_url)

# --- JSON Memory Functions ---
def load_memory_data():
    """Loads memory data from the JSON file."""
    memory_file = GLOBAL_CONFIG["MEMORY_FILE"]
    if not os.path.exists(memory_file) or os.stat(memory_file).st_size == 0:
        return []
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: {GLOBAL_CONFIG['JARVIS_NAME']} detected corrupted or empty JSON in memory file. Starting with empty memory.")
        return []
    except Exception as e:
        print(f"Error loading memory data for {GLOBAL_CONFIG['JARVIS_NAME']}: {e}")
        return []

def save_memory_data(data):
    """Saves memory data to the JSON file."""
    memory_file = GLOBAL_CONFIG["MEMORY_FILE"]
    try:
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        speak(f"Sorry, Sir, {GLOBAL_CONFIG['JARVIS_NAME']} could not save the memory data.")
        print(f"Error saving memory data: {e}")

def add_to_memory(note, category=None):
    """Adds a timestamped and categorized note to the memory file."""
    memory_data = load_memory_data()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate a unique ID (simple increment for now)
    new_id = 1
    if memory_data:
        new_id = max(item.get("id", 0) for item in memory_data) + 1

    if not category:
        speak(f"What category does this note belong to, Sir? For example: idea, task, shopping list, or personal.")
        spoken_category = listen_command(prompt=f"Listening for category...")
        if spoken_category:
            category = spoken_category.lower().strip()
        else:
            speak(f"No category provided, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} will save it without a specific category.")
            category = "uncategorized"

    new_entry = {
        "id": new_id,
        "timestamp": timestamp,
        "note": note,
        "category": category
    }
    memory_data.append(new_entry)
    save_memory_data(memory_data)
    speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has remembered that as a '{category}' note with ID {new_id}.")
    print(f"Added to memory (ID {new_id}, Category '{category}'): {note}")

def read_memory(category=None, summarize=False):
    """Reads and speaks the contents of the memory file, optionally by category or summarized."""
    memory_data = load_memory_data()

    if not memory_data:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} doesn't have anything in memory yet, Sir.")
        return

    filtered_notes = []
    if category:
        speak(f"Here are your notes in the '{category}' category, Sir:")
        for entry in memory_data:
            if entry.get("category", "uncategorized").lower() == category.lower():
                filtered_notes.append(entry)
    else:
        speak(f"Here is everything {GLOBAL_CONFIG['JARVIS_NAME']} has in memory, Sir:")
        filtered_notes = memory_data

    if not filtered_notes:
        if category:
            speak(f"I found no notes in the '{category}' category, Sir.")
        else:
            speak(f"My memory is currently empty, Sir.")
        return

    notes_text_for_display = ""
    for entry in filtered_notes:
        notes_text_for_display += f"ID: {entry.get('id', 'N/A')} | [{entry['timestamp']}] | Category: {entry.get('category', 'Uncategorized').capitalize()}\n"
        notes_text_for_display += f"  Note: {entry['note']}\n\n"

    print(f"\n--- {GLOBAL_CONFIG['JARVIS_NAME']}'s Memory ---")
    print(notes_text_for_display)
    print("----------------------------------\n")

    if summarize and gemini_model:
        speak(f"Since there are multiple entries, {GLOBAL_CONFIG['JARVIS_NAME']} will provide a summary for you.")
        prompt = f"Please summarize the following memory entries concisely, highlighting key information and actionable items. Present it as if you are a helpful AI assistant named {GLOBAL_CONFIG['JARVIS_NAME']}:\n\n{notes_text_for_display}"
        ask_gemini(prompt)
    elif len(notes_text_for_display) < 1000: # Adjust character limit for speaking
        speak(f"Here are the notes: {notes_text_for_display.replace('ID:', 'ID').replace('Category:', 'Category')}") # Speak cleaner version
    else:
        speak(f"Your memory contains many entries, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has printed them to the console.")


def forget_note(note_identifier=None):
    """Deletes a specific note by ID or a keyword/phrase."""
    memory_data = load_memory_data()

    if not memory_data:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} has no notes to forget, Sir.")
        return

    if not note_identifier:
        speak(f"Which note would you like {GLOBAL_CONFIG['JARVIS_NAME']} to forget, Sir? Please tell me the ID number or a keyword from the note.")
        note_identifier = listen_command(prompt="Listening for note ID or keyword...")
        if not note_identifier:
            speak(f"No identifier provided, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} cannot forget a note without knowing which one.")
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
            speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten note with ID {note_id}.")
            print(f"Deleted note with ID {note_id}: {found_notes[0]['note']}")
            return

    except ValueError:
        # Not an ID, try to delete by keyword/phrase
        speak(f"Searching for notes containing '{note_identifier}' to forget, Sir.")
        
        # Use fuzzy matching to find notes containing the identifier
        matching_entries = []
        for entry in memory_data:
            if process.extractOne(note_identifier, [entry['note']], scorer=process.fuzz.partial_ratio)[1] > 80: # Adjust threshold as needed
                matching_entries.append(entry)
            else:
                updated_memory_data.append(entry) # Keep notes that don't match strongly

        if not matching_entries:
            speak(f"I found no notes matching '{note_identifier}' to forget, Sir.")
            updated_memory_data = memory_data # Restore original if no match
        elif len(matching_entries) == 1:
            # If only one strong match, delete it
            save_memory_data(updated_memory_data)
            speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten the note: '{matching_entries[0]['note']}'.")
            print(f"Deleted note by keyword: {matching_entries[0]['note']}")
        else:
            # Multiple matches, ask for clarification
            speak(f"Sir, I found multiple notes containing '{note_identifier}'. Please clarify which one you'd like {GLOBAL_CONFIG['JARVIS_NAME']} to forget by saying its ID:")
            for i, entry in enumerate(matching_entries):
                speak(f"Note {i+1}: ID {entry.get('id', 'N/A')}, '{entry['note']}'")
            
            clarification = listen_command(prompt="Listening for ID to delete...")
            try:
                clarification_id = int(clarification)
                final_updated_memory = []
                deleted_one = False
                for entry in memory_data: # Iterate original data to ensure correct deletion
                    if entry.get("id") == clarification_id:
                        found_notes.append(entry)
                        deleted_one = True
                    else:
                        final_updated_memory.append(entry)
                
                if deleted_one:
                    save_memory_data(final_updated_memory)
                    speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten note with ID {clarification_id}.")
                    print(f"Deleted note with ID {clarification_id}: {found_notes[0]['note'] if found_notes else ''}")
                else:
                    speak(f"I could not find a note with ID {clarification_id}, Sir. No notes were deleted.")
                    save_memory_data(memory_data) # Revert if no deletion
            except ValueError:
                speak(f"That was not a valid ID, Sir. No notes were deleted.")
                save_memory_data(memory_data) # Revert if no deletion
            except Exception as e:
                speak(f"An error occurred during deletion, Sir. {e}")
                save_memory_data(memory_data) # Revert if error

    if len(memory_data) == initial_memory_count and not found_notes:
        speak(f"I could not find any notes matching '{note_identifier}' to forget, Sir.")

def clear_all_memory():
    """Clears all notes from the memory file after confirmation."""
    speak(f"Are you sure you want {GLOBAL_CONFIG['JARVIS_NAME']} to clear all your memories, Sir? This action cannot be undone.")
    confirmation = listen_command(prompt="Say 'yes' to confirm or 'no' to cancel.")
    if "yes" in confirmation:
        save_memory_data([]) # Save an empty list
        speak(f"All memories have been cleared, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has an empty slate.")
        print("All memory cleared.")
    else:
        speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} will keep your memories intact.")

# --- Main Logic ---
def main():
    speak(f"Hello Sir. {GLOBAL_CONFIG['JARVIS_NAME']} at your service.")
    speak("What can I do for you today, Sir?")

    while True:
        user_command_raw = listen_command()
        if not user_command_raw:
            continue

        matched_command_key = find_best_command(user_command_raw)

        if matched_command_key:
            action = COMMANDS[matched_command_key]
            action_type = action["type"]
            target = action.get("target")
            
            command_name_for_feedback = user_command_raw.replace("open ", "").replace("close ", "").strip()

            if action_type == "assistant_command":
                if target == "greet":
                    speak(f"Hello, Sir. How can {GLOBAL_CONFIG['JARVIS_NAME']} assist you today?")
                elif target == "status":
                    speak(f"I am fine, thank you, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} is ready to assist.")
                elif target == "exit":
                    speak(f"Goodbye Sir! Have a great day from {GLOBAL_CONFIG['JARVIS_NAME']}!")
                    break # Exit the loop
            
            elif action_type == "open_url":
                friendly_name = user_command_raw.replace("open ", "").strip()
                open_url(target, friendly_name)

            elif action_type == "open_app":
                fallback_exe = action.get("fallback_target_exe")
                friendly_name = user_command_raw.replace("open ", "").strip()
                open_application(target, friendly_name, fallback_exe)

            elif action_type == "close_app":
                friendly_name = user_command_raw.replace("close ", "").strip()
                close_application(target, friendly_name)
            
            elif action_type == "close_active_window":
                close_active_window()

            elif action_type == "info_query":
                if target == "time":
                    current_time_str = datetime.datetime.now().strftime("%I:%M %p")
                    speak(f"The current time is {current_time_str}, Sir.")
                elif target == "date":
                    current_date_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
                    speak(f"Today's date is {current_date_str}, Sir.")
                elif target == "day":
                    current_day_str = datetime.datetime.now().strftime("%A")
                    speak(f"Today is {current_day_str}, Sir.")
                elif target == "weather":
                    get_weather(GLOBAL_CONFIG["CITY_NAME"])

            elif action_type == "dynamic_search":
                perform_dynamic_search(user_command_raw, action["engine"])

            elif action_type == "gemini_query":
                query_for_gemini = user_command_raw.replace(matched_command_key, "").strip()
                if query_for_gemini:
                    ask_gemini(query_for_gemini)
                else:
                    speak(f"What would you like to ask {GLOBAL_CONFIG['JARVIS_NAME']}, Sir?")
                    follow_up_query = listen_command(prompt="Listening for your question...")
                    if follow_up_query:
                        ask_gemini(follow_up_query)
                    else:
                        speak(f"No question provided, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} is aborting Gemini query.")
            
            elif action_type == "memory_command":
                memory_action = action["action"]
                if memory_action == "add":
                    speak(f"What do you want {GLOBAL_CONFIG['JARVIS_NAME']} to remember, Sir?")
                    note_to_add = listen_command(prompt="Listening for your note...")
                    if note_to_add:
                        add_to_memory(note_to_add)
                    else:
                        speak(f"No note provided, Sir. Nothing added to {GLOBAL_CONFIG['JARVIS_NAME']}'s memory.")
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
                        speak(f"Which category of notes would you like {GLOBAL_CONFIG['JARVIS_NAME']} to read, Sir?")
                        category_to_read = listen_command(prompt="Listening for category...")
                    
                    if category_to_read:
                        read_memory(category=category_to_read)
                    else:
                        speak(f"No category provided, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} cannot filter notes without a category.")
            
        else:
            # Fallback: If no specific command is fuzzy-matched,
            # send the raw user input to Gemini for a general answer.
            speak(f"I didn't recognize that command specifically, Sir. Let {GLOBAL_CONFIG['JARVIS_NAME']} try asking Gemini.")
            ask_gemini(user_command_raw)

# Entry point of the script
if __name__ == "__main__":
    main()