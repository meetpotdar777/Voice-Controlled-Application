import speech_recognition as sr
import pyttsx3
import os
import platform
import subprocess
import webbrowser
import datetime # For potential future features like current time

# --- Configuration ---
# Define the commands and what they should open.
# Keys are the voice commands you'll say (lowercase).
# Values are dictionaries specifying the 'type' (website, application, command)
# and the 'target' (URL for websites, executable name/path for applications).
# For applications, prioritize the simple executable name if it's in your PATH.
# Otherwise, provide the full path using a raw string (r"C:\...")
COMMANDS = {
    # --- Websites ---
    "open chrome": {"type": "website", "target": "https://www.google.com"},
    "open google": {"type": "website", "target": "https://www.google.com"},
    "open browser": {"type": "website", "target": "https://www.google.com"}, # Alias for opening browser
    "open youtube": {"type": "website", "target": "https://www.youtube.com"}, # Corrected official YouTube URL
    "open wikipedia": {"type": "website", "target": "https://www.wikipedia.org"},
    "open github": {"type": "website", "target": "https://github.com"},
    "open stack overflow": {"type": "website", "target": "https://stackoverflow.com"},
    "open whatsapp web": {"type": "website", "target": "https://web.whatsapp.com/"},
    "open whatsapp": {"type": "website", "target": "https://web.whatsapp.com/"}, # Alias for whatsapp web
    "open amazon": {"type": "website", "target": "https://www.amazon.in"}, # Assuming India region
    "open flipkart": {"type": "website", "target": "https://www.flipkart.com"},

    # --- Windows Applications ---
    # Common built-in Windows applications (these should generally work)
    "open calculator": {"type": "application", "target": "calc.exe"},
    "open notepad": {"type": "application", "target": "notepad.exe"},
    "open command prompt": {"type": "application", "target": "cmd.exe"},
    "open powershell": {"type": "application", "target": "powershell.exe"},
    "open files": {"type": "application", "target": "explorer.exe"}, # Windows File Explorer
    "open paint": {"type": "application", "target": "mspaint.exe"},
    "open task manager": {"type": "application", "target": "taskmgr.exe"},
    "open settings": {"type": "application", "target": "ms-settings:"}, # Special URI for Windows settings
    "open setting": {"type": "application", "target": "ms-settings:"}, # Alias for settings
    "open wordpad": {"type": "application", "target": "wordpad.exe"},

    # Example for commonly installed applications (ADJUST PATHS IF THEY DON'T OPEN by name alone)
    # If the app is in your system's PATH, just the executable name is fine.
    # Otherwise, you need the full path, like r"C:\Program Files\YourApp\YourApp.exe"
    "open visual studio code": {"type": "application", "target": "code"},
    # Example for Spotify (REPLACE WITH YOUR ACTUAL PATH IF "spotify" doesn't work directly):
    # "open spotify": {"type": "application", "target": r"C:\Users\YOUR_USERNAME\AppData\Roaming\Spotify\Spotify.exe"},
    "open spotify": {"type": "application", "target": "spotify"}, # Keep this if 'spotify' works from command line
    "open discord": {"type": "application", "target": "discord"},
    "open zoom": {"type": "application", "target": "zoom"}, # Or full path to zoom.exe
    "open vlc": {"type": "application", "target": "vlc"}, # Or full path to vlc.exe
    "open firefox": {"type": "application", "target": "firefox.exe"}, # For Firefox on Windows

    # --- Special Commands for the Assistant Itself ---
    "exit": {"type": "command", "target": "exit"},
    "stop": {"type": "command", "target": "exit"}, # Alias for exit
    "quit": {"type": "command", "target": "exit"},  # Another alias for exit
    # "what time is it": {"type": "command", "target": "time"}, # Example for a custom command
}

# --- Initialize Speech Recognition and Text-to-Speech ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Configure voice properties (optional)
try:
    voices = engine.getProperty('voices')
    # Try to set a female voice if available, otherwise default to first voice
    female_voice_found = False
    for voice in voices:
        # Check for gender attribute (may not be available for all voices) or typical names
        if "female" in voice.name.lower() or "zira" in voice.name.lower() or "helen" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            female_voice_found = True
            break
    if not female_voice_found and len(voices) > 0:
        engine.setProperty('voice', voices[0].id) # Fallback to first available voice
except Exception as e:
    print(f"Could not set voice properties: {e}")

engine.setProperty('rate', 170)  # Speed of speech (words per minute)
engine.setProperty('volume', 1.0) # Volume (0.0 to 1.0)

def speak(text):
    """Converts text to speech and prints it."""
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

def listen_command():
    """Listens for a voice command and returns the recognized text."""
    with sr.Microphone() as source:
        print("\nListening for command...")
        recognizer.adjust_for_ambient_noise(source, duration=0.8) # Adjust for noise, slightly longer duration
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5) # Add timeout for better UX
        except sr.WaitTimeoutError:
            print("No speech detected within the timeout.")
            return ""

    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I could not understand your audio.")
        speak("Sorry, I didn't catch that. Please say your command again.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        speak("My speech recognition service is currently unavailable. Please check your internet connection.")
        return ""

def open_target(action_type, target, command_name_for_feedback):
    """Handles opening of websites and applications based on OS."""
    speak(f"Opening {command_name_for_feedback}...")
    try:
        if action_type == "website":
            webbrowser.open(target)
        elif action_type == "application":
            current_os = platform.system()
            if current_os == "Windows":
                # Use subprocess.Popen for more robust application launching.
                # 'start' command is needed for certain URIs like ms-settings:
                if target.startswith('ms-settings:'):
                    subprocess.Popen(['start', target], shell=True)
                else:
                    # For executables, try to run directly. shell=True can sometimes help
                    # but also carries security implications if target is user-controlled.
                    # For this use case, it's generally safe as targets are predefined.
                    subprocess.Popen(target, shell=True) # Using shell=True for broader compatibility with names/paths
            elif current_os == "Darwin": # macOS
                subprocess.Popen(["open", "-a", target])
            elif current_os == "Linux":
                subprocess.Popen([target]) # Assumes the application is in your PATH
            else:
                speak("Unsupported operating system for opening applications.")
                print(f"Error: Unsupported OS {current_os}")
                return
        print(f"Successfully attempted to open: {target}")
    except FileNotFoundError:
        speak(f"Sorry, I couldn't find the application '{command_name_for_feedback}'. Please ensure it's installed or in your system's PATH.")
        print(f"FileNotFoundError: Target '{target}' not found.")
    except Exception as e:
        speak(f"An error occurred while trying to open {command_name_for_feedback}. Please check the command configuration.")
        print(f"Error opening {command_name_for_feedback} ({target}): {e}")

def main():
    speak("Hello! I am your voice assistant. How can I help you today?")
    while True:
        command = listen_command()
        if not command:
            continue # If no command was recognized, listen again

        action = COMMANDS.get(command)

        if action:
            action_type = action["type"]
            target = action["target"]

            if action_type == "command":
                if target == "exit":
                    speak("Exiting the voice assistant. Goodbye!")
                    break
                # Add more custom commands here if needed, e.g.:
                # elif target == "time":
                #     current_time = datetime.datetime.now().strftime("%I:%M %p")
                #     speak(f"The current time is {current_time}")
            else:
                # Use the user's spoken command for feedback, rather than raw target name
                # Remove "open " prefix for cleaner feedback (e.g., "Opening youtube...")
                command_name_for_feedback = command.replace("open ", "")
                open_target(action_type, target, command_name_for_feedback)
        else:
            speak("I don't have a command for that. Please try another command.")

if __name__ == "__main__":
    main()