#!/usr/bin/env python3
import subprocess
import os
from flask import Flask, request, jsonify, send_from_directory
from markitdown import MarkItDown
from dotenv import load_dotenv
import io
import openai
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

app = Flask(__name__, static_folder='fe')

# Placeholder for personas
personas = [
    {"id": "persona1", "system_prompt": "You are a friendly chatbot.", "voice": "voice1"},
    {"id": "persona2", "system_prompt": "You are a sarcastic chatbot.", "voice": "voice2"},
    {"id": "persona3", "system_prompt": "You are a formal chatbot.", "voice": "voice3"},
]

# Placeholder for call data
call_data = {}

@app.route('/')
def index():
    return send_from_directory('fe', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('fe', path)

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    result = scrape_url(url)
    return jsonify({"result": result})

def scrape_url(url):
    try:
        # Execute the lightpanda command
        result = subprocess.run(['./lightpanda', 'fetch', '--dump', url], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Subprocess failed with error: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

def convert_to_markdown(html_content):
    md = MarkItDown()
    # MarkItDown expects a binary file-like object
    html_bytes = html_content.encode('utf-8')
    html_io = io.BytesIO(html_bytes)
    result = md.convert_stream(html_io)
    return result.text_content

def summarize(markdown_content, system_prompt):
    try:
        # Use chat completions instead of completions
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",  # Updated model name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize the following: {markdown_content}"}
            ],
            max_tokens=150,
            temperature=0.5,
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",  # Replace with your actual site
                "X-Title": "Party Line Game",
            }
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in summarize: {str(e)}")
        return f"Error generating summary: {str(e)}"

@app.route('/call', methods=['POST'])
def call():
    data = request.get_json()
    url = data['url']
    persona_ids = data['personas']

    # Scrape URL
    scraped_content = scrape_url(url)

    # Convert to markdown
    markdown_content = convert_to_markdown(scraped_content)

    # Get system prompts for selected personas
    system_prompts = [persona["system_prompt"] for persona in personas if persona["id"] in persona_ids]
    # Combine system prompts
    combined_system_prompt = "\n".join(system_prompts)

    # Summarize
    summary = summarize(markdown_content, combined_system_prompt)

    call_id = "12345"  # Placeholder
    call_data[call_id] = {"url": url, "personas": persona_ids, "content": summary}

    return jsonify({"id": call_id})

@app.route('/add_to_call', methods=['POST'])
def add_to_call():
    data = request.get_json()
    call_id = data['id']
    persona_id = data['persona']

    if call_id in call_data:
        call_data[call_id]['personas'].append(persona_id)
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid call ID"})

@app.route('/remove_from_call', methods=['POST'])
def remove_from_call():
    data = request.get_json()
    call_id = data['id']
    persona_id = data['persona']

    if call_id in call_data:
        call_data[call_id]['personas'] = [p for p in call_data[call_id]['personas'] if p != persona_id]
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid call ID"})

if __name__ == '__main__':
    app.run(debug=True)#!/usr/bin/env python3
import subprocess
import os
from flask import Flask, request, jsonify, send_from_directory
from markitdown import MarkItDown
from dotenv import load_dotenv
import io
import openai
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

app = Flask(__name__, static_folder='fe')

# Placeholder for personas
personas = [
    {"id": "persona1", "system_prompt": "You are a friendly chatbot.", "voice": "voice1"},
    {"id": "persona2", "system_prompt": "You are a sarcastic chatbot.", "voice": "voice2"},
    {"id": "persona3", "system_prompt": "You are a formal chatbot.", "voice": "voice3"},
]

# Placeholder for call data
call_data = {}

@app.route('/')
def index():
    return send_from_directory('fe', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('fe', path)

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    result = scrape_url(url)
    return jsonify({"result": result})

def scrape_url(url):
    try:
        # Execute the lightpanda command
        result = subprocess.run(['./lightpanda', 'fetch', '--dump', url], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Subprocess failed with error: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

def convert_to_markdown(html_content):
    md = MarkItDown()
    # MarkItDown expects a binary file-like object
    html_bytes = html_content.encode('utf-8')
    html_io = io.BytesIO(html_bytes)
    result = md.convert_stream(html_io)
    return result.text_content

def summarize(markdown_content, system_prompt):
    try:
        # Use chat completions instead of completions
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",  # Updated model name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize the following: {markdown_content}"}
            ],
            max_tokens=150,
            temperature=0.5,
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",  # Replace with your actual site
                "X-Title": "Party Line Game",
            }
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in summarize: {str(e)}")
        return f"Error generating summary: {str(e)}"

@app.route('/call', methods=['POST'])
def call():
    data = request.get_json()
    url = data['url']
    persona_ids = data['personas']

    # Scrape URL
    scraped_content = scrape_url(url)

    # Convert to markdown
    markdown_content = convert_to_markdown(scraped_content)

    # Get system prompts for selected personas
    system_prompts = [persona["system_prompt"] for persona in personas if persona["id"] in persona_ids]
    # Combine system prompts
    combined_system_prompt = "\n".join(system_prompts)

    # Summarize
    summary = summarize(markdown_content, combined_system_prompt)

    call_id = "12345"  # Placeholder
    call_data[call_id] = {"url": url, "personas": persona_ids, "content": summary}

    return jsonify({"id": call_id})

@app.route('/add_to_call', methods=['POST'])
def add_to_call():
    data = request.get_json()
    call_id = data['id']
    persona_id = data['persona']

    if call_id in call_data:
        call_data[call_id]['personas'].append(persona_id)
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid call ID"})

@app.route('/remove_from_call', methods=['POST'])
def remove_from_call():
    data = request.get_json()
    call_id = data['id']
    persona_id = data['persona']

    if call_id in call_data:
        call_data[call_id]['personas'] = [p for p in call_data[call_id]['personas'] if p != persona_id]
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid call ID"})

if __name__ == '__main__':
    app.run(debug=True)
