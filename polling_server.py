import socket
import json
import threading
from class_users import ChangeLogDatabase  # Importing ChangeLogDatabase from class_users

# Initialize the database connection
db_path = 'path_to_your_db'  # Specify the path to your database
change_log_db = ChangeLogDatabase(db_path)

def receive_headers(client_socket):
    # Receiving only the headers
    headers = b""
    client_socket.settimeout(300) 
    action = client_socket.recv(4).decode()  # can get less than 4
    client_socket.settimeout(90)
    if not action:
        return f"client disconnected", ""
    if action != "POST":
        return f"Not valid action", ""
    try:
        while True:
            chunk = client_socket.recv(1)  # gets every time one so not extra data gets lost.
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
    
    return headers + str(data_file)  # Combine headers and body content

def check_for_updates(fileID, lastModID):
    """
    Check for updates in the changeLog for a specific fileID since lastModID.
    
    :param fileID: The ID of the file to check for updates.
    :param lastModID: The last modification ID received from the client.
    :return: A list of changes if there are updates, otherwise an empty list.
    """
    # Fetch changes from the database
    changes = change_log_db.get_changes(fileID, lastModID)
    return changes

def handle_polling_request(client_socket):
    """
    Handle a polling request from a client.
    
    :param client_socket: The socket object for the client connection.
    """
    try:
        # Receive the request from the client
        action, headers = receive_headers(client_socket)
        
        if action != "POST":
            response = ready_to_send(400, "Invalid request method")
            client_socket.sendall(response.encode())
            return
        
        # Parse the request body to get fileID and lastModID
        request_body = headers.split("\r\n\r\n")[1]  # Extract body from headers
        request_data = json.loads(request_body)  # Assuming the body is in JSON format
        
        fileID = request_data.get("fileID")
        lastModID = request_data.get("lastModID")
        
        # Check for updates
        updates = check_for_updates(fileID, lastModID)
        
        if updates:
            response = ready_to_send(200, updates, content_type="application/json")
        else:
            response = ready_to_send(204, "No updates available")  # No content
        
        # Send the response back to the client
        client_socket.sendall(response.encode())
    
    except Exception as e:
        print(f"Error handling polling request: {str(e)}")
        response = ready_to_send(500, "Internal Server Error")
        client_socket.sendall(response.encode())
    finally:
        client_socket.close()

def start_polling_server(host='127.0.0.1', port=8001):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(100)  # Allow up to 5 queued connections
    print('Polling server is up and running')

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f'New client connected: {client_address}')

            # Create a new thread to handle the client
            client_thread = threading.Thread(target=handle_polling_request, args=(client_socket,), daemon=True)
            client_thread.start()

        except Exception as e:
            print(f"Error accepting connection: {str(e)}")

# Start the polling server
if __name__ == "__main__":
    start_polling_server()