import json
import os
import socket
import re
import threading
import urllib.parse
import fcntl
import logging
from class_users import UserDatabase, FileInfoDatabase, FilePermissionsDatabase, ChangeLogDatabase, VersionDatabase, RSAManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create an instance at the start of your server
DB_PATH = "/Users/hila/CEOs/users.db"
user_db = UserDatabase(DB_PATH)
file_permissions_db = FilePermissionsDatabase(DB_PATH)
file_db = FileInfoDatabase(DB_PATH)
change_log_db = ChangeLogDatabase(DB_PATH)
version_log_db = VersionDatabase(DB_PATH)
rsa_manager = RSAManager()

logger.info("Database connections initialized")

def file_exist(file_path):
    """Check if file exists at given path"""
    exists = os.path.exists(file_path)
    logger.debug(f"File existence check for {file_path}: {exists}")
    return exists


def handle_404(client_socket):
    """Send 404 Not Found response with image"""
    logger.info("Sending 404 Not Found response")
    try:
        with open(r"/Users/hila/CEOs/status_code/404.png", "rb") as file3:
            photo = file3.read()
            file_type = "png"
            response = ready_to_send("404 Not Found", photo, file_type)
            client_socket.send(response.encode() + photo)
        logger.debug("404 response sent successfully")
    except Exception as e:
        logger.error(f"Error sending 404 response: {str(e)}")


def handle_403(client_socket):
    """Send 403 Forbidden response with image"""
    logger.info("Sending 403 Forbidden response")
    try:
        with open(r"/Users/hila/CEOs/status_code/403.webp", "rb") as file3:
            photo = file3.read()
            file_type = "webp"
            response = ready_to_send("403 Forbidden", photo, file_type)
            client_socket.send(response.encode() + photo)
        logger.debug("403 response sent successfully")
    except Exception as e:
        logger.error(f"Error sending 403 response: {str(e)}")


def handle_500(client_socket):
    """Send 500 Internal Server Error response with image"""
    logger.error("Sending 500 Internal Server Error response")
    try:
        with open(r"/Users/hila/CEOs/status_code/500.png", "rb") as file3:
            photo = file3.read()
            file_type = "png"
            response = ready_to_send("500 Internal Server Error", photo, file_type)
            client_socket.send(response.encode() + photo)
        logger.debug("500 response sent successfully")
    except BrokenPipeError:
        logger.warning("Client disconnected before 500 response could be sent")
    except Exception as e:
        logger.error(f"Error handling 500 error: {str(e)}")


def file_forbidden(file_path, forbidden):
    """Check if file path is in forbidden list"""
    is_forbidden = file_path in forbidden
    logger.debug(f"Forbidden check for {file_path}: {is_forbidden}")
    return is_forbidden


def ready_to_send(status, data_file, content_type="text/html",Cache=False):
    """Prepare HTTP response headers"""
    logger.debug(f"Preparing response: {status}, content_type: {content_type}")
    headers = f"HTTP/1.1 {status}\r\n"
    headers += f"Content-Type: {content_type}\r\n"
    if isinstance(data_file, bytes):
        content_length = len(data_file)
    else:
        content_length = len(data_file.encode('utf-8'))
    if Cache:
        headers += f"Cache-Control: public, max-age=31536000\r\n"
    headers += f"Content-Length: {content_length}\r\n"
    headers += f"Connection: close\r\n"
    headers += "\r\n"
    
    return headers + str(data_file)


"""def find_file_type(request):
    #Determine file type and adjust request path
    logger.debug(f"Finding file type for request: {request}")
    
    if request == "/":
        request = r"/home_page.html"
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
    
    logger.debug(f"Determined file type: {file_type} for request: {request}")
    return request, file_type
"""

def get_content_of_upload(client_socket, content_length):
    """Receive file upload content from client"""
    logger.info(f"Receiving upload content, expected length: {content_length}")
    
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
            logger.info("File received successfully")
            return content.decode()
        else:
            logger.warning(f"File upload incomplete. Received {bytes_received} of {content_length} bytes")
            return None
    except (BrokenPipeError, ConnectionResetError) as e:
        logger.error(f"Connection error during file upload: {str(e)}")
        return None


def receive_headers(client_socket):
    """Receive and parse HTTP headers from client"""
    logger.debug("Receiving headers from client")
    
    headers = b""
    client_socket.settimeout(300)
    action = client_socket.recv(4).decode()
    client_socket.settimeout(90)
    
    if not action:
        logger.info("Client disconnected")
        return f"client disconnected", ""
    
    if action == "DELE":
        action = action + client_socket.recv(2).decode()
    
    if action not in ["GET ", "POST", "DELETE"]:
        logger.warning(f"Invalid HTTP action received: '{action}'")
        return f"Not valid action", ""
    
    try:
        while True:
            chunk = client_socket.recv(1)
            headers += chunk
            if b"\r\n\r\n" in headers:
                break
    except socket.timeout:
        logger.error("Timeout while receiving headers")
        raise Exception("Timeout while receiving headers")
    finally:
        client_socket.settimeout(None)
    
    logger.debug(f"Headers received successfully, action: {action}")
    return action, headers.decode()


