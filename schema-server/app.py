import os
import json
import argparse
from flask import Flask, jsonify, abort

app = Flask(__name__)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema-dir', default=os.environ.get('SCHEMA_DIR', '/data/schemas'))
    parser.add_argument('--listen', default=os.environ.get('FLASK_RUN_PORT', '5001'))
    args, _ = parser.parse_known_args()
    return args

ARGS = get_args()

@app.route('/<app_name>', methods=['GET'])
def get_schema(app_name):
    filename = f"{app_name}.schema.json"
    filepath = os.path.join(ARGS.schema_dir, filename)
    
    if not os.path.exists(filepath):
        abort(404)
        
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception:
        abort(500)

if __name__ == '__main__':
    host_port = ARGS.listen.split(':')
    port = int(host_port[1]) if len(host_port) > 1 else int(host_port[0])
    host = host_port[0] if len(host_port) > 1 else '0.0.0.0'
    app.run(host=host, port=port)
