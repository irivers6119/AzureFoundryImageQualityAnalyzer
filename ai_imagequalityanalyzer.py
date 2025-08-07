from openai import AzureOpenAI
import os
import json
import datetime
from dotenv import load_dotenv


load_dotenv()

class OpenAIChatSession():
    """
    A class to manage a chat session with the Azure OpenAI service.

    This class provides methods to set up a chat session with the Azure OpenAI API, send messages,
    receive responses, and manage conversation history. It supports setting system messages,
    adding and clearing user messages, and saving the conversation history to a file.

    Attributes:
        endpoint (str): The endpoint for the Azure OpenAI API.
        api_key (str): The API key for accessing the Azure OpenAI service.
        api_version (str): The API version to use.
        client (AzureOpenAI): The Azure OpenAI client initialized with the API key, endpoint, and version.
        model (str): The model to use for the chat session. Default is 'skillstorm-gpt4o'.
        temperature (float): The temperature for the response. Default is 1.
        max_tokens (int): The maximum number of tokens for the response. Default is 1000.
        top_p (float): The top_p value for nucleus sampling. Default is 0.95.
        frequency_penalty (float): The frequency penalty for the response. Default is 0.
        presence_penalty (float): The presence penalty for the response. Default is 0.
        stop (list or None): The stop sequence(s) for the response. Default is None.
        system_message (str): The initial system message to set the context for the chat session.
        total_tokens (int): The total number of tokens used in the chat session.
        last_prompt (str): The last prompt sent to the API.
        last_response (str): The last response received from the API.
        messages (list): A list of messages exchanged in the chat session.

    Methods:
        set_system_message(message):
            Sets the system message for the chat session.

        add_message(message, role='user'):
            Adds a message to the conversation history.

        clear_messages():
            Clears all messages and resets the conversation history with the system message.

        chat(prompt):
            Sends a prompt to the Azure OpenAI API and processes the response.

        start():
            Starts an interactive chat session, allowing user input from the console.

        save():
            Saves the conversation history to a file in JSON format.
    """

    def __init__(self, model='gpt-4o'):
        self.endpoint = os.environ.get('AOAI_ENDPOINT')
        self.api_key = os.environ.get('AOAI_KEY')
        self.api_version = '2024-12-01-preview'

        if not self.endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint or API key not set in environment variables.")

        try:
            self.client = AzureOpenAI(
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
                api_key=self.api_key
            )
        except Exception as e:
            print(f"Error initializing AzureOpenAI client: {e}")
            raise

        # Chat Settings
        self.model = model
        self.temperature = 1
        self.max_tokens = 1000 #response length
        self.top_p = 0.95
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.stop = None
        self.system_message = "You are an expert photographer of interior and exterior vehicle images who helps businesses identify the condition of vehicles to get the best assessment and value. Responses should be quantifiable and specific. Evaluate the quality of images using the following Parameters:\n"
        "Brightness: Overall lightness of the image.\n"
        "Graininess: Presence of visual noise or texture irregularities.\n"
        "Exposure: Balance of light and dark areas.\n"
        "Blurriness: Sharpness and clarity of image details.\n"
        "Scoring Criteria:\n"
        "Each parameter should be scored on a scale from 1 (worst) to 10 (best).\n"
        "If all four scores are below 6, classify each image as bad and recommend a retake. "
        "Else, determine the image is of good quality. Return in the response, the score for each parameter and the final decision."

        # Prompt Management Variables
        self.total_tokens = 0
        self.last_prompt = ""
        self.last_response = ""

        # Construct the initial messages
        self.messages = []
        self.add_message(message=self.system_message, role='system')

        # Load image paths at session start
        self.image_paths = []
        self.load_images()

    def load_images(self):
        """
        Loads all image files from the 'images' directory, reads each as bytes, encodes to base64, and decodes to utf-8.
        Stores a list of dicts: { 'path': ..., 'base64': ... }
        """
        import base64
        images_dir = os.path.join(os.path.dirname(__file__), 'images')
        self.image_paths = []
        try:
            if not os.path.isdir(images_dir):
                print(f"Images directory not found: {images_dir}")
                return
            exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
            for fname in os.listdir(images_dir):
                if fname.lower().endswith(exts):
                    img_path = os.path.join(images_dir, fname)
                    try:
                        with open(img_path, "rb") as img_file:
                            img_bytes = img_file.read()
                            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                            self.image_paths.append({"path": img_path, "base64": img_b64})
                    except Exception as img_e:
                        print(f"Error reading image {img_path}: {img_e}")
            if not self.image_paths:
                print("Warning: No images found in the directory.")
            else:
                print(f"Loaded {len(self.image_paths)} images from {images_dir}")
        except Exception as e:
            print(f"Error loading images: {e}")
            self.image_paths = []

    def set_system_message(self, message):
        self.system_message = message
        self.messages[0] = {"role": "system", "content": message}

    def add_message(self, message=None, role='user'):
        if role == 'user':
            if message is None or message.strip() == "":
                message = (
                    "Evaluate the quality of images using the following Parameters:\n"
                    "Brightness: Overall lightness of the image.\n"
                    "Graininess: Presence of visual noise or texture irregularities.\n"
                    "Exposure: Balance of light and dark areas.\n"
                    "Blurriness: Sharpness and clarity of image details.\n"
                    "Scoring Criteria:\n"
                    "Each parameter should be scored on a scale from 1 (worst) to 10 (best).\n"
                    "If all four scores are below 6, classify each image as bad and recommend a retake. "
                    "Else, determine the image is of good quality. Return in the response, the score for each parameter and the final decision."
                )
        self.messages.append({"role": role, "content": message})

    def clear_messages(self):
        self.messages = []
        self.add_message(role="system", message=self.system_message)

    def chat(self, prompt):
        if not self.image_paths:
            print("No images loaded. Cannot proceed with chat.")
            return

        results = []
        for img in self.image_paths:
            # img is a dict: { 'path': ..., 'base64': ... }
            img_b64 = img["base64"]
            img_path = img["path"]
            # Compose the message with text and image_url
            user_message = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                    }
                }
            ]
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_message}
            ]
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty,
                    stop=self.stop
                )
                response_text = response.choices[0].message.content
                self.last_prompt = prompt
                self.last_response = response_text
                self.total_tokens += response.usage.total_tokens
                print(f"Azure OpenAI response for {img_path}: {response_text}")
                self.add_message(role='assistant', message=response_text)
                results.append({"image": img_path, "response": response_text})
            except Exception as e:
                print(f"Error processing image {img_path}: {e}")
                results.append({"image": img_path, "response": f"Error: {e}"})

        return results

    def start(self):
        print(f"Starting a chat session with the {self.model} model. Type 'exit', 'quit', or 'stop' to end the session. \
                Type 'save' to write the conversation to a file.")
        self.clear_messages()
        while True:
            next_message = input("User: ")
            if next_message.strip().lower() in ['exit', 'quit', 'stop']:
                print("Exiting...")
                break
            if next_message.strip().lower() == 'save':
                self.save()
                print("Saving session...")
                continue
            self.chat(next_message)
        
    def save(self, results=None):
        path = os.path.dirname(__file__)
        base_path = os.path.split(path)[0]
        now = datetime.datetime.now()
        file_name = f"{now.strftime('%Y%m%d %H-%M-%S')} Session Messages.json"
        file_path = os.path.join(base_path, 'imagequalityanalyzer', 'output', file_name)
        try:
            with open(file_path, 'w') as f:
                if results:
                    f.write(json.dumps(results, indent=4))
                else:
                    f.write(json.dumps(self.messages, indent=4))
            print(f"Session saved to {file_path}")
        except Exception as e:
            print(f"Error saving session: {e}")


if __name__ == "__main__":
    chat = OpenAIChatSession()
    chat.start()
