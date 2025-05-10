import json
import os
import socket
import re
import threading
import urllib.parse
import fcntl
from difflib import SequenceMatcher
from class_users import UserDatabase, FileInfoDatabase, FilePermissionsDatabase, ChangeLogDatabase
# Create an instance at the start of your server
DB_PATH = "/Users/hila/CEOs/users.db"
user_db = UserDatabase(DB_PATH)
file_permissions_db = FilePermissionsDatabase(DB_PATH)
file_db = FileInfoDatabase(DB_PATH)
change_log_db = ChangeLogDatabase(DB_PATH)

def file_exist(file_path):
    if not os.path.exists(file_path):
        return False
    return True


def handle_404(client_socket):  
    with open(r"/Users/hila/CEOs/status_code/404.png", "rb") as file3:
        photo = file3.read()
        file_type = "png"
        response = ready_to_send("404 Not Found", photo, file_type)
        client_socket.send(response.encode() + photo)


def handle_403(client_socket):
    with open(r"/Users/hila/CEOs/status_code/403.webp", "rb") as file3:
        photo = file3.read()
        file_type = "webp"
        response = ready_to_send("403 Forbidden", photo, file_type)
        client_socket.send(response.encode() + photo)


def handle_500(client_socket):
    try:
        with open(r"/Users/hila/CEOs/status_code/500.png", "rb") as file3:
            photo = file3.read()
            file_type = "png"
            response = ready_to_send("500 Internal Server Error", photo, file_type)
            client_socket.send(response.encode() + photo)
    except BrokenPipeError:
        print("Client disconnected before response could be sent.")
    except Exception as e:
        print(f"An error occurred while handling 500 error: {str(e)}")


def file_forbidden(file_path, forbidden):
    if file_path in forbidden:
        return True
    return False

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


def find_file_type(request):
    print(request)
    if request == "/":  # for windows change to "\\" for mac "/"
        request = r"/home_page.html"  # will change to /home.html when there will be home screen  /code_page
        file_type = "text/html"
    elif r".html" in request:
        file_type = "text/html"
    elif r"/js" in request:
        file_type = "text/js"
    elif r"/imgs" in request:
        index_dot = request.find(".") + 1
        file_type = "image/" + request[index_dot:index_dot + 3]
    else:
        index_dot = request.find(".") + 1
        file_type = "text/" + request[index_dot:index_dot + 3] 
    print(file_type)
    return request, file_type


def get_content_of_upload(client_socket, content_length):
    # Receive and write file data
    bytes_received = 0
    content = b""
    try:
        while bytes_received < content_length:
            chunk_size = min(1024, content_length - bytes_received)
            data = client_socket.recv(chunk_size)
            if not data:
                break
            content += data
            bytes_received += len(data)

        if bytes_received == content_length:
            msg = "File received successfully."
            print(msg)
            return content.decode()  # Decode the bytes to string before returning
        else:
            msg = f"File upload incomplete. Received {bytes_received} of {content_length} bytes."
            print(msg)
            return None
    except (BrokenPipeError, ConnectionResetError) as e:
        print(f"Connection error during file upload: {str(e)}")
        return None


def receive_headers(client_socket):
    # Receiveing only the headers
    headers = b""
    client_socket.settimeout(300) 
    action = client_socket.recv(4).decode() # can get less than 4
    client_socket.settimeout(90)
    if not action:
        #print("client disconnected")
        return f"client disconnected", ""
    if action != "GET " and action != "POST":
        #print(f"Not valid action: '{action}'")
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

