from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)
terminals = {}  # Dictionary to store terminal information by node ID


@app.route('/create_node', methods=['POST'])
def create_node():
    node_id = request.json.get('node_id')
    command = f'python3 node.py -node_id {node_id}'
    terminal = subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', command])
    terminals[node_id] = terminal.pid  # Store terminal PID by node ID
    return jsonify({'message': f'Node {node_id} created successfully'})


@app.route('/set_mode', methods=['POST'])
def set_mode():
    node_id = request.json.get('node_id')
    mode = request.json.get('mode')
    filename = request.json.get('filename')
    if node_id not in terminals:
        return jsonify({'error': f'Node {node_id} not found'})

    terminal_pid = terminals[node_id]
    if mode == 'send':
        command = f'torrent -setMode send {filename}'
    elif mode == 'download':
        command = f'torrent -setMode download {filename}'
    elif mode == 'exit':
        command = 'torrent -setMode exit'
    else:
        return jsonify({'error': f'Invalid mode: {mode}'})

    subprocess.Popen(['bash', '-c', f'echo "{command}" > /proc/{terminal_pid}/fd/0'])

    return jsonify({'message': f'Mode set to {mode} for {filename}'})


@app.route('/start_tracker', methods=['POST'])
def start_tracker():
    command = 'python3 tracker.py'
    subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', command])
    return jsonify({'message': 'Tracker started successfully'})


if __name__ == '__main__':
    app.run(debug=True)
