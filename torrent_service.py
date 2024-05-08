from flask import Flask, request, jsonify
from flask_cors import CORS
import pexpect
import os

from request.set_mode_request import SetModeRequest

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins
terminals = {}  # Dictionary to store terminal information by node ID

@app.route('/create_node', methods=['POST'])
def create_node():
    node_id = request.json.get('nodeId')

    if node_id is None:
        return jsonify({'error': 'Node ID is required'}), 400  # Return an error response
    
    command = f'python3 node.py -node_id {node_id}'
    terminal = pexpect.spawn(f'bash', ['-c', command])

    try:
        # Example: wait for a specific startup message with a timeout
        terminal.expect('Node program started', timeout=10)
    except pexpect.TIMEOUT:
        # Handle expected timeout if the message does not appear
        print("Timeout while waiting for node to confirm startup.")
        terminal.terminate(force=True)  
        return jsonify({'error': 'Failed to start node or no confirmation received'})
    
    terminals[node_id] = terminal  # Store terminal by node ID
    return jsonify({'message': f'Node {node_id} created successfully'})

@app.route('/set_mode', methods=['POST'])
def set_mode():
    # Parse the request body into SetModeRequest object
    request_data = request.json
    set_mode_request = SetModeRequest(**request_data)
    missing_fields = set_mode_request.check_missing_fields()

    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    terminal = terminals[set_mode_request.node_id]

    command = ""
    if set_mode_request.mode == 'send':
        command = f'torrent -setMode send {set_mode_request.filename}'
    elif set_mode_request.mode == 'download':
        command = f'torrent -setMode download {set_mode_request.filename}'
    elif set_mode_request.mode == 'exit':
        command = 'torrent -setMode exit'
    else:
        return jsonify({'error': f'Invalid mode: {set_mode_request.mode}'}), 400

    terminal.sendline(command)  # Send the command
    return jsonify({'message': f'Mode set to {set_mode_request.mode} for {set_mode_request.filename}'})


@app.route('/start_tracker', methods=['POST'])
def start_tracker():
    command = 'python3 tracker.py'
    # Construct the command with sudo
    terminal = pexpect.spawn(f'bash', ['-c', command])

    try:
        # Example: wait for a specific startup message with a timeout
        terminal.expect('Tracker program started', timeout=10)
    except pexpect.TIMEOUT:
        # Handle expected timeout if the message does not appear
        print("Timeout while waiting for tracker to confirm startup.")
        terminal.terminate(force=True)  
        return jsonify({'error': 'Failed to start tracker or no confirmation received'})

    return jsonify({'message': 'Tracker started successfully'})


@app.route('/get_nodes', methods=['GET'])
def get_nodes():
    nodes_data = []

    for node_id in terminals.keys():
        node_folder = f'node{node_id}'
        node_files_path = os.path.join('node_files', node_folder)
        
        if os.path.exists(node_files_path):
            node_files = os.listdir(node_files_path)
            files_str = ", ".join(node_files) if node_files else ""
            nodes_data.append({
                'nodeId': node_id,
                'files': files_str
            })

    return jsonify({
        'count': len(nodes_data),
        'data': nodes_data
    })



if __name__ == '__main__':
    app.run(debug=True)
