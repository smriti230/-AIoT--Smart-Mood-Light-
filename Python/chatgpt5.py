import paho.mqtt.client as mqtt
import openai
import re
import speech_recognition as sr
import threading
import pyttsx3  # Import the pyttsx3 library

# Set up MQTT Broker details
broker_address = "broker.emqx.io"
broker_port = 1883
voice_command_topic = "voice_command_topic"

response_topic = "response_topic"
# MQTT topic for RGB values
rgb_values_topic = "rgb_values_topic"

# Set up OpenAI API key
openai.api_key = "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"


# Function to recognize speech using the microphone
def recognize_speech():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Say something:")
        audio = recognizer.listen(source)

    try:
        recognized_text = recognizer.recognize_google(audio)
        print("You said:", recognized_text)

        return recognized_text

    except sr.UnknownValueError:
        print("Speech Recognition could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Web Speech Recognition service; {e}")
    except:
        print("Unknow error")

# Function to process the AI model (OpenAI GPT-3)
def process_ai_model(voice_command):
    # Prepare the prompt for the OpenAI API

    prompt = f"""Convert the given text to a command among the following options:
    - Turn off the light
    - Turn on the light
    - Change the light to a specific color

    Text: {voice_command}

    Conditions:
    1. Find a specific color based on the text even if color is not directly mentioned.
    2. If the text contains a specific color, choose the command "Turn on [color] light".
    3. If the text contains the word "party" or "rainbow," choose the command "Turn on all hue lights."
    4. If the text mentions colors indirectly (e.g., sky-like, ocean-like, ocean blue , sea green ,midnight blue,navy blue ,navi blue ,etc .),
     map the keywords like (e.g sky ,ocean, sea, midnight,navy, navi etc) to colors and choose the closest matching color. Then, use the command "
     Turn on [keyword] [closest_color] or [colour] light."
    5. If the text contains the word "dim" and a color, choose the command "Turn on light [color] with reduced intensity."
    6. If the text does not contain any color, choose either "Turn off the light" or "Turn on the light" command.
    """

    # Call the OpenAI API to generate the AI response
    respond = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0
    )

    # Extract the generated text from the response
    generated_text = respond.choices[0].text.strip()

    # List of action-related keywords
    action_keywords = ["turn on", "turn off", "change", "set"]

    # Regular expression patterns to match color names
    color_patterns = {
        "red": r"\bred\b",
        "green": r"\bgreen\b",
        "blue": r"\bblue\b",
        "magenta": r"\bmagenta\b",
        "yellow": r"\byellow\b",
        "orange": r"\borange\b",
        "pink": r"\bpink\b",
        "light green": r"\blight\s*green\b",
        "sky blue": r"\bsky\s*blue\b",
        "purple": r"\bpurple\b",
        "cyan": r"\bcyan\b",
        "gold": r"\bgold\b",
        "brown": r"\bbrown\b",
        "teal": r"\bteal\b",
        "lavender": r"\blavender\b",
        "indigo": r"\bindigo\b",
        "maroon": r"\bmaroon\b",
        "lime": r"\blime\b",
        "olive": r"\bolive\b",
        "aqua": r"\baqua\b",
        "midnight blue": r"\bmidnight\s*blue\b",
        "ocean blue": r"\bocean\s*blue\b",
        "sea green": r"\bsea\s*green\b",
        "navy blue": r"\bnavy\s*blue\b",
        "crimson" : r"\bcrimson\s*red\b"
        # ... (other color patterns as before) ...
    }

    # Check if the generated_text contains any action-related keyword
    if any(keyword in generated_text.lower() for keyword in action_keywords):
        return generated_text

    # If no action-related keyword is found, extract color name using regular expressions
    extracted_color = None
    for color_name, pattern in color_patterns.items():
        if re.search(pattern, generated_text, re.IGNORECASE):
            extracted_color = color_name
            break

    # If no color is extracted and no action-related keyword is found, return the default action (turn off the light)
    if not extracted_color:
        return "Turn off the light"

    # If color is extracted, return the response
    return generated_text

# Function to extract color name from the generated text
def extract_color_name(generated_text):
    # Define a list of color names and their variations
    color_names = {
        "red": ["red"],
        "green": ["green"],
        "blue": ["blue"],
        "magenta": ["magenta"],
        "yellow": ["yellow"],
        "orange": ["orange"],
        "pink": ["pink"],
        "light green": ["light green", "lightgreen", "light-green"],
        "sky blue": ["sky blue", "skyblue", "sky-blue", "light blue"],
        "midnight blue": ["midnightblue" ,"midnight-blue" ,"midnightlikeblue" ,"midnight blue"],
        "aqua": ["aqua"],
        "cyan": ["cyan"],
        "lavender": ["lavender"],
        "indigo": ["indigo"],
        "maroon": ["maroon"],
        "lime": ["lime"],
        "gold": ["gold"],
        "teal": ["teal"],
        "purple": ["purple"],
        "olive": ["olive"],
        "ocean blue": ["oceanblue", "ocean" ,"ocean blue" ,"ocean view"],
        "sea green": ["seagreen","sea green" ,"sea-green"],
        "navy blue": ["navy blue" ,"navi blue" ,"navyblue","navy" ,"navi"],
        "crimson": ["crimson" , "crimson red" , "crimsonred"]
        # Add more colors and their variations as needed
    }

    color_name = None
    for name, variations in color_names.items():
        for variation in variations:
            if re.search(rf"\b{re.escape(variation)}\b", generated_text, re.IGNORECASE):
                color_name = name
                break

    # Additional logic to handle "dim" for all colors
    if "dim" in generated_text.lower() and color_name:
        color_name = "light " + color_name

    print("Extracted color name:", color_name)
    return color_name


