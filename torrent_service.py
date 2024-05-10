from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pexpect
import os
import subprocess
import time

from request.set_mode_request import SetModeRequest

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins
terminals = {}  # Dictionary to store terminal information by node ID
bittorrent_files = []
NODE_FILES_DIR = 'node_files'
LOGS_DIR = 'logs'

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
    
    if set_mode_request.node_id not in terminals.keys():
        return jsonify({'error': 'Invalid node ID'}), 400

    terminal = terminals[set_mode_request.node_id]

    if set_mode_request.mode == 'send':
        command = f'torrent -setMode send {set_mode_request.filename}'
        terminal.sendline(command)  # Send the command
        if set_mode_request.filename not in bittorrent_files:
            bittorrent_files.append(set_mode_request.filename)  # Save filename if it's not already in the list
        return jsonify({'message': f'Mode set to {set_mode_request.mode} for {set_mode_request.filename}'})
    elif set_mode_request.mode == 'download':
        command = f'torrent -setMode download {set_mode_request.filename}'
        terminal.sendline(command)  # Send the command
        # Wait for the file to be downloaded
        download_path = os.path.join(NODE_FILES_DIR, f'node{set_mode_request.node_id}', set_mode_request.filename)
        max_wait_time = 20  # Maximum wait time in seconds
        wait_interval = 2  # Check interval in seconds
        waited_time = 0
        while not os.path.exists(download_path):
            time.sleep(wait_interval)
            waited_time += wait_interval
            if waited_time >= max_wait_time:
                return jsonify({'error': 'File download timeout exceeded'}), 500
        return jsonify({'message': f'Mode set to {set_mode_request.mode} for {set_mode_request.filename}'})
    elif set_mode_request.mode == 'exit':
        command = 'torrent -setMode exit'
        terminal.sendline(command)  # Send the command
        del terminals[set_mode_request.node_id]  # Remove terminal entry upon exit
        # Remove log file associated with the node ID
        log_file_path = f'logs/node{set_mode_request.node_id}.log'
        if os.path.exists(log_file_path):
            os.remove(log_file_path)
        return jsonify({'message': f'Node {set_mode_request.node_id} exited'})
    else:
        return jsonify({'error': f'Invalid mode: {set_mode_request.mode}'}), 400


@app.route('/start_tracker', methods=['POST'])
def start_tracker():
    command = 'python3 tracker.py'
    # Construct the command with sudo
    sudo_gnome_terminal_command = f"sudo gnome-terminal -- bash -c '{command}'"

    # Launch the GNOME Terminal with sudo
    subprocess.Popen(['bash', '-c', sudo_gnome_terminal_command])
    return jsonify({'message': 'Tracker started successfully'})


@app.route('/get_nodes', methods=['GET'])
def get_nodes():
    nodes_data = []

    for node_id in terminals.keys():
        node_folder = f'node{node_id}'
        node_files_path = os.path.join(NODE_FILES_DIR, node_folder)
        
        if os.path.exists(node_files_path):
            node_files = os.listdir(node_files_path)
            files_str = ", ".join(node_files) if node_files else ""
            nodes_data.append({
                'nodeId': node_id,
                'files': files_str
            })

    return jsonify({
        'count': len(nodes_data),
        'data': nodes_data,
        'bittorrentFiles': bittorrent_files
    })


@app.route('/upload_file', methods=['POST'])
def upload_file():
    # Get node ID and file from request data
    node_id = request.form.get('nodeId')
    file = request.files.get('file')

    if not node_id:
        return jsonify({'error': 'Node ID is required'}), 400
    if not file:
        return jsonify({'error': 'File is required'}), 400
    if int(node_id) not in terminals.keys():
        return jsonify({'error': 'Invalid node ID'}), 400


    # Create directory for the node if it doesn't exist
    node_dir = os.path.join(NODE_FILES_DIR, f'node{node_id}')
    os.makedirs(node_dir, exist_ok=True)

    # Save the file to the node's directory
    file_path = os.path.join(node_dir, file.filename)
    file.save(file_path)

    max_wait_time = 20  # Maximum wait time in seconds
    wait_interval = 2  # Check interval in seconds
    waited_time = 0
    while not os.path.exists(file_path):
            time.sleep(wait_interval)
            waited_time += wait_interval
            if waited_time >= max_wait_time:
                return jsonify({'error': 'File download timeout exceeded'}), 500

    # Check if file was saved successfully
    if os.path.exists(file_path):
        return jsonify({'message': f'File uploaded successfully to Node {node_id}'}), 200
    else:
        return jsonify({'error': 'Failed to upload file'}), 500


@app.route('/get_log', methods=['POST'])
def get_log():
    data = request.json
    node_id = data.get('nodeId')
    log_file_name = f'node{node_id}.log'
    log_file_path = os.path.join(LOGS_DIR, log_file_name)

    if os.path.exists(log_file_path):
        # Read the contents of the log file
        with open(log_file_path, 'r') as file:
            log_data = file.read()

        # Send the log data as part of the JSON response
        return jsonify({'logData': log_data})
    else:
        return jsonify({'error': f'Log file not found for Node {node_id}'}), 404
    

if __name__ == '__main__':
    app.run(debug=True)
