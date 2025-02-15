import json
import os
import socket
import re
import subprocess
import threading
import urllib.parse
from difflib import SequenceMatcher


def file_exist(file_path):
    if not os.path.exists(file_path):
        return False
    return True


def handle_404(client_socket):  # for windows change to C:\webroot\ for mac /Users/hila/webroot/
    with open(r"/Users/hila/CEOs/status_code/404.png", "rb") as file3:
        photo = file3.read()
        file_type = "png"
        response = ready_to_send("404 Not Found", photo, file_type)
        client_socket.send(response.encode() + photo)


def handle_403(client_socket):  # for windows change to C:\webroot\ for mac /Users/hila/webroot/
    with open(r"/Users/hila/CEOs/status_code/403.webp", "rb") as file3:
        photo = file3.read()
        file_type = "webp"
        response = ready_to_send("403 Forbidden", photo, file_type)
        client_socket.send(response.encode() + photo)


def handle_500(client_socket):  # for windows change to C:\webroot\ for mac /Users/hila/webroot/
    with open(r"/Users/hila/CEOs/status_code/500.png", "rb") as file3:
        photo = file3.read()
        file_type = "png"
        response = ready_to_send("500 Internal Server Error", photo, file_type)
        client_socket.send(response.encode() + photo)


def file_forbidden(file_path, forbidden):
    if file_path in forbidden:
        return True
    return False


def ready_to_send(status, data_file, content_type="text/html"):
    data = f"HTTP/1.1 {status}\r\n"
    data += f"Content-Type: {content_type}\r\n"
    data += f"Content-Length: {len(data_file)}\r\n"
    data += "\r\n"
    return data


def find_file_type(request):
    if request == "/":  # for windows change to "\\" for mac "/"
        request = r"/html/code_page.html"  # will change to /home.html when there will be home screen  /code_page
        file_type = "text/html"
    elif r"/js" in request:
        file_type = "text/js"
    else:
        index_dot = request.find(".") + 1
        file_type = "text/" + request[index_dot:index_dot + 3]
    print(file_type)
    return request, file_type


def upload_file(client_socket, headers_data, PATH_TO_FOLDER, content_length):
    # Extract filename
    filename = get_filename(client_socket, headers_data)
    if filename == "no file":
        filename = "unnamed_file"
    print(f"File name is: {filename}\nLength: {content_length}")
    client_socket.send(ready_to_send("200 OK", "Ready to receive file", "text/plain").encode())

    # Receive and write file data
    bytes_received = 0
    with open(PATH_TO_FOLDER + "/uploads/" + filename, 'wb') as file:
        while bytes_received < content_length:
            chunk_size = min(1024, content_length - bytes_received)
            data = client_socket.recv(chunk_size)
            if not data:
                break
            file.write(data)
            bytes_received += len(data)

    if bytes_received == content_length:
        msg = "File received successfully."
    else:
        msg = f"File upload incomplete. Received {bytes_received} of {content_length} bytes."
    print(msg)
    client_socket.send(ready_to_send("200 OK", msg, "text/plain").encode())


def receive_headers(client_socket):
    # Receiveing only the headers
    headers = b""
    client_socket.settimeout(300) 
    action = client_socket.recv(4).decode() # can get less than 4
    client_socket.settimeout(25)
    if action != "GET " and action != "POST":
        return "Not valid action", ""
    print(f"Client wants to: '{action}'")

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
    return action, headers


