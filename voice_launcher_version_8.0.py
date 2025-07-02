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

# For Volume Control (Windows specific - requires 'pycaw')
# You'll need to install it: pip install pycaw comtypes
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    from ctypes import cast, POINTER
    PYCAW_AVAILABLE = True
except ImportError:
    print("Warning: 'pycaw' not installed. Volume control commands will not work on Windows.")
    print("To install: pip install pycaw comtypes")
    PYCAW_AVAILABLE = False
except Exception as e:
    print(f"Error importing pycaw: {e}. Volume control commands may not work.")
    PYCAW_AVAILABLE = False


# --- GLOBAL CONFIGURATION (IMPORTANT: Customize these values) ---
GLOBAL_CONFIG = {
    "CITY_NAME": "Australia",  # Your city name for weather queries
    "OPENWEATHERMAP_API_KEY": "YOUR_OPENWEATHERMAP_API_KEY", # Get from openweathermap.org
    "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY", # Get from console.cloud.google.com (Generative Language API)
    "GEMINI_MODEL_NAME": "gemini-1.5-flash", # Changed to a commonly supported model. You can try 'gemini-1.5-pro' if preferred.
    "VOICE_GENDER": "male", # Options: "male", "female", or "default"
    "SPEECH_RATE": 170, # Words per minute (adjust as desired)
    "MEMORY_FILE": "jarvis_memory.json", # Changed to JSON file for structured memory
    "JARVIS_NAME": "Jarvis", # Define Jarvis's name
    "FUZZY_MATCH_THRESHOLD": 75 # Confidence score for command recognition (0-100)
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

    # System Control Commands (Volume)
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
            speak(f"I encountered an issue with your microphone, Sir. Please check its connection.")
            return ""

    try:
        command = r.recognize_google(audio, language='en-in').lower()
        print(f"[You Said]: {command}")
        return command
    except sr.UnknownValueError:
        print("[Speech Recognition] Sorry, I could not understand the audio.")
        # speak("Sorry, Sir, I couldn't understand that. Could you please repeat?") # Too frequent, remove for fluency
        return ""
    except sr.RequestError as e:
        print(f"[Speech Recognition] Could not request results from Google Speech Recognition service; {e}")
        speak(f"I'm sorry, Sir, I cannot connect to the speech recognition service at the moment. Please check your internet connection.")
        return ""

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
        speak(f"Opening {feedback_name} for you, Sir.")
        webbrowser.open(url)
        print(f"[Action] Successfully opened URL: {url}")
    except webbrowser.Error as e:
        speak(f"I'm sorry, Sir, I couldn't open {feedback_name}. Your default web browser might not be configured correctly.")
        print(f"[Error] Webbrowser error opening {url}: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred while trying to open {feedback_name}, Sir.")
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
        speak(f"{feedback_name} opened, Sir.")
    except FileNotFoundError:
        print(f"[Error] Application '{app_target}' not found directly.")
        if fallback_exe:
            try:
                speak(f"Trying to open {feedback_name} using a common system command, Sir.")
                if platform.system() == "Windows":
                    subprocess.Popen(['start', fallback_exe], shell=True, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
                elif platform.system() == "Linux":
                    subprocess.Popen(['xdg-open', fallback_exe])
                elif platform.system() == "Darwin": # macOS
                    subprocess.Popen(['open', '-a', fallback_exe])
                print(f"[Action] Attempted to start '{fallback_exe}' via system command.")
                speak(f"{feedback_name} opened, Sir.")
            except Exception as e:
                speak(f"I'm sorry, Sir, I couldn't open {feedback_name}. Error: {e}")
                print(f"[Error] Failed to open {feedback_name} via fallback: {e}")
        else:
            speak(f"I'm sorry, Sir, I couldn't find {feedback_name} to open and there's no fallback option.")
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
        speak(f"An error occurred while {GLOBAL_CONFIG['JARVIS_NAME']} was trying to find windows to close, Sir.")

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
                        speak(f"Still running. {GLOBAL_CONFIG['JARVIS_NAME']} is force killing {proc.info['name']} (PID: {proc.pid}).")
                        proc.kill()
                    
                    closed_any = True

        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            speak(f"Access denied to close {proc.info['name']}, Sir. Please try running {GLOBAL_CONFIG['JARVIS_NAME']} as administrator for this command.")
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
            speak(f"Some instances of {feedback_name} might still be running, Sir.")
            print(f"[Info] Some instances of {process_name_to_close} might still be running.")
        else:
            speak(f"{feedback_name} closed successfully, Sir.")
            print(f"[Action] Successfully closed: {process_name_to_close}")
    else:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} could not find any running instances of {feedback_name} to close, or it's a non-closable system process, Sir.")
        print(f"[Info] No running instances found or not closable for: {process_name_to_close}")

def close_active_window():
    """Closes the currently active window on Windows."""
    if platform.system() != "Windows":
        speak("This command is only available on Windows, Sir.")
        print("[Info] close_active_window is Windows-specific.")
        return

    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            window_title = win32gui.GetWindowText(hwnd)
            speak(f"Attempting to close '{window_title}', Sir.")
            win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            speak("Active window closed, Sir.")
            print(f"[Action] Active window '{window_title}' closed.")
        else:
            speak("No active window found to close, Sir.")
            print("[Info] No active window found.")
    except Exception as e:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} could not close the active window. Error: {e}")
        print(f"[Error] Error closing active window: {e}")