def get_header(client_socket, headers_data, header_pattern=r'filename:\s*(\S+)', header_name="header"):
    """Extract specific header value using regex with better error handling"""
    logger.debug(f"Looking for header: {header_name} with pattern: {header_pattern}")
    logger.debug(f"Headers data preview: {headers_data[:200]}...")
    
    header_match = re.search(header_pattern, headers_data)
    if not header_match:
        logger.error(f"Header '{header_name}' not found in request")
        logger.debug(f"All headers received:\n{headers_data}")
        error_msg = f"Header '{header_name}' not found"
        client_socket.send(ready_to_send("406 Not Acceptable", error_msg, "text/plain").encode())
        return None
    
    value = header_match.group(1)
    logger.debug(f"Header '{header_name}' extracted: {value}")
    return value


def new_file(client_socket, PATH_TO_FOLDER, headers_data, value=""):
    """Create a new file for a user"""
    logger.info("Creating new file")
    
    user_id = get_header(client_socket, headers_data, r'userId:\s*(\S+)', "userId")
    if not user_id:
        logger.error("User ID not found in headers")
        return
                
    decrypted_user_id = rsa_manager.decrypt(user_id)

    if not decrypted_user_id:
        logger.error("No valid userId header found")
        return
    
    filename = get_header(client_socket, headers_data, r'filename:\s*(\S+)', "filename")
    if not filename:
        logger.error("Filename not found in headers")
        return
    
    decrypted_filename = rsa_manager.decrypt(filename)

    if not decrypted_filename:
        logger.error("No valid userId header found")
        return
    
    logger.info(f"Creating file '{decrypted_filename}' for user {decrypted_user_id}")
    
    # Check if filename already exists for this user
    existing_file = file_db.check_file_exists(decrypted_user_id, decrypted_filename)
    if existing_file:
        logger.warning(f"File '{decrypted_filename}' already exists for user {decrypted_user_id}")
        data = json.dumps({
            "error": "File already exists",
            "fileId": 0
        })
        response = ready_to_send("200", data, "application/json")
    else:
        # Create new file
        result = file_db.add_file(decrypted_filename, decrypted_user_id)
        
        if result['status'] == 201:
            lines = [""]
            if value:
                lines = value.split("/n")
            
            file_path = PATH_TO_FOLDER + "/uploads/" + decrypted_filename
            with open(file_path, 'w') as file:
                file.writelines(lines)
            
            logger.info(f"File '{decrypted_filename}' created at path: {file_path}")
            
            # Get the file ID and grant owner access
            file_id = file_db.check_file_exists(decrypted_user_id, decrypted_filename)
            logger.debug(f"File ID: {file_id}")
            
            result = file_permissions_db.grant_access(file_id, decrypted_user_id, "owner")
            logger.info(f"Owner access granted, result: {result['status']} - {result['message']}")

            data = json.dumps({
                "success": "File created successfully",
                "fileId": file_id
            })
            response = ready_to_send(result['status'], data, "application/json")
        else:
            logger.error(f"File creation failed: {result['message']}")
            response = ready_to_send(result['status'], result['message'], "application/json")
    
    client_socket.send(response.encode())


def modify_file(row, action, content, file_path, linesLength):
    """Modify file content based on action type"""
    logger.info(f"Modifying file: {file_path}, action: {action}, row: {row}")
    
    try:
        with open(file_path, 'r+', encoding='utf-8', newline=None) as file:
            fcntl.flock(file, fcntl.LOCK_EX)
            lines = file.readlines()

            # Handle special cases
            if action == 'delete same line' or action == "Z update":
                logger.debug(f"Lines length: {len(lines)}")
                if len(lines) > linesLength:
                    logger.debug('Update and delete action detected')
                    action = 'update and delete row below'
                else:
                    action = 'update'

            # Perform the action
            if action == "delete highlighted":
                for i in range(content - 1, row - 1, -1):
                    del lines[i]
                logger.debug(f"Deleted highlighted lines from {row} to {content}")

            elif action == 'saveAll':
                lines.clear()
                lines = content
                logger.debug("Saved all content")

            elif action == 'delete':
                logger.debug(f"Attempting to delete row: {row} from {len(lines)} lines")
                if 0 <= row < len(lines):
                    del lines[row]
                else:
                    raise ValueError("Row number is out of bounds.")

            elif action == "insert" or action == "paste":
                if action == "paste":
                    content = content.replace('\\"', '"')
                logger.debug(f"Inserting at row: {row}")
                if row >= len(lines):
                    lines.insert(row, content)
                else:
                    lines.insert(row, content + "\r")

            elif action == 'update':
                if row == len(lines):
                    lines.insert(row, content)
                elif 0 <= row < len(lines):
                    logger.debug(f"Updating line: {row}")
                    lines[row] = content + "\r"
                else:
                    raise ValueError("Row number is out of bounds.")

            elif action == "update and delete row below":
                logger.debug("Update and delete row below")
                del lines[row + 1]
                lines[row] = content + "\r"
            else:
                raise ValueError("Invalid action.")

            # Write changes back to file
            file.seek(0)
            file.truncate()
            file.writelines(lines)
            logger.info("File modification completed successfully")
            return action

    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"The file at {file_path} was not found.")
    except Exception as e:
        logger.error(f"Error modifying file: {str(e)}")
        raise ValueError(f"An error occurred: {e}")