def run_file(client_socket, file, PATH_TO_FOLDER):
    print(f"\n\rRunning file: {file}\n\r")
    if file == "no file":
        return
        
    # Check file extension
    if not file.endswith('.py'):
        response_data = json.dumps({'output': 'Error: Only Python files can be executed'})
        response = ready_to_send("400 Bad Request", response_data, "application/json")
        client_socket.send(response.encode() + response_data.encode('utf-8'))
        return
        
    file_path = f"{PATH_TO_FOLDER}/uploads/{file}"
    working_dir = f"{PATH_TO_FOLDER}/uploads"
    
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file} not found")
            
        # Run the Python file and capture both stdout and stderr
        process = subprocess.Popen(
            ['python', file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir)
        try:
            output, error = process.communicate(timeout=5)
            if error:
                result = error
            else:
                result = output if output else "Program executed successfully with no output."
        except subprocess.TimeoutExpired:
            process.kill()
            result = "Execution timed out after 5 seconds."
            
    except FileNotFoundError as e:
        result = str(e)
    except Exception as e:
        result = f"Error executing file: {str(e)}"

    response_data = json.dumps({'output': result})
    response = ready_to_send("200 OK", response_data, "application/json")
    client_socket.send(response.encode() + response_data.encode('utf-8'))


def get_filename(client_socket, headers_data):
    filename_match = re.search(r'filename:\s*(\S+)', headers_data)
    if not filename_match:
        client_socket.send(ready_to_send("406 Not Acceptable", f" no filename", "text/plain").encode())
        return "no file"
    return filename_match.group(1)

def get_countent_len(client_socket, headers_data):
    match = re.search(r'file-length:\s*(\S+)', headers_data)
    if not match:
        client_socket.send(ready_to_send("406 Not Acceptable", f" no file-length", "text/plain").encode())
        return "no file"
    return match.group(1)


def modify_file(row, action, content, file_path, new_lines_length):
    try:
        with open(file_path, 'r', encoding='utf-8', newline=None) as file:
            lines = file.readlines()  # Read all lines into a list
        
        # Add debug printing
        # print(f"File contents: {repr(lines)}")  # This will show exact contents including newlines
        # print(f"Number of lines: {len(lines)}")
        # print(f"Line lengths: {[len(line) for line in lines]}")

        if action == 'delete':
            print(f"Attempting to delete row: {row} from {len(lines)} ")
            if 0 <= row < len(lines) and new_lines_length < len(lines):  
                del lines[row]
            else:
                raise ValueError("Row number is out of bounds.")
            
        elif action == 'update':
                if new_lines_length > len(lines):
                    print(f"lines: {len(lines)} new lines: {new_lines_length} ")
                    print(f"Attempting to insert: {row}")
                    if row >= len(lines):
                        print(f"at end of file: {row}")
                        content = content + "\n\r" #+ content
                        lines.insert(row, content) 
                    else:
                        print("enter in mid of line ")
                        content_above = lines[row - 1]
                        print(content_above)
                        end = len(content_above) - len(content) - 1
                        lines[row - 1] = content_above[0:end] + "\r"
                        lines.insert(row, content + "\r") 
                elif 0 <= row < len(lines): 
                    print(f"Attempting to update line : {row}")
                    lines[row] = content + "\r"
        else:
            raise ValueError("Row number is out of bounds for modification.")
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            print("was written in file")

    except FileNotFoundError:
        print(e)
        raise FileNotFoundError(f"The file at {file_path} was not found.")
    except Exception as e:
        print(e)
        raise ValueError(f"An error occurred: {e}")


def handle_client(client_socket, client_address, num_thread):
    PATH_TO_FOLDER = r"/Users/hila/CEOs"  # for windows change to C:\webroot\ for mac /Users/hila/webroot
    FORBIDDEN = {PATH_TO_FOLDER + r"/status_code/404.png", PATH_TO_FOLDER + r"/status_code/life.txt",
                 PATH_TO_FOLDER + r"/status_code/500.png"}

    print(f"New connection from {client_address} in thread {num_thread}")
    try:
        while True:
            print("while")
            try:
                #client_socket.settimeout(300) 
                #action = client_socket.recv(4).decode() # can get less than 4
                #client_socket.settimeout(None)  
                #print(f"Client {client_address} wants to: '{action}'")

                action, data = receive_headers(client_socket)
                if action == "Not valid action":
                    print("received unknown action! action:" + action)
                    break
                print(f"Client {client_address} wants to: '{action}'")
                headers_data = data.decode()
                print("------------------")
                print("Client sent headers:" + headers_data)
                print("------------------")

                if action == "GET ":
                    end = headers_data.find(r"HTTP") - 1
                    request = headers_data[:end]  # for windows add .replace("/", "\\")

                    if "/save" in headers_data:
                        print("in save")
                        decoded_request = urllib.parse.unquote(request)
                        match1 = re.search(r'/save\?modification=([^&]+)', decoded_request)
                        if not match1:
                            print("modification header not found")
                            raise ValueError("modification header not found")

                        filename = get_filename(client_socket, headers_data)
                        file_path = PATH_TO_FOLDER + "/uploads/" + filename
                        modification_data = urllib.parse.unquote(match1.group(1))
                        modification = json.loads(modification_data)
                        currentLine = modification['currentLine']
                        row = modification['row']
                        action = modification['action']
                        try:
                            print(f"trying: {row}, {action}, {currentLine}, {file_path} ")
                            modify_file(row, action, currentLine, file_path,modification['linesLength'])
                            msg = "File modified successfully."
                        except Exception as e:
                            msg = f"Error modifying file: {str(e)}"
                        print(msg)
                        client_socket.send(ready_to_send("200 OK", msg, "text/plain").encode())

                    elif "/check-updates" in headers_data:
                        print("Checks For Updates")
                        filename = get_filename(client_socket, headers_data)
    
                        # Get the content length from the headers
                        content_len = get_countent_len(client_socket, headers_data)
    
                        # Get the actual file size on the server
                        file_path = f"{PATH_TO_FOLDER}/uploads/{filename}"
                        response_data = {'hasUpdates': False}  # Default to no updates

                        if os.path.exists(file_path):
                            actual_file_len = os.path.getsize(file_path)
                            if int(content_len) != actual_file_len:
                                response_data['hasUpdates'] = True  # Update available

                        # Send JSON response
                        response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
                        client_socket.send(response.encode() + json.dumps(response_data).encode('utf-8'))

                    elif "/run" in headers_data:
                        print("in run")
                        filename = get_filename(client_socket, headers_data)
                        if not os.path.exists(f"{PATH_TO_FOLDER}/uploads/{filename}"):
                            client_socket.send(ready_to_send("404 Not Found", f"{filename} does not exist in uploads",
                                                             "text/plain").encode())
                        run_file(client_socket, filename, PATH_TO_FOLDER)

                    elif "/load" in headers_data:
                        try:
                            print("in load")
                            filename = get_filename(client_socket, headers_data)
                            file_path = f"{PATH_TO_FOLDER}/uploads/{filename}"
                            
                            if not os.path.exists(file_path):
                                response_data = json.dumps({'fullContent': ''})
                            else:
                                with open(file_path, 'r') as file:
                                    content = file.read()
                                    response_data = json.dumps({
                                        'fullContent': content
                                    })

                            print("loaded successfully")
                            response = ready_to_send("200 OK", response_data, "application/json")
                            client_socket.send(response.encode() + response_data.encode('utf-8'))
                            
                        except Exception as e:
                            print(f"Error in load handler: {str(e)}")
                            error_response = json.dumps({'error': str(e)})
                            response = ready_to_send("500 Internal Server Error", error_response, "application/json")
                            client_socket.send(response.encode() + error_response.encode('utf-8'))

                    elif "imgs" in request or request == "//":  # for windows change to // for mac //

                        if file_forbidden(PATH_TO_FOLDER + request, FORBIDDEN):
                            handle_403(client_socket)

                        elif not file_exist(PATH_TO_FOLDER + request):
                            handle_404(client_socket)

                        else:
                            request, file_type = find_file_type(request)

                            with open(PATH_TO_FOLDER + request, "rb") as file3:
                                status = "200 OK"
                                photo = file3.read()
                            response = ready_to_send(status, photo, file_type)
                            client_socket.send(response.encode() + photo)

                    elif "." in request or "/" == request:  # is the last option/elif
                        request, file_type = find_file_type(request)

                        if file_forbidden(PATH_TO_FOLDER + request, FORBIDDEN):
                            handle_403(client_socket)

                        elif not file_exist(PATH_TO_FOLDER + request):
                            handle_404(client_socket)

                        else:
                            with open(PATH_TO_FOLDER + request, "r") as file2:
                                code = file2.read()
                                status = "200 OK"
                                response = ready_to_send(status, code, file_type)
                                response += code
                                client_socket.send(response.encode())

                    else:
                        print("500")
                        handle_500(client_socket)

                elif action == "POST":
                    try:
                        match = re.search(r'Content-Length: (\d+)', headers_data)
                        if not match:
                            print("Content-Length header not found")
                            raise ValueError("Content-Length header not found")

                        content_length = int(match.group(1))
                                
                        if "/upload" in headers_data: 
                            print("in uploads")
                            upload_file(client_socket, headers_data, PATH_TO_FOLDER, content_length)

                        else:
                            print("Not valid action")
                            raise ValueError("Not valid action")

                    except Exception as e:
                        print(f"Error processing POST request: {str(e)}")
                        handle_500(client_socket)

                else:
                    print("received unknown action! action:" + action)
                    break  # Exit the loop if an unknown action is received

            except ConnectionResetError:
                print(f"Connection reset by peer: {client_address} in thread {num_thread}")
                break
            except Exception as e:
                print(f"Error handling client {client_address}: {str(e)}")
                break

    finally:
        client_socket.close()
        print(f"Disconnected client {client_address}")
        print("_________________________")


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 8000))
    server_socket.listen(5)  # Allow up to 5 queued connections
    print('Server is up and running')
    num_thread = 0

    while True:
        try:
            print("Waiting for connections...")
            client_socket, client_address = server_socket.accept()
            print(f'New client connected: {client_address}')

            num_thread = num_thread + 1

            # Create a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, num_thread), daemon=True)
            client_thread.start()

        except Exception as e:
            print(f"Error accepting connection: {str(e)}")


if __name__ == "__main__":
    main()