def set_system_volume(level=None, change_by=None, mute=False, unmute=False):
    """Controls system volume (Windows only using pycaw)."""
    if not PYCAW_AVAILABLE or platform.system() != "Windows":
        speak("I'm sorry, Sir, volume control is currently only supported on Windows with the 'pycaw' library installed.")
        print("[Info] Volume control unavailable: not Windows or pycaw not installed.")
        return

    try:
        devices = AudioUtilities.GetSpeakers() # Corrected line: removed extra space, fixed capitalization
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        if mute:
            if volume.GetMute() == 0: # If not already muted
                volume.SetMute(1, None)
                speak("Volume muted, Sir.")
                print("[Action] Volume muted.")
            else:
                speak("Volume is already muted, Sir.")
        elif unmute:
            if volume.GetMute() == 1: # If already muted
                volume.SetMute(0, None)
                speak("Volume unmuted, Sir.")
                print("[Action] Volume unmuted.")
            else:
                speak("Volume is not muted, Sir.")
        elif level is not None:
            # Convert percentage (0-100) to decibels (-65.25 to 0)
            # Volume.SetMasterVolumeLevel(dB, None)
            # volume.SetMasterVolumeLevelScalar(scalar, None) (0.0 to 1.0)
            scalar_level = max(0.0, min(1.0, float(level) / 100.0))
            volume.SetMasterVolumeLevelScalar(scalar_level, None)
            speak(f"Volume set to {int(scalar_level * 100)} percent, Sir.")
            print(f"[Action] Volume set to {int(scalar_level * 100)}%.")
        elif change_by is not None:
            current_scalar_volume = volume.GetMasterVolumeLevelScalar()
            new_scalar_volume = current_scalar_volume + (float(change_by) / 100.0)
            new_scalar_volume = max(0.0, min(1.0, new_scalar_volume))
            volume.SetMasterVolumeLevelScalar(new_scalar_volume, None)
            speak(f"Volume adjusted. Current volume is now {int(new_scalar_volume * 100)} percent, Sir.")
            print(f"[Action] Volume changed by {change_by}%. Current: {int(new_scalar_volume * 100)}%.")

    except Exception as e:
        speak(f"I encountered an error trying to control the volume, Sir. Error: {e}")
        print(f"[Error] Volume control error: {e}")