def show_version(file_id, user_id, version, client_socket):
    """Show a specific version of a file"""
    logger.info(f"Showing version {version} of file {file_id} for user {user_id}")
    
    if not file_id or not user_id or not version:
        logger.error("Missing required parameters: file_id, user_id, or version")
        raise ValueError("File ID, User ID or Version not provided")
    
    fullcontent = version_log_db.get_version_fullcontent(version, file_id)
    
    if fullcontent is None:
        logger.warning(f"Version {version} not found for file {file_id}")
        response = ready_to_send("404 Not Found", json.dumps({"error": "Version or content not found"}), "application/json")
    else:
        logger.debug(f"Version content retrieved: {fullcontent[0][:100]}...")
        response = ready_to_send("200 OK", json.dumps({"fullContent": fullcontent[0]}), "application/json")
    
    client_socket.send(response.encode())


def save_modification(client_socket, file_id, file_name, file_path, match1, user_id):
    """Save file modifications"""
    logger.info(f"Saving modification for file {file_id} by user {user_id}")
    
    if not os.path.exists(file_path):
        logger.error(f"File path does not exist: {file_path}")
        if file_name == "File not found":
            client_socket.send(ready_to_send("200 OK", "File does not exist in database", "text/plain").encode())
        else:
            client_socket.send(ready_to_send("200 OK", "File does not exist in path", "text/plain").encode())
    elif file_name == "File not found":
        logger.error(f"File {file_id} not found in database")
        client_socket.send(ready_to_send("200 OK", "File does not exist in database", "text/plain").encode())
    else:
        modification_data = urllib.parse.unquote(match1.group(1))
        try:
            modification = json.loads(modification_data)
            logger.debug(f"Modification data: {modification}")

            content = modification['content']
            
            try:
                modification['action'] = modify_file(
                    modification['row'], 
                    modification['action'], 
                    content, 
                    file_path, 
                    modification['linesLength']
                )
                msg = "File modified successfully."
                if modification['action'] in ["paste", "update delete row below"]:
                    content = content + "\n"
                change_log_db.add_modification(file_id, modification, user_id)
                logger.info("Modification saved successfully")
            except Exception as e:
                msg = f"Error modifying file: {str(e)}"
                logger.error(msg)
            
            client_socket.send(ready_to_send("200 OK", msg, "text/plain").encode())
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")


# GET request handlers
def handle_poll_updates(client_socket, headers_data):
    """Handle polling for file updates"""
    try:
        fileID = get_header(client_socket, headers_data, r'fileID:\s*(\d+)', "fileID")
        lastModID = get_header(client_socket, headers_data, r'lastModID:\s*(\d+)', "lastModID")
        userID = get_header(client_socket, headers_data, r'userID:\s*(\d+)', "userID")
        
        if not fileID or not lastModID or not userID:
            return
        
        updates = change_log_db.get_changes_for_user(fileID, lastModID, userID)
        if updates:
            response = ready_to_send(200, json.dumps(updates), content_type="application/json")
        else:
            response = ready_to_send(200, json.dumps("No updates"), content_type="application/json")
        
        client_socket.send(response.encode())
        
    except BrokenPipeError:
        logger.warning("Client disconnected before poll-updates response could be sent")
    except Exception as e:
        logger.error(f"Error in poll-updates: {str(e)}")
        handle_500(client_socket)


def handle_save_request(client_socket, headers_data, request, PATH_TO_FOLDER):
    """Handle file save requests"""
    logger.info("Handling save request")
    
    decoded_request = urllib.parse.unquote(request)
    match1 = re.search(r'/save\?modification=([^&]+)', decoded_request)
    if not match1:
        logger.error("Modification header not found in save request")
        raise ValueError("modification header not found")
    
    file_id = get_header(client_socket, headers_data, r'fileID:\s*(\d+)', "fileID")
    user_id = get_header(client_socket, headers_data, r'userID:\s*(\d+)', "userID")
    
    if not file_id or not user_id:
        return
    
    file_name = file_db.get_filename_by_id(file_id)['filename']
    file_path = PATH_TO_FOLDER + "/uploads/" + file_name
    
    save_modification(client_socket, file_id, file_name, file_path, match1, user_id)