def new_file(client_socket, PATH_TO_FOLDER, headers_data, value = ""):
    user_id = get_header(client_socket, headers_data, r'userId:\s*(\S+)')
    if not user_id:
        return
    filename = get_header(client_socket, headers_data, r'filename:\s*(\S+)')
    if not filename:
        return
    
    # Check if filename already exists for this user
    existing_file = file_db.check_file_exists(user_id, filename)
    if existing_file:
        # File already exists, send error response
        data = json.dumps({
            "error": "File already exists",
            "fileId": 0
        })
        print("File already exists")
        response = ready_to_send("200", data, "application/json")
        
    else:
        # Create new file
        result = file_db.add_file(filename, user_id)
        
        if result['status'] == 201:
            lines = [""]
            if value:
                lines = value.split("/n")
            with open(PATH_TO_FOLDER + "/uploads/"+ filename, 'w') as file:
                file.writelines(lines)  # Create file
            print(f"File {filename} created in path.")
            # Get the file ID of the newly created file
            file_id = file_db.check_file_exists(user_id, filename)
            file_permissions_db.grant_access(file_id, user_id,"owner")

            data = json.dumps({
                "success": "File created successfully",
                "fileId": file_id
            })
            # Send success response
            print("File created successfully")
            response = ready_to_send(result['status'], data, "application/json")
        else:
            # Send error response
            print("error: " + result['message'])
            response = ready_to_send(result['status'], result['message'], "application/json")
        client_socket.send(response.encode())


def get_header(client_socket, headers_data, header=r'filename:\s*(\S+)'):
    header_match = re.search(header, headers_data)
    if not header_match:
        client_socket.send(ready_to_send("406 Not Acceptable", f" header not found", "text/plain").encode())
        return "header not found file"
    return header_match.group(1)

def get_filename(client_socket, headers_data):
    filename_match = re.search(r'filename:\s*(\S+)', headers_data)
    if not filename_match:
        client_socket.send(ready_to_send("406 Not Acceptable", f" no filename", "text/plain").encode())
        return "no filename"
    return filename_match.group(1)


def get_countent_len(client_socket, headers_data):
    match = re.search(r'file-length:\s*(\S+)', headers_data)
    if not match:
        client_socket.send(ready_to_send("406 Not Acceptable", f" no file-length", "text/plain").encode())
        return "no file"
    return match.group(1)


def modify_file(row, action, content, file_path, linesLength):
    try:
        with open(file_path, 'r+', encoding='utf-8', newline=None) as file:
            # Lock the file for writing
            fcntl.flock(file, fcntl.LOCK_EX)

            lines = file.readlines()  # Read all lines into a list

            # Checking if an empty line has been deleted
            if action == 'delete same line' or action == "Z update":
                print("lineslength: " + str(len(lines)))
                if len(lines) > linesLength:
                    print('update and delete ')
                    action = 'update and delete row below'
                else:
                    action = 'update'

                
            if action == "delete highlighted":
                for i in range(content - 1,row - 1, -1):  # content is used as the end of the delete
                    del lines[i]

            elif action == 'saveAll':
                lines.clear()
                lines = content

            elif action == 'delete':
                print(f"Attempting to delete row: {row} from {len(lines)} ")
                if 0 <= row < len(lines):
                    del lines[row]
                else:
                    raise ValueError("Row number is out of bounds.")

            elif action == "insert" or action == "paste":
                if action == "paste":
                    content = content.replace('\\"', '"')
                print(f"Attempting to insert: {row}")
                if row >= len(lines):
                    print(f"at end of file: {row}")
                    lines.insert(row, content )
                else:
                    print("enter in mid of line ")
                    lines.insert(row, content + "\r")

            elif action == 'update':
                if row == len(lines):
                    lines.insert(row, content)
                elif 0 <= row < len(lines):
                    print(f"Attempting to update line : {row}")
                    lines[row] = content + "\r"
                else:
                    raise ValueError("Row number is out of bounds.")
                
            elif action == "update and delete row below":
                    print("in update and delete row below")
                    del lines[row + 1]
                    lines[row] = content + "\r"
            else:
                raise ValueError("Invalid action.")

            # Move the file pointer to the beginning of the file
            file.seek(0)
            file.truncate()  # Clear the file before writing new content
            file.writelines(lines)
            print("was written in file")
            return action


    except FileNotFoundError as e:
        print(e)
        raise FileNotFoundError(f"The file at {file_path} was not found.")
    except Exception as e:
        print(e)
        raise ValueError(f"An error occurred: {e}")
    