def get_weather(city_name):
    """Fetches and speaks the current weather for the given city."""
    api_key = GLOBAL_CONFIG["OPENWEATHERMAP_API_KEY"]
    if not api_key or api_key == "YOUR_OPENWEATHERMAP_API_KEY":
        speak(f"My OpenWeatherMap API key is not configured, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} cannot fetch weather information.")
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
            
            speak(f"The weather in {city_name} is currently {description}, with a temperature of {temperature:.1f} degrees Celsius and humidity of {humidity} percent, Sir.")
            print(f"[Action] Weather fetched for {city_name}: {description}, {temperature}°C, {humidity}% humidity.")
        else:
            speak(f"Sorry, Sir, {GLOBAL_CONFIG['JARVIS_NAME']} could not retrieve weather information for {city_name} at this time.")
            print(f"[API Error] OpenWeatherMap API error for {city_name}: {data.get('message', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        speak(f"I cannot connect to the internet to get weather information, Sir. Please check your connection.")
        print("[Network Error] No internet connection for OpenWeatherMap.")
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            speak(f"It seems my OpenWeatherMap API key is invalid, Sir. Please check its configuration.")
            print(f"[API Error] OpenWeatherMap API key invalid (401 error).")
        elif http_err.response.status_code == 404:
            speak(f"Sorry, Sir, {GLOBAL_CONFIG['JARVIS_NAME']} could not find weather information for {city_name}. Please check the city name.")
            print(f"[API Error] City not found (404 error) for {city_name}.")
        else:
            speak(f"An HTTP error occurred while fetching weather information: {http_err}, Sir.")
            print(f"[API Error] HTTP error fetching weather: {http_err}")
    except requests.exceptions.RequestException as req_err:
        speak(f"A general request error occurred while trying to get weather information: {req_err}, Sir.")
        print(f"[Network Error] General request error for OpenWeatherMap: {req_err}")
    except json.JSONDecodeError:
        speak(f"I received an unreadable response from the weather service, Sir.")
        print(f"[JSON Error] Could not decode JSON from OpenWeatherMap.")
    except Exception as e:
        speak(f"An unexpected error occurred while {GLOBAL_CONFIG['JARVIS_NAME']} was fetching weather information: {e}, Sir.")
        print(f"[Error] Weather fetching unexpected error: {e}")

def ask_gemini(query):
    """Sends a query to the Gemini model and speaks the response."""
    if not gemini_model:
        speak(f"I cannot connect to the Gemini AI, Sir. My API key is not configured or an error occurred during setup.")
        print("[Config Error] Gemini model not initialized.")
        return

    speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} is thinking...")
    try:
        response = gemini_model.generate_content(query)
        gemini_text_response = response.text
        speak(gemini_text_response)
        print(f"[Gemini Response] Query: '{query}' -> Response: '{gemini_text_response}'")
    except Exception as e:
        speak(f"I'm sorry, Sir, {GLOBAL_CONFIG['JARVIS_NAME']} encountered an error trying to process your request with Gemini.")
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
        speak(f"What exactly do you want {GLOBAL_CONFIG['JARVIS_NAME']} to search on {search_engine_type}, Sir?")
        follow_up_query = listen_command(prompt=f"Listening for your {search_engine_type} query...")
        if follow_up_query:
            query = follow_up_query
        else:
            speak(f"No search query provided, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} is aborting search.")
            print(f"[Info] Search aborted: no query provided for {search_engine_type}.")
            return

    try:
        if search_engine_type == "google":
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            speak(f"Searching Google for {query}, Sir.")
        elif search_engine_type == "youtube":
            search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}" # Corrected YouTube URL
            speak(f"Searching YouTube for {query}, Sir.")
        elif search_engine_type == "github":
            search_url = f"https://github.com/search?q={requests.utils.quote(query)}"
            speak(f"Searching GitHub for {query}, Sir.")
        else:
            speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} can only search on Google, YouTube, or GitHub at the moment, Sir.")
            print(f"[Info] Unsupported search engine requested: {search_engine_type}.")
            return

        webbrowser.open(search_url)
        print(f"[Action] Opened search URL: {search_url}")
    except webbrowser.Error as e:
        speak(f"I'm sorry, Sir, I couldn't open the search page. Your default web browser might be an issue.")
        print(f"[Error] Webbrowser error during search for '{query}' on {search_engine_type}: {e}")
    except Exception as e:
        speak(f"An unexpected error occurred during the search operation, Sir.")
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
        speak(f"Sir, my memory file seems corrupted. I'm starting with a fresh memory. Apologies for the inconvenience.")
        return []
    except Exception as e:
        print(f"[Memory Error] Error loading memory data for {GLOBAL_CONFIG['JARVIS_NAME']}: {e}")
        speak(f"An error occurred while loading my memories, Sir. Some data might be inaccessible.")
        return []