def handle_file_details(client_socket, headers_data):
    """Handle get file details requests"""
    logger.info("Handling file details request")
    
    try:
        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\d+)', "fileID")
        if not file_id:
            return

        file_details = file_db.get_file_details(file_id)
        if not file_details:
            response = ready_to_send("404 Not Found", json.dumps({"error": "File not found"}), "application/json")
            client_socket.send(response.encode())
            return

        users_with_access = file_permissions_db.get_users_with_access(file_id)
        response_data = {
            "filename": file_details['filename'],
            "users": users_with_access,
            "owner_id": file_details['owner_id']
        }
        response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
        client_socket.send(response.encode())
        
    except Exception as e:
        logger.error(f"Error in get-file-details: {str(e)}")
        error_response = json.dumps({"error": str(e)})
        response = ready_to_send("500 Internal Server Error", error_response, "application/json")
        client_socket.send(response.encode())


def handle_user_files(client_socket, headers_data):
    """Handle get user files requests"""
    logger.info("Handling user files request")
    
    try:

        user_id = get_header(client_socket, headers_data, r'userId:\s*(\S+)', "userId")
        if user_id:
            logger.info(f"Found user ID using pattern userId: {user_id}")
                
        decrypted_user_id = rsa_manager.decrypt(user_id)

        if not decrypted_user_id:
            logger.error("No valid userId header found")
            return
        
        decrypted_user_id = int(decrypted_user_id)
        logger.info(f"Getting files for user ID: {decrypted_user_id}")
        
        user_files = file_permissions_db.get_user_access_files(decrypted_user_id)
        file_ids = [file['fileID'] for file in user_files]
        file_names = [file['filename'] for file in user_files]
        
        logger.info(f"Found {len(file_ids)} files for user {decrypted_user_id}")
        
        response_data = json.dumps({
            'filesId': file_ids,
            'filenames': file_names
        })
        
        response = ready_to_send("200 OK", response_data, "application/json")
        client_socket.send(response.encode())
        
    except Exception as e:
        logger.error(f"Error getting user files: {str(e)}")
        error_response = json.dumps({'error': str(e)})
        response = ready_to_send("500 Internal Server Error", error_response, "application/json")
        client_socket.send(response.encode())


def handle_version_details(client_socket, headers_data):
    """Handle get version details requests"""
    logger.info("Handling version details request")
    
    try:
        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\d+)', "fileID")
        if not file_id:
            return
        
        versions = version_log_db.get_versions_by_fileID(file_id)
        response_data = json.dumps({
            'versions': versions,
            'owner_id': file_db.get_owner_id(file_id)
        })
        response = ready_to_send("200 OK", response_data, "application/json")
        client_socket.send(response.encode())
        
    except Exception as e:
        logger.error(f"Error in get-version-details: {str(e)}")
        error_response = json.dumps({"error": str(e)})
        response = ready_to_send("500 Internal Server Error", error_response, "application/json")
        client_socket.send(response.encode())


def handle_show_version(client_socket, headers_data):
    """Handle show version requests"""
    logger.info("Handling show version request")
    
    file_id = get_header(client_socket, headers_data, r'fileID:\s*(\d+)', "fileID")
    user_id = get_header(client_socket, headers_data, r'userID:\s*(\d+)', "userID")
    version = get_header(client_socket, headers_data, r'version:\s*(\d+)', "version")
    
    if not file_id or not user_id or not version:
        return
    
    show_version(file_id, user_id, version, client_socket)


def handle_viewer_status(client_socket, headers_data):
    """Handle check viewer status requests"""
    logger.info("Handling viewer status check")
    
    file_id = get_header(client_socket, headers_data, r'fileId:\s*(\d+)', "fileId")
    user_id = get_header(client_socket, headers_data, r'userId:\s*(\d+)', "userId")
    
    if not file_id or not user_id:
        return
    
    is_editor_or_owner = file_permissions_db.is_editor_or_owner(file_id, user_id)
    response = ready_to_send("200 OK", json.dumps({"isViewer": not is_editor_or_owner}), "application/json")
    client_socket.send(response.encode())


def handle_new_file_request(client_socket, headers_data, PATH_TO_FOLDER):
    """Handle new file creation requests"""
    logger.info("Handling new file request")
    
    new_file(client_socket, PATH_TO_FOLDER, headers_data,"// New file'")


def handle_load_file(client_socket, headers_data, PATH_TO_FOLDER):
    """Handle file loading requests"""
    logger.info("Handling load file request")
    
    try:
        fileId = get_header(client_socket, headers_data, r'fileId:\s*(\S+)', "fileId")
        if not fileId:
            logger.info(f"Found user ID using pattern userId: {fileId}")
            return
                
        decrypted_file_id = rsa_manager.decrypt(fileId)

        if not decrypted_file_id:
            logger.error("No valid userId header found")
            return

        file_status_and_name = file_db.get_filename_by_id(decrypted_file_id)
        filename = file_status_and_name['filename']
        status = file_status_and_name['status']
        
        if status == 404:
            logger.warning(f"File not found: {filename}")
            response = ready_to_send("404 Not Found", filename, "application/json")
            client_socket.send(response.encode())
        else:
            file_path = f"{PATH_TO_FOLDER}/uploads/{filename}"
            logger.info(f"Loading file ID: {decrypted_file_id}, name: {filename}")
            
            if not os.path.exists(file_path):
                content = ''
            else:
                with open(file_path, 'r') as file:
                    content = file.read()

            lastModID = change_log_db.get_last_mod_id(decrypted_file_id)
            response_data = {
                'lastModID': lastModID,
                'fullContent': content
            }
            response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
            client_socket.send(response.encode())
            logger.info("File loaded successfully")

    except Exception as e:
        logger.error(f"Error in load handler: {str(e)}")
        error_response = json.dumps({'error': str(e)})
        response = ready_to_send("500 Internal Server Error", error_response, "application/json")
        client_socket.send(response.encode())