# Function to generate RGB values based on the color name
def generate_rgb_values(generated_text):
    # Extract the color name from the generated text
    color_name = extract_color_name(generated_text)

    # Dictionary with predefined color names and their RGB values
    color_values = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "magenta": (255, 0, 255),
        "yellow": (255, 255, 0),
        "orange": (255, 69, 0),
        "pink": (255, 80, 80),
        "light green": (80, 250, 50),
        "sky blue": (135, 206, 250),
        "purple": (128, 0, 128),
        "cyan": (0, 139, 139),
        "gold": (255, 215, 0),
        "brown": (165, 42, 42),
        "teal": (0, 128, 128),
        "lavender": (230, 230, 250),
        "indigo": (75, 0, 130),
        "maroon": (128, 0, 0),
        "lime": (0, 128, 0),
        "olive": (128, 128, 0),
        "aqua": (0, 255, 255),
        "midnight blue": (25, 25, 112),
        "ocean blue": (0, 119, 190),
        "sea green": (20, 255, 105),
        "navy blue": (0,0,128),
        "crimson": (220,20,60)
        # Add more colors as needed
    }

    # Check if the color_name exists in the dictionary
    if color_name and color_name.lower() in color_values:
        return color_values[color_name.lower()]
    elif "turn on" in generated_text.lower():
        # Default to white color (255, 255, 255) if "turn on" is mentioned
        return (255, 255, 255)
    elif "turn off" in generated_text.lower():
        # Default to black color (0, 0, 0) if "turn off" is mentioned
        return (0, 0, 0)
    else:
        # Default to black color (0, 0, 0) for other cases
        return (0, 0, 0)


# MQTT client callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(voice_command_topic)



def text_to_speech(text):
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()

    # Set properties (optional)
    engine.setProperty("rate", 150)  # Speed of speech (words per minute)
    engine.setProperty("volume", 0.9)  # Volume level (0.0 to 1.0)

    # Preprocess the text to remove "Answer:" or any other prefix
    # You can add more prefixes to remove if needed
    prefixes_to_remove = ["Answer:"]
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()

    # Convert text to speech and play it
    engine.say(text)
    engine.runAndWait()




# Function to perform speech recognition in a separate thread
def perform_speech_recognition():
    while True:
        voice_command = recognize_speech()
        if voice_command:
            print("Received voice command:", voice_command)
            first_word = voice_command.split()[0].lower()

            # Check if the first word matches the "special_word"
            if first_word == "chat":  # Replace "special_word" with the desired word
                # Remove the special word from the voice command
                voice_command_without_special_word = ' '.join(voice_command.split()[1:])

                # If the text is empty after removing the special word, go for speech recognition again
                if not voice_command_without_special_word.strip():
                    print("No valid command. Trying speech recognition again.")
                    text_to_speech("No valid command. Please try again.")  # Provide voice feedback
                    continue

                # Process the voice command using the AI model (e.g., ChatGPT)
                response = process_ai_model(voice_command_without_special_word)
                print("AI Response:", response)
                # Provide voice feedback for AI response
                text_to_speech(response)


                # Extract color name from the generated text
                color_name = extract_color_name(response)
                print("Extracted color name:", color_name)

                # Generate RGB values based on the color name
                rgb_values = generate_rgb_values(response)
                print("Generated RGB values:", rgb_values)

                # Publish the AI-generated response to the response topic
                client.publish(response_topic, response)

                # Publish RGB values to the RGB values topic
                client.publish(rgb_values_topic, f"{rgb_values[0]},{rgb_values[1]},{rgb_values[2]}")
            else:
                print("Voice command does not contain the special word. Trying speech recognition again.")
                text_to_speech("No valid command. Please try again.")  # Provide voice feedback
# Create an MQTT client instance
client = mqtt.Client()

# Set up the callback functions
client.on_connect = on_connect
# No need to set client.on_message here, it will be handled later.

# Connect to the MQTT broker
client.connect(broker_address, broker_port)

# Start the MQTT loop to maintain the connection and handle callbacks
client.loop_start()

# Start the speech recognition thread
speech_thread = threading.Thread(target=perform_speech_recognition)
speech_thread.daemon = True  # The thread will terminate when the main program ends.
speech_thread.start()

# Loop indefinitely to keep the program running
while True:
    pass