def save_memory_data(data):
    """Saves memory data to the JSON file."""
    memory_file = GLOBAL_CONFIG["MEMORY_FILE"]
    try:
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"[Memory] Memory saved successfully to '{memory_file}'.")
    except Exception as e:
        speak(f"Sorry, Sir, {GLOBAL_CONFIG['JARVIS_NAME']} could not save the memory data due to an error.")
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
        speak(f"What category does this note belong to, Sir? For example: idea, task, shopping list, or personal.")
        spoken_category = listen_command(prompt=f"Listening for category...")
        if spoken_category:
            category = spoken_category.lower().strip()
        else:
            speak(f"No category provided, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} will save it as 'uncategorized'.")
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
    print(f"[Memory Action] Added to memory (ID {new_id}, Category '{category}'): {note}")

def read_memory(category=None, summarize=False):
    """Reads and speaks the contents of the memory file, optionally by category or summarized."""
    memory_data = load_memory_data()

    if not memory_data:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} doesn't have anything in memory yet, Sir.")
        print("[Memory Action] No memory entries to read.")
        return

    filtered_notes = []
    if category:
        for entry in memory_data:
            if entry.get("category", "uncategorized").lower() == category.lower():
                filtered_notes.append(entry)
        
        if not filtered_notes:
            speak(f"I found no notes in the '{category}' category, Sir.")
            print(f"[Memory Action] No notes found in category '{category}'.")
            return
        speak(f"Here are your notes in the '{category}' category, Sir:")
        print(f"[Memory Action] Reading notes in category: '{category}'.")
    else:
        speak(f"Here is everything {GLOBAL_CONFIG['JARVIS_NAME']} has in memory, Sir:")
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
            speak(f"There is only one relevant entry, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} will read it directly.")
            speak(f"Note: {filtered_notes[0]['note']}")
    elif len(notes_text_for_display) < 1000 and len(filtered_notes) < 5: # Adjust character/count limit for speaking all
        speak(f"Here are the notes: {notes_text_for_display.replace('ID:', 'ID').replace('Category:', 'Category')}") # Speak cleaner version
    else:
        speak(f"Your memory contains many entries, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has printed them to the console for your review.")
        print(f"[Info] Memory too long to speak, printed to console.")


def forget_note(note_identifier=None):
    """Deletes a specific note by ID or a keyword/phrase."""
    memory_data = load_memory_data()

    if not memory_data:
        speak(f"{GLOBAL_CONFIG['JARVIS_NAME']} has no notes to forget, Sir.")
        print("[Memory Action] No notes to delete.")
        return

    if not note_identifier:
        speak(f"Which note would you like {GLOBAL_CONFIG['JARVIS_NAME']} to forget, Sir? Please tell me the ID number or a keyword from the note.")
        note_identifier = listen_command(prompt="Listening for note ID or keyword...")
        if not note_identifier:
            speak(f"No identifier provided, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} cannot forget a note without knowing which one.")
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
            speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten note with ID {note_id}.")
            print(f"[Memory Action] Deleted note with ID {note_id}: {found_notes[0]['note']}")
            return

    except ValueError:
        # Not an ID, try to delete by keyword/phrase
        speak(f"Searching for notes containing '{note_identifier}' to forget, Sir.")
        
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
            speak(f"I found no notes strongly matching '{note_identifier}' to forget, Sir.")
            print(f"[Memory Action] No strong match found for '{note_identifier}'. No notes deleted.")
            updated_memory_data = memory_data # Restore original if no match
        elif len(matching_entries) == 1:
            # If only one strong match, delete it
            save_memory_data(updated_memory_data)
            speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten the note: '{matching_entries[0]['note']}'.")
            print(f"[Memory Action] Deleted note by keyword: {matching_entries[0]['note']}")
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
                        found_notes.append(entry) # Keep track of what was found/deleted
                        deleted_one = True
                    else:
                        final_updated_memory.append(entry)
                
                if deleted_one:
                    save_memory_data(final_updated_memory)
                    speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has forgotten note with ID {clarification_id}.")
                    print(f"[Memory Action] Deleted note with ID {clarification_id}: {found_notes[0]['note'] if found_notes else ''}")
                else:
                    speak(f"I could not find a note with ID {clarification_id}, Sir. No notes were deleted.")
                    print(f"[Memory Action] No note found with ID {clarification_id}. Reverting changes.")
                    save_memory_data(memory_data) # Revert if no deletion
            except ValueError:
                speak(f"That was not a valid ID, Sir. No notes were deleted.")
                print("[Memory Action] Invalid ID provided for deletion.")
                save_memory_data(memory_data) # Revert if no deletion
            except Exception as e:
                speak(f"An error occurred during deletion, Sir. {e}")
                print(f"[Memory Error] Error during multi-match deletion: {e}")
                save_memory_data(memory_data) # Revert if error

    if len(memory_data) == initial_memory_count and not found_notes: # Final check if anything was actually deleted
        speak(f"I could not find any notes matching '{note_identifier}' to forget, Sir.")
        print(f"[Memory Action] No notes deleted after full attempt for '{note_identifier}'.")


