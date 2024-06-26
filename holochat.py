import tkinter as tk
from tkinter import scrolledtext, simpledialog
import apsw
import json
import signal
import sys
import time
import random
import os
from cryptography.fernet import Fernet
import gensim
from gensim.models import Word2Vec
import numpy as np

# Constants
API_KEY_FILE = "api_key.txt"
CONFIG_FILE = ".config"
DB_FILE = "qa_data.db"
TABLE_NAME = "qa_data"
ENCRYPTION_KEY_FILE = "secret.key"
PASSWORD_FILE = "password.txt"

def load_encryption_key():
    """Load the encryption key from a file."""
    try:
        with open(ENCRYPTION_KEY_FILE, "rb") as key_file:
            return Fernet(key_file.read())
    except FileNotFoundError:
        print(f"Encryption key file '{ENCRYPTION_KEY_FILE}' not found.")
        raise

def encrypt_data(data, fernet):
    """Encrypt the data."""
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data, fernet):
    """Decrypt the data."""
    return fernet.decrypt(data.encode()).decode()

def load_config():
    """Load configuration settings from a file."""
    default_config = {
        "teaching_enabled": True,
        "specific_question": "What is the answer to life, the universe, and everything?"
    }
    try:
        if not os.path.exists(CONFIG_FILE):
            save_config(default_config)
            return default_config
        with open(CONFIG_FILE, "r") as config_file:
            return json.load(config_file)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading configuration: {str(e)}")
        save_config(default_config)
        return default_config

def save_config(config):
    """Save configuration settings to a file."""
    try:
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(config, config_file)
    except IOError as e:
        print(f"Error saving configuration: {str(e)}")

def print_typing_message(output_text, response_length):
    """Print a simulated typing message based on response length."""
    min_duration = 0.5
    max_duration = 2.0
    per_char_duration = 0.05
    typing_duration = min(max(min_duration + response_length * per_char_duration, min_duration), max_duration)
    output_text.insert(tk.END, "holo is typing...")
    output_text.update()
    time.sleep(typing_duration)
    output_text.delete("end - 1 chars", tk.END)  # Remove "..." from the output text

def handle_specific_question(output_text, config):
    """Handle the specific question with a predefined response and file generation."""
    output_text.insert(tk.END, "That is the right question!\n")
    file_content = "example content"
    file_name = "example.txt"
    try:
        with open(file_name, "w") as file:
            file.write(file_content)
        output_text.insert(tk.END, f"Text file '{file_name}' created in the current directory.\n")
    except IOError as e:
        output_text.insert(tk.END, f"Error creating text file: {str(e)}\n")

def handle_unknown_question(output_text, question, cursor, config, word2vec_model):
    """Handle unknown questions by asking the user for possible answers or using machine learning."""
    try:
        if config["teaching_enabled"]:
            output_text.insert(tk.END, "I don't know the answer to that. Can you teach me?\n")
            possible_answers = simpledialog.askstring("Teach Me", "Enter possible answers separated by a unique delimiter (e.g., ';'):")
            if possible_answers:
                possible_answers_list = [ans.strip() for ans in possible_answers.split(";")]
                for answer in possible_answers_list:
                    cursor.execute(f"INSERT OR IGNORE INTO {TABLE_NAME} (question, answer) VALUES (?, ?)", (question.lower(), answer))
                output_text.insert(tk.END, "Thank you for teaching me!\n")
            else:
                output_text.insert(tk.END, "No answers provided.\n")
        else:
            similar_pair = find_most_similar_pair(question, qa_pairs, word2vec_model)
            if similar_pair:
                _, response = similar_pair
                output_text.insert(tk.END, f"You: {question}\n")
                print_typing_message(output_text, len(response))
                output_text.insert(tk.END, f"holo: {response}\n")
            else:
                output_text.insert(tk.END, "I'm sorry, my responses are limited. You must ask the right questions.\n")
    except Exception as e:
        output_text.insert(tk.END, f"Error handling unknown question: {str(e)}\n")

def bot_response(output_text, question, cursor, config, word2vec_model):
    """Generate a response to a given question."""
    try:
        cursor.execute(f"SELECT answer FROM {TABLE_NAME} WHERE question=?", (question.lower(),))
        results = cursor.fetchall()
        if results:
            response = random.choice([result[0] for result in results])
            output_text.insert(tk.END, f"You: {question}\n")
            print_typing_message(output_text, len(response))
            output_text.insert(tk.END, f"Holo: {response}\n")
        elif question.lower() == config["specific_question"].lower():
            handle_specific_question(output_text, config)
        else:
            handle_unknown_question(output_text, question, cursor, config, word2vec_model)
    except Exception as e:
        output_text.insert(tk.END, f"Error generating bot response: {str(e)}\n")

