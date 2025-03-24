import socket
import random
import json
import threading

def receive_headers(client_socket):
    # Receiveing only the headers
    headers = b""
    client_socket.settimeout(300) 
    action = client_socket.recv(4).decode() # can get less than 4
    client_socket.settimeout(90)
    if not action:
        return f"client disconnected", ""
    if action != "POST":
        return f"Not valid action", ""
    try:
        while True:
            chunk = client_socket.recv(1)  # gets every time one so not exstra data gets lost.
            headers += chunk
            if b"\r\n\r\n" in headers:
                break
    except socket.timeout:
        raise Exception("Timeout while receiving headers")
    finally:
        client_socket.settimeout(None)
    return action, headers.decode()


def ready_to_send(status, data_file, content_type="text/html"):
    headers = f"HTTP/1.1 {status}\r\n"
    headers += f"Content-Type: {content_type}\r\n"
    if isinstance(data_file, bytes):
        content_length = len(data_file)  # For binary data
    else:
        content_length = len(data_file.encode('utf-8'))  # For string data
    headers += f"Content-Length: {content_length}\r\n"
    headers += f"Connection: close\r\n"
    headers += "\r\n"
    
    return headers + str(data_file) # Combine headers and body content

def check_for_updates():
    # Add logic to this
    # sholud check which way sholud i keep the updates db 

    return random.choice([True, False])  # Randomly return True or False

def handle_polling_request():

    pass

def start_polling_server(port=8001, host='127.0.0.1'):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(100)  # Allow up to 5 queued connections
    print('Polling server is up and running')


    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f'New client connected: {client_address}')

            num_thread = num_thread + 1

            # Create a new thread to handle the client
            client_thread = threading.Thread(target=handle_polling_request, args=(client_socket, client_address, num_thread), daemon=True)
            client_thread.start()

        except Exception as e:
            print(f"Error accepting connection: {str(e)}")