def handle_public_key(client_socket):
    """Handle public key requests"""
    logger.info("Handling public key request")
    
    try:
        public_key_string = rsa_manager.get_public_key_string()
        response_data = json.dumps({"publicKey": public_key_string})
        response = ready_to_send("200 OK", response_data, "application/json")
        client_socket.send(response.encode())
        
    except Exception as e:
        logger.error(f"Error getting public key: {str(e)}")
        handle_500(client_socket)


def find_file_type(request):
    """Determine file type and adjust request path - FIXED VERSION"""
    logger.debug(f"Finding file type for request: {request}")
    
    if request == "/":
        request = r"/home_page.html"
        file_type = "text/html"
    elif r".html" in request:
        file_type = "text/html"
    elif r"/js" in request:
        file_type = "application/javascript"  # Fixed: was "text/js"
    elif r"/css" in request:
        file_type = "text/css"
    elif r"/imgs" in request:
        # Fixed: Better handling of image file types
        if request.endswith('.ico'):
            file_type = "image/x-icon"  # Correct MIME type for .ico files
        elif request.endswith('.png'):
            file_type = "image/png"
        elif request.endswith('.jpg') or request.endswith('.jpeg'):
            file_type = "image/jpeg"
        elif request.endswith('.gif'):
            file_type = "image/gif"
        elif request.endswith('.webp'):
            file_type = "image/webp"
        elif request.endswith('.svg'):
            file_type = "image/svg+xml"
        else:
            # Fallback for unknown image types
            index_dot = request.rfind(".") + 1  # Use rfind to get last dot
            extension = request[index_dot:].lower()
            file_type = f"image/{extension}"
    else:
        # Handle other file types
        index_dot = request.rfind(".") + 1  # Use rfind to get last dot
        if index_dot > 0:
            extension = request[index_dot:].lower()
            # Map common extensions to correct MIME types
            mime_map = {
                'css': 'text/css',
                'js': 'application/javascript',
                'json': 'application/json',
                'txt': 'text/plain',
                'md': 'text/markdown',
                'xml': 'application/xml'
            }
            file_type = mime_map.get(extension, f"text/{extension}")
        else:
            file_type = "text/plain"
    
    logger.debug(f"Determined file type: {file_type} for request: {request}")
    return request, file_type


def handle_static_files(client_socket, request, PATH_TO_FOLDER, FORBIDDEN):
    """Handle static file requests (images, HTML, etc.) - FIXED VERSION"""
    logger.debug(f"Handling static file request: {request}")
    
    if file_forbidden(PATH_TO_FOLDER + request, FORBIDDEN):
        logger.warning(f"Forbidden file access attempt: {request}")
        handle_403(client_socket)
    elif not file_exist(PATH_TO_FOLDER + request):
        logger.warning(f"File not found: {request}")
        handle_404(client_socket)
    else:
        request, file_type = find_file_type(request)
        logger.info(f"Serving file: {request}, type: {file_type}")  # Fixed: show file_type

        if "imgs/" in request:
            try:
                with open(PATH_TO_FOLDER + request, "rb") as file3:
                    photo = file3.read()
                
                # Fixed: Create proper HTTP response for binary files
                #headers += f"Cache-Control: public, max-age=31536000\r\n"  # Cache for 1 year
               
                response = ready_to_send("200 ok",photo,file_type).encode('utf-8') + photo
                client_socket.send(response)
                
            except Exception as e:
                logger.error(f"Error serving image file {request}: {e}")
                handle_500(client_socket)
        else:
            try:
                with open(PATH_TO_FOLDER + request, "r", encoding='utf-8') as file2:
                    code = file2.read()
                
                # Create proper HTTP response for text filesr
                
                response = ready_to_send("200 ok",code,file_type) + code
                client_socket.send(response.encode('utf-8'))
                
            except Exception as e:
                logger.error(f"Error serving text file {request}: {e}")
                handle_500(client_socket)