def signal_handler(sig, frame):
    """Handle termination signal to save config and close database."""
    try:
        save_config(config)
        if connection:
            connection.close()
        sys.exit(0)
    except Exception as e:
        print(f"Error handling termination signal: {str(e)}")
        sys.exit(1)

def password_check(fernet, root, output_text):
    """Check for the correct password."""
    try:
        with open(PASSWORD_FILE, "r") as file:
            encrypted_password = file.read().strip()
        password = simpledialog.askstring("Password", "Enter password:", show='*')
        decrypted_password = decrypt_data(encrypted_password, fernet)
        if password != decrypted_password:
            output_text.insert(tk.END, "Incorrect password. Exiting...\n")
            time.sleep(2)
            sys.exit(0)
    except Exception as e:
        output_text.insert(tk.END, f"An error occurred during password verification: {str(e)}\n")
        time.sleep(2)
        sys.exit(1)

def train_word2vec_model(qa_pairs):
    """Train Word2Vec model on the questions."""
    try:
        sentences = [question.lower().split() for question, _ in qa_pairs]
        model = Word2Vec(sentences, vector_size=100, window=5, min_count=1, workers=4)
        return model
    except Exception as e:
        print(f"Error training Word2Vec model: {str(e)}")
        return None

def find_most_similar_pair(question, qa_pairs, word2vec_model):
    """Find the most similar question-answer pair using Word2Vec embeddings."""
    try:
        question_tokens = question.lower().split()
        max_similarity = -1
        most_similar_pair = None
        for q, a in qa_pairs:
            similarity = calculate_similarity(question_tokens, q.lower().split(), word2vec_model)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_pair = (q, a)
        return most_similar_pair
    except Exception as e:
        print(f"Error finding most similar pair: {str(e)}")
        return None

def calculate_similarity(tokens1, tokens2, word2vec_model):
    """Calculate similarity between two sets of tokens using Word2Vec."""
    try:
        vec1 = np.mean([word2vec_model.wv[word] for word in tokens1 if word in word2vec_model.wv], axis=0)
        vec2 = np.mean([word2vec_model.wv[word] for word in tokens2 if word in word2vec_model.wv], axis=0)
        if vec1.shape == () or vec2.shape == ():
            return 0.0
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    except Exception as e:
        print(f"Error calculating similarity: {str(e)}")
        return 0.0

# Initialize GUI
root = tk.Tk()
root.title("Holochat")
root.geometry("700x400")  # Set default size

# Text area for displaying conversation
output_text = scrolledtext.ScrolledText(root, width=80, height=20, wrap=tk.WORD)
output_text.grid(column=0, row=0, padx=10, pady=10, columnspan=2)

# Input field for user input
input_field = tk.Entry(root, width=80)
input_field.grid(column=0, row=1, padx=10, pady=10)

# Initialize connection variable
connection = None

# Function to handle user input
def handle_input(event=None):
    global connection, cursor, config, word2vec_model  # Ensure we use the global variables

    user_input = input_field.get()
    if user_input.lower() == "secret":
        password_check(fernet, root, output_text)
    elif user_input.lower() == "toggle teaching":
        config["teaching_enabled"] = not config["teaching_enabled"]
        save_config(config)
        output_text.insert(tk.END, f"Teaching mode is now {'enabled' if config['teaching_enabled'] else 'disabled'}\n")
    else:
        bot_response(output_text, user_input, cursor, config, word2vec_model)
    input_field.delete(0, tk.END)

# Bind Enter key to handle_input function
root.bind('<Return>', handle_input)

# Button to submit user input
submit_button = tk.Button(root, text="Submit", command=handle_input)
submit_button.grid(column=1, row=1, padx=10, pady=10)

# Welcome message in the text area
output_text.insert(tk.END, "Start a conversation with me.\n")

# Load encryption key
try:
    fernet = load_encryption_key()

    # Load the API key
    with open(API_KEY_FILE, "r") as file:
        encrypted_api_key = file.read().strip()
        api_key = decrypt_data(encrypted_api_key, fernet)

    # Connect to the SQLite database
    connection = apsw.Connection(DB_FILE)
    cursor = connection.cursor()

    # Create the table if not exists
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {TABLE_NAME} (question TEXT, answer TEXT)''')

    # Load configuration
    config = load_config()

    # Load existing Q&A pairs
    cursor.execute(f"SELECT question, answer FROM {TABLE_NAME}")
    qa_pairs = cursor.fetchall()

    # Train Word2Vec model
    word2vec_model = train_word2vec_model(qa_pairs)

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Start the GUI main loop
    root.mainloop()

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    # Ensure proper cleanup
    try:
        save_config(config)
        if connection:
            connection.close()
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
