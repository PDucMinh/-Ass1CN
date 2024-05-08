from flask import Flask, request, jsonify
from flask_cors import CORS
import pexpect
import subprocess

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins
terminals = {}  # Dictionary to store terminal information by node ID

@app.route('/create_node', methods=['POST'])
def create_node():
    node_id = request.json.get('node_id')
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
    node_id = request.json.get('node_id')
    mode = request.json.get('mode')
    filename = request.json.get('filename')

    if node_id not in terminals:
        return jsonify({'error': f'Node {node_id} not found'})

    terminal = terminals[node_id]

    command = ""
    if mode == 'send':
        command = f'torrent -setMode send {filename}'
    elif mode == 'download':
        command = f'torrent -setMode download {filename}'
    elif mode == 'exit':
        command = 'torrent -setMode exit'
    else:
        return jsonify({'error': f'Invalid mode: {mode}'})

    terminal.sendline(command)  # Send the command
    return jsonify({'message': f'Mode set to {mode} for {filename}'})

@app.route('/start_tracker', methods=['POST'])
def start_tracker():
    command = 'python3 tracker.py'
    # Construct the command with sudo
    sudo_gnome_terminal_command = f"sudo gnome-terminal -- bash -c '{command}'"

    # Launch the GNOME Terminal with sudo
    subprocess.Popen(['bash', '-c', sudo_gnome_terminal_command])
    return jsonify({'message': 'Tracker started successfully'})


if __name__ == '__main__':
    app.run(debug=True)