def handle_get_requests(client_socket, request, headers_data, PATH_TO_FOLDER, FORBIDDEN):
    """Handle all GET requests"""
    if "/poll-updates" in request:
        handle_poll_updates(client_socket, headers_data)
    else:
        logger.debug(f"Processing GET request: {request}")
        if "/save" in request:
            handle_save_request(client_socket, headers_data, request, PATH_TO_FOLDER)
        elif "/get-file-details" in request:
            handle_file_details(client_socket, headers_data)
        elif "/get-user-files" in request:
            handle_user_files(client_socket, headers_data)
        elif "/get-version-details" in request:
            handle_version_details(client_socket, headers_data)
        elif "/show-version" in request:
            handle_show_version(client_socket, headers_data)
        elif "/check-viewer-status" in request:
            handle_viewer_status(client_socket, headers_data)
        elif "/new-file" in request:
            handle_new_file_request(client_socket, headers_data, PATH_TO_FOLDER)
        elif "/load" in request:
            handle_load_file(client_socket, headers_data, PATH_TO_FOLDER)
        elif "/get-public-key" in request:
            handle_public_key(client_socket)
        elif "imgs/" in request or request == "//" or "." in request or "/" == request:
            handle_static_files(client_socket, request, PATH_TO_FOLDER, FORBIDDEN)
        else:
            logger.warning(f"Unknown GET request: {request}")
            handle_500(client_socket)


# POST request handlers
def handle_login(client_socket, content_length):
    """Handle login requests"""
    logger.info("Handling login request")
    
    body = client_socket.recv(content_length).decode()
    data = json.loads(body)
    
    # Check if data is encrypted
    if 'encrypted' in data and data['encrypted']:
        logger.debug("Processing encrypted login credentials")
        decrypted_username = rsa_manager.decrypt(data.get('username'))
        decrypted_password = rsa_manager.decrypt(data.get('password'))
        
        if not decrypted_username or not decrypted_password:
            logger.error("Failed to decrypt login credentials")
            response = {'status': 400, 'message': 'Failed to decrypt credentials'}
            client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())
            return
            
        username = decrypted_username
        password = decrypted_password
    else:
        logger.debug("Processing unencrypted login credentials")
        username = data.get('username')
        password = data.get('password')
    
    logger.info(f"Login attempt for username: {username}")
    response = user_db.login(username, password)
    
    if response['status'] == 200:
        logger.info(f"Login successful for: {username}")
    else:
        logger.warning(f"Login failed for: {username}")
    
    client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())


def handle_signup(client_socket, content_length):
    """Handle signup requests"""
    logger.info("Handling signup request")
    
    body = client_socket.recv(content_length).decode()
    data = json.loads(body)
    
    # Check if data is encrypted
    if 'encrypted' in data and data['encrypted']:
        logger.debug("Processing encrypted signup credentials")
        decrypted_username = rsa_manager.decrypt(data.get('username'))
        decrypted_password = rsa_manager.decrypt(data.get('password'))
        
        if not decrypted_username or not decrypted_password:
            logger.error("Failed to decrypt signup credentials")
            response = {'status': 400, 'message': 'Failed to decrypt credentials'}
            client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())
            return
            
        username = decrypted_username
        password = decrypted_password
    else:
        logger.debug("Processing unencrypted signup credentials")
        username = data.get('username')
        password = data.get('password')
    
    logger.info(f"Signup attempt for username: {username}")
    response = user_db.signup(username, password)
    
    if response['status'] == 201:
        logger.info(f"User registration successful: {username}")
    else:
        logger.warning(f"User registration failed: {username}")
    
    client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())


def handle_user_permissions(client_socket, content_length, headers_data, request):
    """Handle grant/revoke user permissions requests"""
    logger.info(f"Handling user permissions request: {request}")
    
    body = client_socket.recv(content_length).decode()
    data = json.loads(body)
    username = data.get('username')
    userID = user_db.get_user_id(username)
    fileID = data.get('fileID')
    role = data.get('role')
    ownerID = get_header(client_socket, headers_data, r'ownerID:\s*(\d+)', "ownerID")

    if not userID:
        logger.error(f"User not found: {username}")
        client_socket.send(ready_to_send("500 Internal Server Error", json.dumps("Not a user!!"), "application/json").encode())
    elif not ownerID or not file_db.is_owner(int(fileID), int(ownerID)):
        logger.error(f"Permission denied: User {ownerID} is not owner of file {fileID}")
        client_socket.send(ready_to_send("500 Internal Server Error", json.dumps("Not owner!!"), "application/json").encode())
    else:
        if "/revoke-user-to-file" in request:
            logger.info(f"Revoking access for user {userID} from file {fileID}")
            response = file_permissions_db.revoke_access(fileID, userID)
        elif "/grant-user-to-file" in request:
            logger.info(f"Granting {role} access for user {userID} to file {fileID}")
            response = file_permissions_db.grant_access(fileID, userID, role)
        
        client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json").encode())


def handle_save_version(client_socket, content_length):
    """Handle save new version request"""
    logger.info("Handling save new version request")
    try:
        content = get_content_of_upload(client_socket, content_length)
        if not content:
            raise ValueError("No content received")
            
        data = json.loads(content)
        file_id = data.get('fileID')
        user_id = data.get('userID')
        content = data.get('content')
        
        if not all([file_id, user_id, content]):
            raise ValueError("Missing required parameters")
            
        if file_permissions_db.is_viewer(file_id, user_id):
            logger.warning(f"User {user_id} is a viewer and cannot save new versions")
            response = ready_to_send("403 Forbidden", json.dumps({"error": "Viewers cannot save new versions"}), "application/json")
            client_socket.send(response.encode())
            return
            
        save_new_version(file_id, user_id, content, client_socket)
    except ValueError as e:
        logger.error(f"Error in save version request: {str(e)}")
        response = ready_to_send("400 Bad Request", json.dumps({"error": str(e)}), "application/json")
        client_socket.send(response.encode())
    except Exception as e:
        logger.error(f"Unexpected error in save version request: {str(e)}")
        handle_500(client_socket)


