import os
import json
import requests
import argparse
from flask import Flask, request, jsonify
from jsonschema import validate, ValidationError

app = Flask(__name__)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--listen', default=os.environ.get('FLASK_RUN_PORT', '5003'))
    args, _ = parser.parse_known_args()
    return args

ARGS = get_args()

SCHEMA_SVC = os.environ.get('SCHEMA_SVC_URL', 'http://schema-service:5001')
VALUES_SVC = os.environ.get('VALUES_SVC_URL', 'http://values-service:5002')
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://host.docker.internal:11434')
MODEL_NAME = "llama3"

def query_ollama(prompt):
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json().get('response', '')
        return None
    except Exception:
        return None

def extract_app_name_jk(user_input):
    prompt = f"""
    Identify the application name from the user input.
    Options: [tournament, matchmaking, chat]
    User Input: "{user_input}"
    Return ONLY JSON: {{"app_name": "name"}}
    """
    response = query_ollama(prompt)
    if not response:
        return None
    try:
        clean = response.replace("```json", "").replace("```", "").strip()
        return json.loads(clean).get("app_name")
    except:
        return None

def process_config_update(user_input, current_values, schema):
    prompt = f"""
    Update the Configuration JSON based on User Request.
    User Request: "{user_input}"
    Current JSON: {json.dumps(current_values)}
    Schema Rules: {json.dumps(schema)}
    Instructions:
    1. Return the FULL updated JSON.
    2. Do not remove existing fields.
    3. Only change what is requested.
    4. Ensure valid JSON output.
    """
    response = query_ollama(prompt)
    if not response:
        return None
    try:
        clean = response.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return None

@app.route('/message', methods=['POST'])
def handle_message():
    data = request.json
    user_input = data.get('input')
    
    if not user_input:
        return jsonify({"error": "No input"}), 400

    app_name = extract_app_name_jk(user_input)
    if not app_name:
        return jsonify({"error": "App not found"}), 400

    try:
        s_res = requests.get(f"{SCHEMA_SVC}/{app_name}")
        v_res = requests.get(f"{VALUES_SVC}/{app_name}")
        
        if s_res.status_code != 200 or v_res.status_code != 200:
            return jsonify({"error": "Data missing"}), 404
            
        schema = s_res.json()
        values = v_res.json()
    except:
        return jsonify({"error": "Service error"}), 500

    new_values = process_config_update(user_input, values, schema)
    if not new_values:
        return jsonify({"error": "Generation failed"}), 500

    try:
        validate(instance=new_values, schema=schema)
    except ValidationError:
        return jsonify({"error": "Validation failed"}), 500

    return jsonify(new_values)

if __name__ == '__main__':
    host_port = ARGS.listen.split(':')
    port = int(host_port[1]) if len(host_port) > 1 else int(host_port[0])
    host = host_port[0] if len(host_port) > 1 else '0.0.0.0'
    app.run(host=host, port=port)
