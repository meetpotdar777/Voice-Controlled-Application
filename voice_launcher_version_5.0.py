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

# --- GLOBAL CONFIGURATION (IMPORTANT: Customize these values) ---
GLOBAL_CONFIG = {
    "CITY_NAME": "Australia",  # Your city name for weather queries
    "OPENWEATHERMAP_API_KEY": "PASTE_YOUR_API_KEY", # Get from openweathermap.org
    "GEMINI_API_KEY": "PASTE_YOUR_API_KEY", # Get from console.cloud.google.com (Generative Language API)
    "GEMINI_MODEL_NAME": "gemini-1.5-flash", # Changed to a commonly supported model. You can try 'gemini-1.5-pro' if preferred.
    "VOICE_GENDER": "male", # Options: "male", "female", or "default"
    "SPEECH_RATE": 170, # Words per minute (adjust as desired)
    "MEMORY_FILE": "jarvis_memory.txt" # File to store notes/ideas
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
        
        # Test Gemini model availability and set it
        # The API often prepends "models/" to the name, but sometimes it's optional.
        # We will try with and without the prefix.
        chosen_model_name = GLOBAL_CONFIG["GEMINI_MODEL_NAME"]
        
        # Add a check for available models for robustness
        available_models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        
        if chosen_model_name in available_models:
            gemini_model = genai.GenerativeModel(chosen_model_name)
        elif f"models/{chosen_model_name}" in available_models:
            gemini_model = genai.GenerativeModel(f"models/{chosen_model_name}")
        else:
            print(f"Error: Configured Gemini model '{chosen_model_name}' not found or does not support 'generateContent'.")
            print("Available models supporting 'generateContent':", available_models)
            if available_models:
                # Fallback to the first available generateContent model if preferred isn't found
                fallback_model = available_models[0]
                speak(f"Falling back to model {fallback_model} for Gemini features.")
                gemini_model = genai.GenerativeModel(fallback_model)
                print(f"Successfully configured Gemini with fallback model: {fallback_model}")
            else:
                print("No Gemini models found supporting 'generateContent'. Gemini features will be unavailable.")

        if gemini_model:
            print(f"Gemini API configured successfully with model: {gemini_model.model_name}.")
        else:
            print("Gemini features will be unavailable.")

    except Exception as e:
        print(f"Error configuring Gemini API: {e}. Gemini features will be unavailable.")
else:
    print("Warning: GEMINI_API_KEY not found or is default. Gemini features will be unavailable.")

# --- Define the COMMANDS dictionary ---
# IMPORTANT: Update application paths/process names to match your system exactly.
COMMANDS = {
    # Assistant Commands
    "hello jarvis": {"type": "assistant_command", "target": "greet"},
    "how are you": {"type": "assistant_command", "target": "status"},
    "exit": {"type": "assistant_command", "target": "exit"},
    "quit": {"type": "assistant_command", "target": "exit"},
    "goodbye": {"type": "assistant_command", "target": "exit"},

    # URL Opening Commands
    "open google": {"type": "open_url", "target": "https://www.google.com"},
    "open youtube": {"type": "open_url", "target": "https://www.youtube.com"}, # Corrected YouTube URL
    "open github": {"type": "open_url", "target": "https://github.com"},
    "open linkedin": {"type": "open_url", "target": "https://www.linkedin.com"},

    # Application Opening Commands (Windows specific paths or common .exe names)
    # IMPORTANT: Verify 'target' is the exact process name or full path.
    # 'fallback_target_exe' is for more friendly `start` command if direct `target` fails.
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

    # Memory Commands
    "remember this": {"type": "memory_command", "action": "add"},
    "take a note": {"type": "memory_command", "action": "add"},
    "store this": {"type": "memory_command", "action": "add"},
    "what do you remember": {"type": "memory_command", "action": "read"},
    "read my notes": {"type": "memory_command", "action": "read"},
    "show my notes": {"type": "memory_command", "action": "read"},
}

# --- Speech Functions ---
def speak(text):
    """Converts text to speech using the initialized engine."""
    print(f"Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()

def listen_command(prompt="Listening..."):
    """Listens for a command from the microphone."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(prompt)
        r.pause_threshold = 0.8
        r.energy_threshold = 4000 # Adjust this value if it's too sensitive or not sensitive enough
        r.dynamic_energy_threshold = True
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
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
        print(f"Best fuzzy match: '{best_match}' with score {score}")
        return best_match
    else:
        print(f"No strong command match found for '{user_input}' (score: {score})")
        return None

# --- Core Action Functions ---
def open_url(url, command_name_for_feedback):
    """Opens a URL in the default web browser."""
    speak(f"Opening {command_name_for_feedback}.")
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
        speak(f"{command_name_for_feedback} opened.")
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
                speak(f"{command_name_for_feedback} opened.")
            except Exception as e:
                speak(f"I couldn't open {command_name_for_feedback}. Error: {e}")
                print(f"Failed to open {command_name_for_feedback} via fallback: {e}")
        else:
            speak(f"I'm sorry, I couldn't find {command_name_for_feedback} to open.")
            print(f"No fallback provided for {app_target}.")
    except Exception as e:
        speak(f"An error occurred while trying to open {command_name_for_feedback}.")
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
                    speak(f"Attempting to terminate {command_name_for_feedback} (PID: {proc.pid}).")
                    proc.terminate()
                    proc.wait(timeout=3)
                    if proc.is_running():
                        proc.kill()
                    found_and_attempted = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if found_and_attempted:
            speak(f"{command_name_for_feedback} close attempt completed.")
        else:
            speak(f"Could not find any running instances of {command_name_for_feedback} to close.")
        return

    speak(f"Attempting to close {command_name_for_feedback}...")
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
                    
                    speak(f"Found {proc.info['name']} (PID: {proc.pid}). Attempting graceful termination...")
                    proc.terminate()
                    proc.wait(timeout=3)
                    
                    if proc.is_running():
                        speak(f"Still running. Force killing {proc.info['name']} (PID: {proc.pid}).")
                        proc.kill()
                    
                    closed_any = True

        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            speak(f"Access denied to close {proc.info['name']}. Please try running Jarvis as administrator for this command.")
            print(f"AccessDenied: Could not terminate process {proc.info['name']} (PID: {proc.pid}).")
            closed_any = True
            continue
        except Exception as e:
            print(f"Error while trying to close {proc.info['name']} (PID: {proc.pid}): {e}")
            continue

    if closed_any:
        speak(f"{command_name_for_feedback} close attempt completed.")
        final_check_running = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == process_name_to_close_lower:
                final_check_running = True
                break
        
        if final_check_running:
            speak(f"Some instances of {command_name_for_feedback} might still be running.")
        else:
            speak(f"{command_name_for_feedback} closed successfully.")
            print(f"Successfully closed: {process_name_to_close}")
    else:
        speak(f"Could not find any running instances of {command_name_for_feedback} to close, or it's a non-closable system process.")
        print(f"No running instances found or not closable for: {process_name_to_close}")

def close_active_window():
    """Closes the currently active window on Windows."""
    if platform.system() != "Windows":
        speak("This command is only available on Windows.")
        return

    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            speak("Active window closed.")
            print("Active window closed.")
        else:
            speak("No active window found to close.")
            print("No active window found.")
    except Exception as e:
        speak(f"Could not close the active window. Error: {e}")
        print(f"Error closing active window: {e}")

def get_weather(city_name):
    """Fetches and speaks the current weather for the given city."""
    api_key = GLOBAL_CONFIG["OPENWEATHERMAP_API_KEY"]
    if not api_key or api_key == "YOUR_OPENWEATHERMAP_API_KEY":
        speak("My OpenWeatherMap API key is not configured. I cannot fetch weather information.")
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
            
            speak(f"The weather in {city_name} is currently {description}, with a temperature of {temperature:.1f} degrees Celsius and humidity of {humidity} percent.")
        elif data["cod"] == "404":
            speak(f"Sorry, I could not find weather information for {city_name}. Please check the city name.")
        else:
            speak("Sorry, I could not retrieve weather information at this time.")
            print(f"OpenWeatherMap API error: {data.get('message', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        speak("I cannot connect to the internet to get weather information. Please check your connection.")
    except Exception as e:
        speak("An error occurred while fetching weather information.")
        print(f"Weather error: {e}")

def ask_gemini(query):
    """Sends a query to the Gemini model and speaks the response."""
    if not gemini_model:
        speak("I cannot connect to the Gemini AI. My API key is not configured or an error occurred during setup.")
        return

    speak("Thinking...")
    try:
        response = gemini_model.generate_content(query)
        gemini_text_response = response.text
        speak(gemini_text_response)
    except Exception as e:
        speak("I'm sorry, I encountered an error trying to process your request with Gemini.")
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
    """Performs a dynamic search on Google or YouTube."""
    # This extracts the query part after the command, e.g., "search google for [query]"
    # It takes the part after the matched command.
    try:
        # Find where the command ends and the query begins
        command_phrase_end = ""
        if f" {search_engine_type} for" in user_command_raw:
            command_phrase_end = f" {search_engine_type} for"
        elif f" on {search_engine_type}" in user_command_raw:
            command_phrase_end = f" on {search_engine_type}"
        
        command_end_index = user_command_raw.find(command_phrase_end)

        if command_end_index != -1:
            query = user_command_raw[command_end_index + len(command_phrase_end):].strip()
        else:
            # Fallback for simple cases like "google [query]" if not caught by fuzzy match
            query = user_command_raw.replace("search", "").replace("find", "").replace(search_engine_type, "").replace("on", "").strip()

    except Exception:
        # Fallback for unexpected parsing issues
        query = user_command_raw.replace("search", "").replace("find", "").replace(search_engine_type, "").replace("on", "").replace("for", "").strip() # Added 'for'

    if not query:
        speak(f"What do you want me to search on {search_engine_type}?")
        follow_up_query = listen_command(prompt=f"Listening for your {search_engine_type} query...")
        if follow_up_query:
            query = follow_up_query
        else:
            speak("No search query provided. Aborting search.")
            return

    if search_engine_type == "google":
        search_url = f"https://www.google.com/search?q={query}"
        speak(f"Searching Google for {query}")
    elif search_engine_type == "youtube":
        search_url = f"https://www.youtube.com/results?search_query={query}" # Corrected Youtube URL
        speak(f"Searching YouTube for {query}")
    else:
        speak("I can only search on Google or YouTube at the moment.")
        return

    webbrowser.open(search_url)

# --- Memory Functions ---
def add_to_memory(note):
    """Adds a timestamped note to the memory file."""
    memory_file = GLOBAL_CONFIG["MEMORY_FILE"]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {note}\n")
        speak("I have remembered that.")
        print(f"Added to memory: {note}")
    except Exception as e:
        speak("Sorry, I could not save that to my memory.")
        print(f"Error writing to memory file: {e}")

def read_memory():
    """Reads and speaks the contents of the memory file."""
    memory_file = GLOBAL_CONFIG["MEMORY_FILE"]
    try:
        if not os.path.exists(memory_file) or os.stat(memory_file).st_size == 0:
            speak("I don't have anything in my memory yet.")
            print("Memory file is empty or does not exist.")
            return

        with open(memory_file, "r", encoding="utf-8") as f:
            notes = f.read()
            if notes.strip(): # Check if there's actual content after stripping whitespace
                speak("Here's what I have in my memory:")
                print("\n--- Jarvis's Memory ---")
                print(notes)
                print("-----------------------\n")
                # Option to speak a summary or the whole thing if not too long
                if len(notes) < 500: # Adjust character limit for speaking
                    speak(notes)
                else:
                    speak("My memory contains many entries. I've printed them to the console.")
            else:
                speak("My memory seems to be empty.")
                print("Memory file is empty after reading.")

    except Exception as e:
        speak("Sorry, I encountered an error trying to read my memory.")
        print(f"Error reading memory file: {e}")


# --- Main Logic ---
def main():
    speak("Hello Sir. Jarvis at your service.")
    speak("What can I do for you?")

    while True:
        user_command_raw = listen_command()
        if not user_command_raw:
            continue

        matched_command_key = find_best_command(user_command_raw)

        if matched_command_key:
            action = COMMANDS[matched_command_key]
            action_type = action["type"]
            target = action.get("target")
            
            # For feedback, strip the command phrase to get the "thing" being acted upon
            command_name_for_feedback = user_command_raw.replace("open ", "").replace("close ", "").strip()
            # For dynamic search, this needs more specific parsing as done in perform_dynamic_search

            if action_type == "assistant_command":
                if target == "greet":
                    speak("Hello, how can I help you today?")
                elif target == "status":
                    speak("I am fine, thank you. Ready to assist.")
                elif target == "exit":
                    speak("Goodbye Sir! Have a great day!")
                    break # Exit the loop
            
            elif action_type == "open_url":
                # Extract the friendly name for feedback (e.g., "Google" from "open google")
                friendly_name = user_command_raw.replace("open ", "").strip()
                open_url(target, friendly_name)

            elif action_type == "open_app":
                fallback_exe = action.get("fallback_target_exe")
                # Extract the friendly name for feedback (e.g., "Chrome" from "open chrome")
                friendly_name = user_command_raw.replace("open ", "").strip()
                open_application(target, friendly_name, fallback_exe)

            elif action_type == "close_app":
                # Extract the friendly name for feedback (e.g., "Chrome" from "close chrome")
                friendly_name = user_command_raw.replace("close ", "").strip()
                close_application(target, friendly_name)
            
            elif action_type == "close_active_window":
                close_active_window()

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
                    get_weather(GLOBAL_CONFIG["CITY_NAME"])

            elif action_type == "dynamic_search":
                perform_dynamic_search(user_command_raw, action["engine"])

            elif action_type == "gemini_query":
                # Extract the actual query for Gemini
                query_for_gemini = user_command_raw.replace(matched_command_key, "").strip()
                if query_for_gemini:
                    ask_gemini(query_for_gemini)
                else:
                    speak("What would you like to ask me?")
                    follow_up_query = listen_command(prompt="Listening for your question...")
                    if follow_up_query:
                        ask_gemini(follow_up_query)
                    else:
                        speak("No question provided. Aborting Gemini query.")
            
            elif action_type == "memory_command":
                memory_action = action["action"]
                if memory_action == "add":
                    # Prompt user for what to remember
                    speak("What do you want me to remember?")
                    note_to_add = listen_command(prompt="Listening for your note...")
                    if note_to_add:
                        add_to_memory(note_to_add)
                    else:
                        speak("No note provided. Nothing added to memory.")
                elif memory_action == "read":
                    read_memory()
            
        else:
            # Fallback: If no specific command is fuzzy-matched,
            # send the raw user input to Gemini for a general answer.
            # Be mindful of API costs if you enable this aggressively.
            speak("I didn't recognize that command specifically. Let me try asking Gemini.")
            ask_gemini(user_command_raw)

# Entry point of the script
if __name__ == "__main__":
    main()