def handle_upload_file(client_socket, content_length, headers_data, PATH_TO_FOLDER):
    """Handle file upload requests"""
    logger.info("Handling file upload request")
    
    content = get_content_of_upload(client_socket, content_length)
    if content:
        content = json.loads(content)
        new_file(client_socket, PATH_TO_FOLDER, headers_data, content['content'])
    else:
        logger.error("No content received for file upload")
        client_socket.send(ready_to_send("400 Bad Request", "Broken pipe or No content").encode())


def handle_post_requests(client_socket, request, headers_data, PATH_TO_FOLDER):
    """Handle all POST requests"""
    logger.debug(f"Processing POST request: {request}")
    
    try:
        match = re.search(r'Content-Length: (\d+)', headers_data)
        if not match:
            logger.error("Content-Length header not found")
            raise ValueError("Content-Length header not found")

        content_length = int(match.group(1))
        logger.debug(f"Content length: {content_length}")
        
        if "/login" in request:
            handle_login(client_socket, content_length)
        elif "/signup" in request:
            handle_signup(client_socket, content_length)
        elif "/grant-user-to-file" in request or "/revoke-user-to-file" in request:
            handle_user_permissions(client_socket, content_length, headers_data, request)
        elif "/save-new-version" in request:
            handle_save_version(client_socket, content_length)
        elif "/disconnection" in request:
            logger.info("Client disconnection request")
            if content_length > 0:
                client_socket.recv(content_length).decode()
            return
        elif "/upload-file" in request:
            handle_upload_file(client_socket, content_length, headers_data, PATH_TO_FOLDER)
        else:
            logger.warning(f"Unknown POST request: {request}")
            handle_500(client_socket)

    except Exception as e:
        logger.error(f"Error processing POST request: {str(e)}")
        handle_500(client_socket)


# DELETE request handlers
def handle_delete_version(client_socket, headers_data):
    """Handle version deletion request"""
    logger.info("Handling version deletion request")
    try:
        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\S+)', "fileID")
        user_id = get_header(client_socket, headers_data, r'userID:\s*(\S+)', "userID")
        version = get_header(client_socket, headers_data, r'version:\s*(\S+)', "version")
        
        if file_permissions_db.is_viewer(file_id, user_id):
            logger.warning(f"User {user_id} is a viewer and cannot delete versions")
            response = ready_to_send("403 Forbidden", json.dumps({"error": "Viewers cannot delete versions"}), "application/json")
            client_socket.send(response.encode())
            return
            
        delete_version(file_id, user_id, version, client_socket)
    except ValueError as e:
        logger.error(f"Error in delete version request: {str(e)}")
        response = ready_to_send("400 Bad Request", json.dumps({"error": str(e)}), "application/json")
        client_socket.send(response.encode())
    except Exception as e:
        logger.error(f"Unexpected error in delete version request: {str(e)}")
        handle_500(client_socket)