def clear_all_memory():
    """Clears all notes from the memory file after confirmation."""
    speak(f"Are you sure you want {GLOBAL_CONFIG['JARVIS_NAME']} to clear all your memories, Sir? This action cannot be undone.")
    confirmation = listen_command(prompt="Say 'yes' to confirm or 'no' to cancel.")
    if "yes" in confirmation:
        save_memory_data([]) # Save an empty list
        speak(f"All memories have been cleared, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} has an empty slate.")
        print("[Memory Action] All memory cleared.")
    else:
        speak(f"Understood, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} will keep your memories intact.")
        print("[Memory Action] Memory clear action cancelled.")

# --- Main Logic ---
def main():
    speak(f"Hello Sir. {GLOBAL_CONFIG['JARVIS_NAME']} at your service.")
    speak("What can I do for you today, Sir?")

    while True:
        user_command_raw = listen_command()
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
                    speak(f"Hello, Sir. How can {GLOBAL_CONFIG['JARVIS_NAME']} assist you today?")
                elif target == "status":
                    speak(f"I am fine, thank you, Sir. {GLOBAL_CONFIG['JARVIS_NAME']} is ready to assist.")
                elif target == "exit":
                    speak(f"Goodbye Sir! Have a great day from {GLOBAL_CONFIG['JARVIS_NAME']}!")
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
                        speak("To what percentage would you like to set the volume, Sir?")
                        vol_str = listen_command(prompt="Listening for volume percentage...")
                        if vol_str and vol_str.isdigit():
                            vol_level = int(vol_str)
                            if 0 <= vol_level <= 100:
                                set_system_volume(level=vol_level)
                            else:
                                speak("Please provide a percentage between 0 and 100, Sir.")
                        else:
                            speak("I didn't catch a valid volume percentage, Sir.")
                    except Exception as e:
                        speak(f"An error occurred trying to set volume: {e}, Sir.")
                elif volume_action == "increase":
                    speak("By how much should I increase the volume, Sir? For example, by 10 or 20 percent.")
                    change_str = listen_command(prompt="Listening for volume increase amount...")
                    if change_str and change_str.isdigit():
                        change_amount = int(change_str)
                        set_system_volume(change_by=change_amount)
                    else:
                        speak("I didn't catch a valid increase amount, Sir.")
                elif volume_action == "decrease":
                    speak("By how much should I decrease the volume, Sir? For example, by 10 or 20 percent.")
                    change_str = listen_command(prompt="Listening for volume decrease amount...")
                    if change_str and change_str.isdigit():
                        change_amount = -int(change_str) # Negative for decrease
                        set_system_volume(change_by=change_amount)
                    else:
                        speak("I didn't catch a valid decrease amount, Sir.")
                elif volume_action == "mute":
                    set_system_volume(mute=True)
                elif volume_action == "unmute":
                    set_system_volume(unmute=True)


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
                # Pass matched_command_key here to help with precise query extraction
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
            speak(f"I didn't recognize '{user_command_raw}' specifically, Sir. Let {GLOBAL_CONFIG['JARVIS_NAME']} try asking Gemini.")
            ask_gemini(user_command_raw)

# Entry point of the script
if __name__ == "__main__":
    main()