def handle_client(client_socket, client_address, num_thread):
    PATH_TO_FOLDER = r"/Users/hila/CEOs"  # for windows change to C:\webroot\ for mac /Users/hila/webroot
    FORBIDDEN = {PATH_TO_FOLDER + r"/status_code/404.png", PATH_TO_FOLDER + r"/status_code/life.txt",
                 PATH_TO_FOLDER + r"/status_code/500.png"}

    try:
        try:
            action, data = receive_headers(client_socket)
            if action == "client disconnected":
                print(action)
                client_socket.close()
                return  # Exit the function

            if action == "Not valid action":
                print(action)
                return  # Exit the function

            
            headers_data = data

            if not "/poll-updates" in headers_data:
                    print("_________________________")
                    #print(f"Client {client_address} wants to: '{action}'")

            if action == "GET ":
                end = headers_data.find(r"HTTP") - 1
                request = headers_data[:end]

                if "/poll-updates" in headers_data:
                    try:
                        fileID = get_header(client_socket, headers_data, r'fileID:\s*(\d+)')
                        lastModID = get_header(client_socket, headers_data, r'lastModID:\s*(\d+)')
                        userID = get_header(client_socket, headers_data, r'userID:\s*(\d+)')
                        # Check for updates
                        updates = change_log_db.get_changes_for_user(fileID,lastModID, userID)
                        if updates:
                            response = ready_to_send(200, json.dumps(updates), content_type="application/json")
                        else: 
                            response = ready_to_send(200, json.dumps("No updates"), content_type="application/json")
                        try:
                            client_socket.send(response.encode())
                        except BrokenPipeError:
                            print("Client disconnected before response could be sent")
                            return
                        
                    except Exception as e:
                        print(f"Error in poll-updates: {str(e)}")
                        try:
                            handle_500(client_socket)
                        except BrokenPipeError:
                            print("Client disconnected during error handling")
                            return

                elif "/save" in headers_data:
                    print("in save")
                    #check if file exist in path and if he is in the db - not exist but in db create one.
                    decoded_request = urllib.parse.unquote(request)
                    match1 = re.search(r'/save\?modification=([^&]+)', decoded_request)
                    if not match1:
                        print("modification header not found")
                        raise ValueError("modification header not found")
                    
                    file_id = get_header(client_socket, headers_data, r'fileID:\s*(\d+)')
                    file_name = file_db.get_filename_by_id(file_id)['filename']
                    user_id = get_header(client_socket, headers_data, r'userID:\s*(\d+)')
                    file_path = PATH_TO_FOLDER + "/uploads/" + file_name

                    if not os.path.exists(file_path):
                        if file_name == "File not found":
                            print(f"File {file_id} does not exist in the database or path.")
                            client_socket.send(ready_to_send("200 OK", "File does not exist", "text/plain").encode())
                        else:
                            print(f"File {file_id} does not exist in the path.")
                            client_socket.send(ready_to_send("200 OK", "File does not exist", "text/plain").encode())
                    elif file_name == "File not found":
                        print(f"File {file_id} does not exist in the database.")
                        client_socket.send(ready_to_send("200 OK", "File does not exist", "text/plain").encode())


                    else:
                        modification_data = urllib.parse.unquote(match1.group(1)) 
                        modification = json.loads(modification_data)
                                
                        try:
                            print(f"trying: {modification['row']}, {modification['action']}, {modification['content']}, {file_path} ")
                            modification['action'] = modify_file(modification['row'], modification['action'], modification['content'], file_path, modification['linesLength'])
                            msg = "File modified successfully."
                            if modification['action'] in ["paste", "update delete row below"]:
                                modification["content"] = modification["content"] + "\n"
                            # Log the change only if successful
                            change_log_db.add_modification(file_id, modification, user_id)  
                        except Exception as e:
                            msg = f"Error modifying file: {str(e)}"
                        print(msg)
                        client_socket.send(ready_to_send("200 OK", msg, "text/plain").encode())
                        
                elif "/get-file-details" in headers_data:
                    try:
                        print("in /get-file-details")
                        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\d+)')
                        if not file_id:
                            raise ValueError("File ID not provided")

                        # Get file details from database
                        file_details = file_db.get_file_details(file_id)
                        if not file_details:
                            response = ready_to_send("404 Not Found", json.dumps({"error": "File not found"}), "application/json")
                            client_socket.send(response.encode())
                            return
                        # Get users with access to this file
                        users_with_access = file_permissions_db.get_users_with_access(file_id)
                        #owner_username_user_id = 
                        
                        # Prepare response data
                        response_data = {
                            "filename": file_details['filename'],
                            "users": users_with_access,
                            "owner_id": file_details['owner_id']
                        }
                        response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
                        client_socket.send(response.encode())
                    except Exception as e:
                        print(f"Error in get-file-details: {str(e)}")
                        error_response = json.dumps({"error": str(e)})
                        response = ready_to_send("500 Internal Server Error", error_response, "application/json")
                        client_socket.send(response.encode())

                elif "/get-user-files" in headers_data:
                    try:
                        print("Getting user files")
                        user_id = get_header(client_socket, headers_data, r'userId:\s*(\d+)')
                        
                        if user_id is None:
                            return  # Handle the case where user_id is not found

                        user_id = int(user_id)  # Convert user_id to integer if necessary

                        # Get list of files that user has access to
                        user_files = file_permissions_db.get_user_access_files(user_id)
                        
                        # Separate file IDs and filenames into two lists
                        file_ids = [file['fileID'] for file in user_files]
                        file_names = [file['filename'] for file in user_files]

                        # Prepare the response data with separate arrays
                        response_data = json.dumps({
                            'filesId': file_ids,
                            'filenames': file_names
                        })
                        
                        response = ready_to_send("200 OK", response_data, "application/json")
                        client_socket.send(response.encode())
                    except Exception as e:
                        print(f"Error getting user files: {str(e)}")
                        error_response = json.dumps({'error': str(e)})
                        response = ready_to_send("500 Internal Server Error", error_response, "application/json")
                        client_socket.send(response.encode())
                
                elif "/new-file" in headers_data:
                    print("New file")
                    user_id = get_header(client_socket, headers_data, r'userId:\s*(\S+)')
                    filename = get_header(client_socket, headers_data, r'filename:\s*(\S+)')
                    response = new_file(client_socket, PATH_TO_FOLDER, headers_data)

                elif "/load" in headers_data:
                    try:
                        print("Load")
                        fileId = get_header(client_socket, headers_data, r'fileId:\s*(\S+)')
                        file_status_and_name = file_db.get_filename_by_id(fileId)
                        filename = file_status_and_name['filename']
                        status = file_status_and_name['status']
                        if status == 404:
                            print(filename)
                            response = ready_to_send("404 Not Found", filename, "application/json")
                            client_socket.send(response.encode())
                        else:
                            file_path = f"{PATH_TO_FOLDER}/uploads/{filename}"
                            print("fileID: " + fileId + " name: " + filename)
                            if not os.path.exists(file_path):
                                response_data = json.dumps({'fullContent': ''})
                            else:
                                with open(file_path, 'r') as file:
                                    content = file.read()
                                    response_data = json.dumps({
                                        'fullContent': content
                                    })

                            print("loaded successfully")
                            lastModID = change_log_db.get_last_mod_id(fileId)
                            response_data = {
                                'lastModID': lastModID,
                                'fullContent': content
                            }
                            response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
                            client_socket.send(response.encode())

                    except Exception as e:
                        print(f"Error in load handler: {str(e)}")
                        error_response = json.dumps({'error': str(e)})
                        response = ready_to_send("500 Internal Server Error", error_response, "application/json")
                        client_socket.send(response.encode() + error_response.encode('utf-8'))

                elif "imgs/" in request or request == "//":  # for windows change to // for mac //

                    if file_forbidden(PATH_TO_FOLDER + request, FORBIDDEN):
                        handle_403(client_socket)

                    elif not file_exist(PATH_TO_FOLDER + request):
                        handle_404(client_socket)

                    else:
                        request, file_type = find_file_type(request)
                        print("Geting a file - " + request)

                        with open(PATH_TO_FOLDER + request, "rb") as file3:
                            status = "200 OK"
                            photo = file3.read()
                        response = ready_to_send(status, photo, file_type)
                        client_socket.send(response.encode() + photo)

                elif "." in request or "/" == request:  # is the last option/elif
                    request, file_type = find_file_type(request)
                    print("Geting a file - " + request)

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
                    print("last else 500")
                    handle_500(client_socket)

            elif action == "POST":
                try:
                    match = re.search(r'Content-Length: (\d+)', headers_data)
                    if not match:
                        print("Content-Length header not found")
                        raise ValueError("Content-Length header not found")

                    content_length = int(match.group(1))
                    if "/signup" in headers_data:
                        body = client_socket.recv(content_length).decode()
                        data = json.loads(body)
                        username = data.get('username')
                        password = data.get('password')
                        response = user_db.signup(username, password)
                        client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())

                    elif "/login" in headers_data:
                        #print("headers_data: " + headers_data)
                        body = client_socket.recv(content_length).decode()
                        data = json.loads(body)
                        username = data.get('username')
                        password = data.get('password')
                        response = user_db.login(username, password)
                        client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())
                    
                    elif "/grant-user-to-file" in headers_data:
                        #print("headers_data: " + headers_data)
                        body = client_socket.recv(content_length).decode()
                        data = json.loads(body)
                        fileID = data.get('fileID')
                        username = data.get('username')
                        userID = user_db.get_user_id(username)
                        response = file_permissions_db.grant_access(fileID,userID)
                        client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())

                    elif "/revoke-user-to-file" in headers_data:
                        #print("headers_data: " + headers_data)
                        body = client_socket.recv(content_length).decode()
                        data = json.loads(body)
                        fileID = data.get('fileID')
                        username = data.get('username')
                        userID = user_db.get_user_id(username)
                        response = file_permissions_db.revoke_access(fileID,userID)
                        client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())


                    elif "/disconnection" in headers_data:
                        body = ""
                        if content_length > 0:
                            body = client_socket.recv(content_length).decode()
                        return  # Exit the function

                    elif "/upload-file" in headers_data: 
                        print("------------------")
                        print("in uploads")
                        content = get_content_of_upload(client_socket, content_length)
                        print("after content")
                        if content:
                            new_file(client_socket, PATH_TO_FOLDER, headers_data,content)
                        else:
                            client_socket.send(ready_to_send("400 Bad Request", "Broken pipe or No content"))


                except Exception as e:
                    print(f"Error processing POST request: {str(e)}")
                    handle_500(client_socket)

            else:
                print("received unknown action! action: " + action)

        except ConnectionResetError:
            print(f"Connection reset by peer: {client_address} in thread {num_thread}")
        except socket.timeout:
            print(f"Socket timeout for client {client_address} in thread {num_thread}")
        except Exception as e:
            print(f"Error handling client {client_address}: {str(e)}")
            # Optionally, send an error response to the client
            error_response = ready_to_send("500 Internal Server Error", str(e), "text/plain")
            client_socket.send(error_response.encode())

    finally:
        client_socket.close()
        if not "/poll-updates" in headers_data: 
            print(f"Disconnected client {client_address}")
            print("_________________________")

def start_main_server(host='127.0.0.1', port=8000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(100)  # Allow up to 5 queued connections
    print('Main server is up and running')
    print("Link: http://"+ host + ":8000")
    print()
    num_thread = 0
    print("Waiting for connections...")
    while True:
        try:
            client_socket, client_address = server_socket.accept()

            num_thread = num_thread + 1

            # Create a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, num_thread), daemon=True)
            client_thread.start()

        except Exception as e:
            print(f"Error accepting connection: {str(e)}")