def handle_delete_file(client_socket, headers_data, PATH_TO_FOLDER):
    """Handle delete file requests"""
    logger.info("Handling delete file request")
    
    try:
        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\d+)', "fileID")
        user_id = get_header(client_socket, headers_data, r'userID:\s*(\d+)', "userID")
        
        if not file_id or not user_id:
            return
        
        if not file_db.is_owner(int(file_id), int(user_id)):
            logger.error(f"User {user_id} is not owner of file {file_id}")
            client_socket.send(ready_to_send("500 Internal Server Error", json.dumps("Not owner!!"), "application/json").encode())
            return

        logger.info(f"Deleting file {file_id}")
        file_result = file_db.delete_file(file_id)

        if file_result['status'] != 200:
            response = ready_to_send(str(file_result['status']), json.dumps({"error": file_result['message']}), "application/json")
            client_socket.send(response.encode())
            return

        permissions_result = file_permissions_db.delete_file_permissions(file_id)
        if permissions_result['status'] != 200:
            response = ready_to_send(str(permissions_result['status']), json.dumps({"error": permissions_result['message']}), "application/json")
            client_socket.send(response.encode())
            return

        # Delete file from filesystem
        try:
            file_path = os.path.join(PATH_TO_FOLDER, "uploads", file_result['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted from filesystem: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file from filesystem: {str(e)}")

        response = ready_to_send("200 OK", json.dumps({"message": "File deleted successfully"}), "application/json")
        client_socket.send(response.encode())
        
    except Exception as e:
        logger.error(f"Error in delete-file: {str(e)}")
        error_response = json.dumps({"error": str(e)})
        response = ready_to_send("500 Internal Server Error", error_response, "application/json")
        client_socket.send(response.encode())


def handle_delete_requests(client_socket, request, headers_data, PATH_TO_FOLDER):
    """Handle all DELETE requests"""
    logger.debug(f"Processing DELETE request: {request}")
    
    if "/delete-version" in request:
        handle_delete_version(client_socket, headers_data)
    elif "/delete-file" in request:
        handle_delete_file(client_socket, headers_data, PATH_TO_FOLDER)
    else:
        logger.warning(f"Unknown DELETE request: {request}")
        handle_500(client_socket)


def handle_client(client_socket, client_address, num_thread):
    """Main client handler - now modularized into smaller functions"""
    PATH_TO_FOLDER = r"/Users/hila/CEOs"
    FORBIDDEN = {f"{PATH_TO_FOLDER}/status_code/404.png", f"{PATH_TO_FOLDER}/status_code/life.txt",
                 f"{PATH_TO_FOLDER}/status_code/500.png"}

    client_ip = client_address[0]
    client_port = client_address[1]

    try:
        try:
            action, headers_data = receive_headers(client_socket)
            
            if action == "client disconnected":
                logger.info(f"Client {client_ip} disconnected gracefully")
                client_socket.close()
                return

            if action == "Not valid action":
                logger.warning(f"Invalid HTTP method from {client_ip}")
                return

            end = headers_data.find(r"HTTP") - 1
            request = headers_data[:end]

            # Log non-polling requests with cleaner format
            if "/poll-updates" not in request:
                method = action.strip()
                logger.info(f"{client_ip} → {method} {request}")

            # Route requests to appropriate handlers
            if action == "GET ":
                handle_get_requests(client_socket, request, headers_data, PATH_TO_FOLDER, FORBIDDEN)
            elif action == "POST":
                handle_post_requests(client_socket, request, headers_data, PATH_TO_FOLDER)
            elif action == "DELETE":
                handle_delete_requests(client_socket, request, headers_data, PATH_TO_FOLDER)
            else:
                logger.warning(f"Unknown HTTP method: {action}")

        except ConnectionResetError:
            logger.warning(f"Connection lost: {client_ip} (Thread #{num_thread})")
        except socket.timeout:
            logger.warning(f"Request timeout: {client_ip} (Thread #{num_thread})")
        except Exception as e:
            logger.error(f"Request failed from {client_ip}: {str(e)}")
            error_response = ready_to_send("500 Internal Server Error", str(e), "text/plain")
            client_socket.send(error_response.encode())

    finally:
        client_socket.close()
        if "/poll-updates" not in request:
            logger.info(f"Connection closed: {client_ip}")


def start_main_server(host='127.0.0.1', port=8000):
    """Start the main server with improved logging"""
    logger.info("Starting main server...")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(100)
    
    logger.info(f"Main server is up and running on {host}:{port}")
    logger.info(f"Link: http://{host}:{port}")
    
    num_thread = 0
    logger.info("Waiting for connections...")
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            num_thread += 1
            
            # Create a new thread to handle the client
            client_thread = threading.Thread(
                target=handle_client, 
                args=(client_socket, client_address, num_thread), 
                daemon=True
            )
            client_thread.start()

        except Exception as e:
            logger.error(f"Error accepting connection: {str(e)}")

def save_new_version(file_id, user_id, content, client_socket):
    """Save a new version of a file"""
    logger.info(f"Saving new version for file {file_id} by user {user_id}")
    
    if not file_id or not user_id or not content:
        logger.error("Missing required parameters: file_id, user_id, or content")
        raise ValueError("File ID, User ID or Content not provided")
    elif file_permissions_db.is_viewer(file_id, user_id):
        logger.warning(f"User {user_id} is a viewer and cannot save new versions")
        raise ValueError("Viewers cannot save new versions")
    elif not file_permissions_db.is_editor_or_owner(file_id, user_id):
        logger.warning(f"User {user_id} does not have permission to save versions")
        raise ValueError("User does not have permission to save versions")
    
    result = version_log_db.add_version(file_id, content)
    response = ready_to_send(result['status'], json.dumps(result['message']), "application/json")
    client_socket.send(response.encode())

def delete_version(file_id, user_id, version, client_socket):
    """Delete a specific version of a file"""
    logger.info(f"Deleting version {version} of file {file_id} for user {user_id}")
    
    if not file_id or not user_id or not version:
        logger.error("Missing required parameters: file_id, user_id, or version")
        raise ValueError("File ID, User ID or Version not provided")
    elif file_permissions_db.is_viewer(file_id, user_id):
        logger.warning(f"User {user_id} is a viewer and cannot delete versions")
        raise ValueError("Viewers cannot delete versions")
    elif not file_permissions_db.is_editor_or_owner(file_id, user_id):
        logger.warning(f"User {user_id} does not have permission to delete versions")
        raise ValueError("User does not have permission to delete versions")
    
    result = version_log_db.delete_version(version, file_id)
    response = ready_to_send(result['status'], json.dumps(result['message']), "application/json")
    client_socket.send(response.encode())

if __name__ == "__main__":
    start_main_server()