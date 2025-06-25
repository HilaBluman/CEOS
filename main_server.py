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

# Initialize global AES key at module level
global_AES_key = None
try:
    global_AES_key = str(rsa_manager.generateAESKey())
    if not global_AES_key:
        raise RuntimeError("Failed to generate AES key")
except Exception as e:
    logger.error(f"Failed to initialize encryption: {str(e)}")
    raise RuntimeError("Failed to initialize encryption")

logger.info("Database connections initialized")

def should_encrypt_response(headers_data):
    """Check if the request indicates AES encryption should be used"""
    encrypted_header = re.search(r'encrypted:\s*(\S+)', headers_data)
    return bool(encrypted_header and encrypted_header.group(1).lower() == 'true')

def encrypt_response_data(data, use_encryption=False, key = global_AES_key):
    """Encrypt response data if encryption is enabled"""
    if use_encryption and key:
        try:
            if isinstance(data, dict):
                data_str = json.dumps(data)
            else:
                data_str = str(data)
            encrypted_data = rsa_manager.encryptAES(data_str, str(key))
            return {"encrypted_data": encrypted_data, "encrypted": True}
        except Exception as e:
            logger.error(f"Error encrypting response data: {str(e)}")
            return data
    return data

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
            file_type = "image/png"
            response = ready_to_send("404 Not Found", photo, file_type)
            client_socket.send(response)
        logger.debug("404 response sent successfully")
    except Exception as e:
        logger.error(f"Error sending 404 response: {str(e)}")


def handle_403(client_socket):
    """Send 403 Forbidden response with image"""
    logger.info("Sending 403 Forbidden response")
    try:
        with open(r"/Users/hila/CEOs/status_code/403.webp", "rb") as file3:
            photo = file3.read()
            file_type = "image/webp"
            response = ready_to_send("403 Forbidden", photo, file_type)
            client_socket.send(response)
        logger.debug("403 response sent successfully")
    except Exception as e:
        logger.error(f"Error sending 403 response: {str(e)}")


def handle_500(client_socket):
    """Send 500 Internal Server Error response with image"""
    logger.error("Sending 500 Internal Server Error response")
    try:
        with open(r"/Users/hila/CEOs/status_code/500.png", "rb") as file3:
            photo = file3.read()
            file_type = "image/png"
            response = ready_to_send("500 Internal Server Error", photo, file_type)
            client_socket.send(response)
        logger.debug("500 response sent successfully")
    except BrokenPipeError:
        logger.warning("Client disconnected before 500 response could be sent")
    except Exception as e:
        logger.error(f"Error handling 500 error: {str(e)}")


def file_forbidden(file_path, forbidden):
    """Check if file path is in forbidden list or contains Archive"""
    is_forbidden = file_path in forbidden or "/Archive" in file_path
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
    if isinstance(data_file, bytes):
        return headers.encode() + data_file
    return (headers + str(data_file)).encode()


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
        
        # Don't send error response for polling requests - just return None
        if header_name in ['fileID', 'lastModID', 'userID'] and '/poll-updates' in headers_data:
            logger.debug(f"Skipping error response for polling header: {header_name}")
            return None
            
        error_msg = f"Header '{header_name}' not found"
        try:
            client_socket.send(ready_to_send("406 Not Acceptable", error_msg, "text/plain"))
        except:
            pass  # Ignore if client disconnected
        return None
    
    value = header_match.group(1)
    return value


def new_file(client_socket, PATH_TO_FOLDER, headers_data, value=""):
    """Create a new file for a user"""
    logger.info("Creating new file")
    
    use_encryption = should_encrypt_response(headers_data)
    
    user_id = get_header(client_socket, headers_data, r'userId:\s*(\S+)', "userId")
    if not user_id:
        logger.error("User ID not found in headers")
        return
    
    # Check if the user ID is AES encrypted
    is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
    if is_encrypted and is_encrypted.lower() == 'true':
        decrypted_user_id = rsa_manager.decryptAES(user_id, str(global_AES_key))
    else:
        decrypted_user_id = rsa_manager.decryptRSA(user_id)

    if not decrypted_user_id:
        logger.error("No valid userId header found")
        return
    
    filename = get_header(client_socket, headers_data, r'filename:\s*(\S+)', "filename")
    if not filename:
        logger.error("Filename not found in headers")
        return
    
    # Check if the filename is AES encrypted
    if is_encrypted and is_encrypted.lower() == 'true':
        decrypted_filename = rsa_manager.decryptAES(filename, str(global_AES_key))
    else:
        decrypted_filename = rsa_manager.decryptRSA(filename)

    if not decrypted_filename:
        logger.error("No valid filename found")
        return
    
    logger.info(f"Creating file '{decrypted_filename}' for user {decrypted_user_id}")
    
    # Check if filename already exists for this user
    existing_file = file_db.check_file_exists(decrypted_user_id, decrypted_filename)
    if existing_file:
        logger.warning(f"File '{decrypted_filename}' already exists for user {decrypted_user_id}")
        data = {
            "error": "File already exists",
            "fileId": 0
        }
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
            
            result2 = file_permissions_db.grant_access(file_id, decrypted_user_id, "owner")
            logger.info(f"Owner access granted, result: {result2['status']} - {result2['message']}")

            data = {
                "success": "File created successfully",
                "fileId": file_id,
                "fileAESKey": result['aes_key']
            }
        else:
            logger.error(f"File creation failed: {result['message']}")
            data = {"error": result['message']}
    
    # Encrypt response if needed
    response_data = encrypt_response_data(data, use_encryption)
    response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
    client_socket.send(response)


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
                    if linesLength == row + len(content.split("\n")):
                        print("in paste")
                        content = content + "\r"

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


def get_version(file_id, user_id, version, client_socket, use_encryption=False):
    """Get a specific version of a file"""
    logger.info(f"Get version {version} of file {file_id} for user {user_id}")
    
    if not file_id or not user_id or not version:
        logger.error("Missing required parameters: file_id, user_id, or version")
        raise ValueError("File ID, User ID or Version not provided")
    
    fullcontent = version_log_db.get_version_fullcontent(version, file_id)
    lastID = change_log_db.get_last_mod_id(file_id);
    
    if fullcontent is None:
        logger.warning(f"Version {version} not found for file {file_id}")
        data = {"error": "Version or content not found"}
    else:
        #logger.debug(f"Version content retrieved: {fullcontent[0][:100]}...")
        if lastID and not lastID == None:
            data = {"fullContent": fullcontent[0], "lastID": lastID}
        else:
            data = {"fullContent": fullcontent[0]}
    
    file_key = file_db.get_aes_key(file_id)
    if file_key is None:
        logger.error("No AES key found for file")
        raise ValueError("AES key not found for the file")
    # Encrypt response if needed
    response_data = encrypt_response_data(data, use_encryption, file_key)
    response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
    client_socket.send(response)


def save_modification(client_socket, file_id, file_name, file_path, modification_data, user_id):
    """Save file modifications"""
    logger.info(f"Saving modification for file {file_id} by user {user_id}")
    
    if not os.path.exists(file_path):
        logger.error(f"File path does not exist: {file_path}")
        if file_name == "File not found":
            client_socket.send(ready_to_send("200 OK", "File does not exist in database", "text/plain"))
        else:
            client_socket.send(ready_to_send("200 OK", "File does not exist in path", "text/plain"))
        return
        
    if file_name == "File not found":
        logger.error(f"File {file_id} not found in database")
        client_socket.send(ready_to_send("200 OK", "File does not exist in database", "text/plain"))
        return
        
    try:
        # Get the modification data from the match object
        logger.debug(f"Modification data: {modification_data}")
        
        # Parse the modification data
        try:
            modification = json.loads(modification_data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in modification data: {e}")
            client_socket.send(ready_to_send("400 Bad Request", "Invalid modification data format", "text/plain"))
            return
            
        # Validate required fields
        required_fields = ['content', 'row', 'action', 'linesLength']
        missing_fields = [field for field in required_fields if field not in modification]
        if missing_fields:
            logger.error(f"Missing required fields in modification data: {missing_fields}")
            client_socket.send(ready_to_send("400 Bad Request", f"Missing required fields: {', '.join(missing_fields)}", "text/plain"))
            return
            
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
            client_socket.send(ready_to_send("500 Internal Server Error", msg, "text/plain"))
            return
        
        client_socket.send(ready_to_send("200 OK", msg, "text/plain"))
        
    except Exception as e:
        logger.error(f"Error processing modification: {str(e)}")
        client_socket.send(ready_to_send("500 Internal Server Error", str(e), "text/plain"))


# GET request handlers
def handle_poll_updates(client_socket, headers_data):
    """Handle polling for file updates with encryption support"""
    try:
        # Check if request is encrypted
        encrypted_header = re.search(r'encrypted:\s*(\S+)', headers_data)
        is_encrypted = encrypted_header and encrypted_header.group(1).lower() == 'true'
        
        if is_encrypted:
            #logger.info("Handling encrypted poll-updates request")
            # Get encrypted headers - note the different regex pattern for encrypted data
            fileID_encrypted = get_header(client_socket, headers_data, r'fileID:\s*(\S+)', "fileID")
            lastModID_encrypted = get_header(client_socket, headers_data, r'lastModID:\s*(\S+)', "lastModID")
            userID_encrypted = get_header(client_socket, headers_data, r'userID:\s*(\S+)', "userID")
            
            if not fileID_encrypted or not lastModID_encrypted or not userID_encrypted:
                logger.error("Missing encrypted headers in poll-updates")
                return
            
            # Decrypt the headers
            try:
                fileID = rsa_manager.decryptAES(fileID_encrypted, str(global_AES_key))
                lastModID = rsa_manager.decryptAES(lastModID_encrypted, str(global_AES_key))
                userID = rsa_manager.decryptAES(userID_encrypted, str(global_AES_key))
                
                if not fileID or not lastModID or not userID:
                    logger.error("Failed to decrypt poll-updates headers")
                    return
                    
                logger.debug(f"Decrypted polling headers: fileID={fileID}, userID={userID}, lastModID={lastModID}")
                    
            except Exception as e:
                logger.error(f"Error decrypting poll-updates headers: {str(e)}")
                return
        else:
            #logger.info("Handling unencrypted poll-updates request")
            # Get unencrypted headers (original method)
            fileID = get_header(client_socket, headers_data, r'fileID:\s*(\d+)', "fileID")
            lastModID = get_header(client_socket, headers_data, r'lastModID:\s*(\d+)', "lastModID")
            userID = get_header(client_socket, headers_data, r'userID:\s*(\d+)', "userID")
            
            if not fileID or not lastModID or not userID:
                logger.error("Missing unencrypted headers in poll-updates")
                return
        
        # Convert to integers
        try:
            fileID = int(fileID)
            lastModID = int(lastModID)
            userID = int(userID)
        except ValueError as e:
            logger.error(f"Error converting headers to integers: {str(e)}")
            return
        
        updates = change_log_db.get_changes_for_user(fileID, lastModID, userID)
        
        # Get file AES key for encryption
        file_key = file_db.get_aes_key(fileID)
        if not file_key:
            logger.error("No AES key found for file")
            return
            
        if updates:
            # Encrypt the updates if encryption is enabled
            if is_encrypted:
                try:
                    # Ensure updates is a valid JSON string before encryption
                    updates_json = json.dumps(updates)
                    response_data = encrypt_response_data(updates_json, True, file_key)
                    logger.debug(f"Encrypted response data: {response_data}")
                except Exception as e:
                    logger.error(f"Error encrypting updates: {str(e)}")
                    return
            else:
                response_data = updates
            response = ready_to_send("200 OK", json.dumps(response_data), content_type="application/json")
        else:
            response = ready_to_send("200 OK", json.dumps("No updates"), content_type="application/json")
        
        client_socket.send(response)
        
    except BrokenPipeError:
        logger.warning("Client disconnected before poll-updates response could be sent")
    except Exception as e:
        logger.error(f"Error in poll-updates: {str(e)}")
        handle_500(client_socket)



def handle_save_request(client_socket, headers_data, request, PATH_TO_FOLDER):
    """Handle file save requests"""
    logger.info("Handling save request")
    
    if not global_AES_key:
        logger.error("Global AES key not available")
        client_socket.send(ready_to_send("500 Internal Server Error", "Server encryption error", "text/plain"))
        return
    
    file_id = get_header(client_socket, headers_data, r'fileID:\s*(\S+)', "fileID")
    user_id = get_header(client_socket, headers_data, r'userID:\s*(\S+)', "userID")
    
    if not file_id or not user_id:
        return

    # Check if the values are AES encrypted
    is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
    if is_encrypted and is_encrypted.lower() == 'true':
        if isinstance(file_id, str) and isinstance(user_id, str):
            file_id = rsa_manager.decryptAES(file_id, str(global_AES_key))
            user_id = rsa_manager.decryptAES(user_id, str(global_AES_key))
        else:
            logger.error("Invalid file_id or user_id type")
            return
    
    if not file_id or not user_id:
        logger.error("Failed to decrypt parameters or missing parameters")
        return
    
    #decoded_request = urllib.parse.unquote(request)
    match1 = re.search(r'/save\?modification=([^&]+)', request)
    if not match1:
        logger.error("Modification header not found in save request")
        raise ValueError("modification header not found")
    
    try:
        # Get the encrypted modification data
        encrypted_modification = match1.group(1)
        file_AES_key = str(file_db.get_aes_key(file_id))
        print("file_AES_key: " + str(file_AES_key))
        if not file_AES_key:
            logger.error(f"No AES key found for file ID: {file_id}")
            client_socket.send(ready_to_send("404 Not Found", "No AES key found for file", "text/plain"))
            return
        # Decrypt the modification data
        modification = rsa_manager.decryptAES(encrypted_modification, str(file_AES_key))
        if not modification:
            raise ValueError("Failed to decrypt modification data")
            
    except Exception as e:
        logger.error(f"Error decrypting modification data: {str(e)}")
        client_socket.send(ready_to_send("400 Bad Request", "Failed to decrypt modification data", "text/plain"))
        return

    file_name = file_db.get_filename_by_id(file_id)['filename']
    file_path = PATH_TO_FOLDER + "/uploads/" + file_name
    
    save_modification(client_socket, file_id, file_name, file_path, modification, user_id)


def handle_file_details(client_socket, headers_data):
    """Handle get file details requests"""
    logger.info("Handling file details request")
    
    try:
        use_encryption = should_encrypt_response(headers_data)
        
        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\S+)', "fileID")
        if not file_id:
            return

        # Decrypt file_id if it's AES encrypted
        is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
        if is_encrypted and is_encrypted.lower() == 'true':
            if isinstance(file_id, str):
                file_id = rsa_manager.decryptAES(file_id, str(global_AES_key))
            else:
                logger.error("Invalid file_id type")
                return
        
        if not file_id:
            logger.error("Failed to decrypt file ID")
            return

        file_details = file_db.get_file_details(file_id)
        if not file_details:
            data = {"error": "File not found"}
            response_data = encrypt_response_data(data, use_encryption)
            response = ready_to_send("404 Not Found", json.dumps(response_data), "application/json")
            client_socket.send(response)
            return

        users_with_access = file_permissions_db.get_users_with_access(file_id)
        data = {
            "filename": file_details['filename'],
            "users": users_with_access,
            "owner_id": file_details['owner_id']
        }
        
        # Encrypt response if needed
        response_data = encrypt_response_data(data, use_encryption)
        response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
        client_socket.send(response)
        
    except Exception as e:
        logger.error(f"Error in get-file-details: {str(e)}")
        error_data = {"error": str(e)}
        response_data = encrypt_response_data(error_data, use_encryption)
        response = ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json")
        client_socket.send(response)


def handle_user_files(client_socket, headers_data):
    """Handle get user files requests"""
    logger.info("Handling user files request")
    
    try:
        use_encryption = should_encrypt_response(headers_data)
        
        user_id = get_header(client_socket, headers_data, r'userId:\s*(\S+)', "userId")
        is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
        
        if not user_id:
            error_data = {'error': "not user id found"}
            response_data = encrypt_response_data(error_data, use_encryption)
            response = ready_to_send("400 Bad Request", json.dumps(response_data), "application/json")
            client_socket.send(response)
            return
            
        if is_encrypted and is_encrypted.lower() == 'true':
            logger.info("Decrypting AES encrypted user ID")
            if isinstance(user_id, str):
                try:
                    # Decrypt the AES encrypted user ID
                    decrypted_user_id = rsa_manager.decryptAES(user_id, str(global_AES_key))
                    if not decrypted_user_id:
                        raise ValueError("Failed to decrypt user ID")
                except Exception as e:
                    logger.error(f"Error decrypting user ID: {str(e)}")
                    error_data = {'error': 'Failed to decrypt user ID'}
                    response_data = encrypt_response_data(error_data, use_encryption)
                    response = ready_to_send("400 Bad Request", json.dumps(response_data), "application/json")
                    client_socket.send(response)
                    return
            else:
                logger.error("Invalid user_id type")
                return
        else:
            logger.info("Using unencrypted user ID")
            decrypted_user_id = user_id

        if not decrypted_user_id:
            logger.error("No valid userId header found")
            return
        
        decrypted_user_id = int(decrypted_user_id)
        logger.info(f"Getting files for user ID: {decrypted_user_id}")
        
        user_files = file_permissions_db.get_user_access_files(decrypted_user_id)
        file_ids = [file['fileID'] for file in user_files]
        file_names = [file['filename'] for file in user_files]
        
        logger.info(f"Found {len(file_ids)} files for user {decrypted_user_id}")
        
        data = {
            'filesId': file_ids,
            'filenames': file_names
        }
        
        # Encrypt response if needed
        response_data = encrypt_response_data(data, use_encryption)
        response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
        client_socket.send(response)
        
    except Exception as e:
        logger.error(f"Error getting user files: {str(e)}")
        error_data = {'error': str(e)}
        response_data = encrypt_response_data(error_data, use_encryption)
        response = ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json")
        client_socket.send(response)


def handle_version_details(client_socket, headers_data):
    """Handle get version details requests"""
    logger.info("Handling version details request")
    
    try:
        use_encryption = should_encrypt_response(headers_data)
        
        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\S+)', "fileID")
        if not file_id:
            return
        
        # Decrypt file_id if it's AES encrypted
        is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
        if is_encrypted and is_encrypted.lower() == 'true':
            if isinstance(file_id, str):
                file_id = rsa_manager.decryptAES(file_id, str(global_AES_key))
            else:
                logger.error("Invalid file_id type")
                return
        
        if not file_id:
            logger.error("Failed to decrypt file ID")
            return
        
        versions = version_log_db.get_versions_by_fileID(file_id)
        data = {
            'versions': versions,
            'owner_id': file_db.get_owner_id(file_id)
        }
        
        # Encrypt response if needed
        response_data = encrypt_response_data(data, use_encryption)
        response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
        client_socket.send(response)
        
    except Exception as e:
        logger.error(f"Error in get-version-details: {str(e)}")
        error_data = {"error": str(e)}
        response_data = encrypt_response_data(error_data, use_encryption)
        response = ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json")
        client_socket.send(response)


def handle_get_version(client_socket, headers_data):
    """Handle get version requests"""
    logger.info("Handling get version request")
    
    use_encryption = should_encrypt_response(headers_data)
    
    file_id = get_header(client_socket, headers_data, r'fileID:\s*(\S+)', "fileID")
    user_id = get_header(client_socket, headers_data, r'userID:\s*(\S+)', "userID")
    version = get_header(client_socket, headers_data, r'version:\s*(\S+)', "version")
    
    if not file_id or not user_id or not version:
        return
    
    # Decrypt parameters if they're AES encrypted
    is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
    if is_encrypted and is_encrypted.lower() == 'true':
        if isinstance(file_id, str) and isinstance(user_id, str):
            file_id = rsa_manager.decryptAES(file_id, str(global_AES_key))
            aes_key = file_db.get_aes_key(file_id)
            user_id = rsa_manager.decryptAES(user_id, str(aes_key))
            version = version
        else:
            logger.error("Invalid file_id or user_id type")
            return
    
    if not file_id or not user_id or not version:
        logger.error("Failed to decrypt parameters")
        return
    
    get_version(file_id, user_id, version, client_socket, use_encryption)


def handle_viewer_status(client_socket, headers_data):
    """Handle check viewer status requests"""
    logger.info("Handling viewer status check")
    
    use_encryption = should_encrypt_response(headers_data)
    
    file_id = get_header(client_socket, headers_data, r'fileId:\s*(\S+)', "fileId")
    user_id = get_header(client_socket, headers_data, r'userId:\s*(\S+)', "userId")
    
    if not file_id or not user_id:
        return
    
    # Decrypt parameters if they're AES encrypted
    is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
    if is_encrypted and is_encrypted.lower() == 'true':
        if isinstance(file_id, str) and isinstance(user_id, str):
            file_id = rsa_manager.decryptAES(file_id, str(global_AES_key))
            aes_key = file_db.get_aes_key(file_id)
            user_id = rsa_manager.decryptAES(user_id, str(aes_key))
        else:
            logger.error("Invalid file_id or user_id type")
            return
    
    if not file_id or not user_id:
        logger.error("Failed to decrypt parameters")
        return
    
    is_editor_or_owner = file_permissions_db.is_editor_or_owner(file_id, user_id)
    data = {"isViewer": not is_editor_or_owner}
    
    # Encrypt response if needed
    response_data = encrypt_response_data(data, use_encryption)
    response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
    client_socket.send(response)


def handle_new_file_request(client_socket, headers_data, PATH_TO_FOLDER):
    """Handle new file creation requests"""
    logger.info("Handling new file request")
    
    new_file(client_socket, PATH_TO_FOLDER, headers_data,"// New file'")


def handle_load_file(client_socket, headers_data, PATH_TO_FOLDER):
    """Handle file loading requests"""
    logger.info("Handling load file request")
    
    try:
        use_encryption = should_encrypt_response(headers_data)
        
        fileId = get_header(client_socket, headers_data, r'fileId:\s*(\S+)', "fileId")
        if not fileId:
            logger.info(f"Found user ID using pattern userId: {fileId}")
            return
        
        # Check if the file ID is AES encrypted
        is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
        if is_encrypted and is_encrypted.lower() == 'true':
            decrypted_file_id = rsa_manager.decryptAES(fileId, str(global_AES_key))
        else:
            decrypted_file_id = rsa_manager.decryptRSA(fileId)

        if not decrypted_file_id:
            logger.error("No valid userId header found")
            return

        file_status_and_name = file_db.get_filename_by_id(decrypted_file_id)
        filename = file_status_and_name['filename']
        status = file_status_and_name['status']
        
        if status == 404:
            logger.warning(f"File not found: {filename}")
            data = {"error": filename}
            response_data = encrypt_response_data(data, use_encryption)
            response = ready_to_send("404 Not Found", json.dumps(response_data), "application/json")
            client_socket.send(response)
        else:
            file_path = f"{PATH_TO_FOLDER}/uploads/{filename}"
            logger.info(f"Loading file ID: {decrypted_file_id}, name: {filename}")
            
            if not os.path.exists(file_path):
                content = ''
            else:
                with open(file_path, 'r') as file:
                    content = file.read()
            fileAESKey = file_db.get_aes_key(decrypted_file_id)
            logger.info("fileAESKey: " + str(fileAESKey))
            lastModID = change_log_db.get_last_mod_id(decrypted_file_id)
            data = {
                'lastModID': lastModID,
                'fullContent': content,
                'fileAESKey': fileAESKey
            }
            
            # Encrypt response if needed
            response_data = encrypt_response_data(data, use_encryption)
            response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
            client_socket.send(response)
            logger.info("File loaded successfully")

    except Exception as e:
        logger.error(f"Error in load handler: {str(e)}")
        error_data = {'error': str(e)}
        response_data = encrypt_response_data(error_data, use_encryption)
        response = ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json")
        client_socket.send(response)


def handle_public_key(client_socket):
    """Handle public key requests"""
    logger.info("Handling public key request")
    
    try:
        public_key_string = rsa_manager.get_public_key_string()
        response_data = json.dumps({"publicKey": public_key_string})
        response = ready_to_send("200 OK", response_data, "application/json")
        client_socket.send(response)
        
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
        logger.info(f"Serving file: {request}, type: {file_type}")

        if "imgs/" in request:
            try:
                with open(PATH_TO_FOLDER + request, "rb") as file3:
                    photo = file3.read()
               
                response = ready_to_send("200 ok",photo,file_type)
                client_socket.send(response)
                
            except Exception as e:
                logger.error(f"Error serving image file {request}: {e}")
                handle_500(client_socket)
        else:
            try:
                with open(PATH_TO_FOLDER + request, "r", encoding='utf-8') as file2:
                    code = file2.read()
                response = ready_to_send("200 ok",code,file_type)
                client_socket.send(response)
                
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
        elif "/get-version" in request:
            handle_get_version(client_socket, headers_data)
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
def handle_login(client_socket, content_length,headers_data):
    """Handle login requests"""
    logger.info("Handling login request")

    body = client_socket.recv(content_length).decode()
    data = json.loads(body)
    
    # Check if data is encrypted
    if 'encrypted' in data and data['encrypted']:
        logger.debug("Processing encrypted login credentials")
        decrypted_username = rsa_manager.decryptRSA(data.get('username'))
        decrypted_password = rsa_manager.decryptRSA(data.get('password'))
        
        if not decrypted_username or not decrypted_password:
            logger.error("Failed to decrypt login credentials")
            response = {'status': 400, 'message': 'Failed to decrypt credentials'}
            client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json"))
            return
            
        username = decrypted_username
        password = decrypted_password
    else:
        logger.debug("Processing unencrypted login credentials")
        username = data.get('username')
        password = data.get('password')
    
    logger.info(f"Login attempt for username: {username}")
    clientPublicRSA = data.get('public_key_client')
    if not clientPublicRSA:
        response = ready_to_send("404 Not Found", 'public-key-client not found', "application/json")
        client_socket.send(response)
        return
    response = user_db.login(username, password, clientPublicRSA)
    if response['status'] == 200:
        logger.info(f"Login successful for: {username}")
    else:
        logger.warning(f"Login failed for: {username}")
    
    client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json"))


def handle_signup(client_socket, content_length):
    """Handle signup requests"""
    logger.info("Handling signup request")
    
    body = client_socket.recv(content_length).decode()
    data = json.loads(body)
    
    # Check if data is encrypted
    if 'encrypted' in data and data['encrypted']:
        logger.debug("Processing encrypted signup credentials")
        decrypted_username = rsa_manager.decryptRSA(data.get('username'))
        decrypted_password = rsa_manager.decryptRSA(data.get('password'))
        
        if not decrypted_username or not decrypted_password:
            logger.error("Failed to decrypt signup credentials")
            response = {'status': 400, 'message': 'Failed to decrypt credentials'}
            client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json"))
            return
            
        username = decrypted_username
        password = decrypted_password
    else:
        logger.debug("Processing unencrypted signup credentials")
        username = data.get('username')
        password = data.get('password')
    
    logger.info(f"Signup attempt for username: {username}")
    clientPublicRSA = data.get('public_key_client')
    if not clientPublicRSA:
        response = ready_to_send("404 Not Found", 'public-key-client not found', "application/json")
        client_socket.send(response)
        return
    response = user_db.signup(username, password,clientPublicRSA)
    
    if response['status'] == 201:
        logger.info(f"User registration successful: {username}")
    else:
        logger.warning(f"User registration failed: {username}")
    
    client_socket.send(ready_to_send(response['status'], json.dumps(response), "application/json"))


def handle_user_permissions(client_socket, content_length, headers_data, request):
    """Handle grant/revoke user permissions requests"""
    logger.info(f"Handling user permissions request: {request}")
    
    use_encryption = should_encrypt_response(headers_data)
    
    body = client_socket.recv(content_length).decode()
    
    # Decrypt body if it's AES encrypted
    is_encrypted = 'encrypted' in headers_data and 'true' in headers_data
    if is_encrypted:
        try:
            body_data = json.loads(body)
            if body_data.get('encrypted'):
                decrypted_body = rsa_manager.decryptAES(body_data.get('data'), str(global_AES_key))
                data = json.loads(str(decrypted_body))
            else:
                data = body_data
        except Exception as e:
            logger.error(f"Error decrypting request body: {str(e)}")
            data = json.loads(body)
    else:
        data = json.loads(body)
    
    username = data.get('username')
    userID = user_db.get_user_id(username)
    fileID = data.get('fileID')
    role = data.get('role')
    ownerID_encrypted = data.get('ownerID_encrypted')
    aes_key = file_db.get_aes_key(fileID) 
    ownerID = rsa_manager.decryptAES(str(ownerID_encrypted), str(aes_key))

    if not userID:
        logger.error(f"User not found: {username}")
        error_data = {"message": "Not a user!!"}
        response_data = encrypt_response_data(error_data, use_encryption)
        client_socket.send(ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json"))
    elif not ownerID or not file_db.is_owner(int(fileID), int(ownerID)):
        logger.error(f"Permission denied: User {ownerID} is not owner of file {fileID}")
        error_data = {"message": "Not owner!!"}
        response_data = encrypt_response_data(error_data, use_encryption)
        client_socket.send(ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json"))
    else:
        if "/revoke-user-to-file" in request:
            logger.info(f"Revoking access for user {userID} from file {fileID}")
            response = file_permissions_db.revoke_access(fileID, userID)
        elif "/grant-user-to-file" in request:
            logger.info(f"Granting {role} access for user {userID} to file {fileID}")
            response = file_permissions_db.grant_access(fileID, userID, role)
        
        # Encrypt response if needed
        response_data = encrypt_response_data(response, use_encryption)
        client_socket.send(ready_to_send(response['status'], json.dumps(response_data), "application/json"))


def handle_save_version(client_socket, content_length, headers_data):
    """Handle save new version request"""
    logger.info("Handling save new version request")
    
    try:
        use_encryption = should_encrypt_response(headers_data)
        
        content = get_content_of_upload(client_socket, content_length)
        if not content:
            raise ValueError("No content received")

        data_json = json.loads(content)
        if data_json.get('encrypted'):
            encrypted_data = data_json.get('data')
            if not encrypted_data:
                raise ValueError("No encrypted data received")
            
            # Decrypt the data using global AES key
            decrypted_data = rsa_manager.decryptAES(encrypted_data, str(global_AES_key))
            if not decrypted_data:
                raise ValueError("Failed to decrypt data")
            
            data_json = json.loads(decrypted_data)
        
        file_id = data_json.get('fileID')
        aes_key = file_db.get_aes_key(str(file_id))
        user_id = str(rsa_manager.decryptAES(data_json.get('userID_encrpted'),str(aes_key)))
        content = str(rsa_manager.decryptAES(data_json.get('content'),str(aes_key)))
        print("user: " + user_id)
        
        if not all([file_id, user_id, content]):
            raise ValueError("Missing required parameters")
            
        if file_permissions_db.is_viewer(file_id, user_id):
            logger.warning(f"User {user_id} is a viewer and cannot save new versions")
            error_data = {"error": "Viewers cannot save new versions"}
            response_data = encrypt_response_data(error_data, use_encryption)
            response = ready_to_send("403 Forbidden", json.dumps(response_data), "application/json")
            client_socket.send(response)
            return
            
        save_new_version(file_id, user_id, content, client_socket, use_encryption)
    except ValueError as e:
        logger.error(f"Error in save version request: {str(e)}")
        error_data = {"error": str(e)}
        response_data = encrypt_response_data(error_data, use_encryption)
        response = ready_to_send("400 Bad Request", json.dumps(response_data), "application/json")
        client_socket.send(response)
    except Exception as e:
        logger.error(f"Error saving new version: {str(e)}")
        error_data = {"error": "Internal server error"}
        response_data = encrypt_response_data(error_data, use_encryption)
        response = ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json")
        client_socket.send(response)


def handle_upload_file(client_socket, content_length, headers_data, PATH_TO_FOLDER):
    """Handle file upload requests"""
    logger.info("Handling file upload request")
    
    content = get_content_of_upload(client_socket, content_length)
    if content:
        # Decrypt content if it's AES encrypted
        content_json = json.loads(content)
        if content_json.get('encrypted'):
            decrypted_content = rsa_manager.decryptAES(content_json.get('content'), str(global_AES_key))
            content_json['content'] = decrypted_content
        
        new_file(client_socket, PATH_TO_FOLDER, headers_data, content_json['content'])
    else:
        logger.error("No content received for file upload")
        client_socket.send(ready_to_send("400 Bad Request", "Broken pipe or No content"))


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
        
        if "/login" in request: #rsa
            handle_login(client_socket, content_length, headers_data) 
        elif "/signup" in request:  #rsa
            handle_signup(client_socket, content_length)    
        elif "/grant-user-to-file" in request or "/revoke-user-to-file" in request:
            handle_user_permissions(client_socket, content_length, headers_data, request)
        elif "/save-new-version" in request:
            handle_save_version(client_socket, content_length, headers_data)
        elif "/disconnection" in request:
            logger.info("Client disconnection request")
            if content_length > 0:
                client_socket.recv(content_length).decode()
            return
        elif "/get-global-aes" in request: 
            handle_global_aes(client_socket, content_length)
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
        use_encryption = should_encrypt_response(headers_data)
        
        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\S+)', "fileID")
        user_id = get_header(client_socket, headers_data, r'userID:\s*(\S+)', "userID")
        version = get_header(client_socket, headers_data, r'version:\s*(\S+)', "version")
        
        # Decrypt parameters if they're AES encrypted
        is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
        if is_encrypted and is_encrypted.lower() == 'true':
            if isinstance(file_id, str) and isinstance(user_id, str) and  isinstance(version, str):
                file_id = rsa_manager.decryptAES(file_id, str(global_AES_key))
                aes_key = file_db.get_aes_key(file_id)
                user_id = rsa_manager.decryptAES(user_id, str(aes_key))
                version = version
            else:
                logger.error("Invalid file_id or user_id type")
                return
        
        if not file_id or not user_id or not version:
            logger.error("Failed to decrypt parameters or missing parameters")
            return
        
        if file_permissions_db.is_viewer(file_id, user_id):
            logger.warning(f"User {user_id} is a viewer and cannot delete versions")
            error_data = {"error": "Viewers cannot delete versions"}
            response_data = encrypt_response_data(error_data, use_encryption)
            response = ready_to_send("403 Forbidden", json.dumps(response_data), "application/json")
            client_socket.send(response)
            return
            
        delete_version(file_id, user_id, version, client_socket, use_encryption)
    except ValueError as e:
        logger.error(f"Error in delete version request: {str(e)}")
        error_data = {"error": str(e)}
        response_data = encrypt_response_data(error_data, use_encryption)
        response = ready_to_send("400 Bad Request", json.dumps(response_data), "application/json")
        client_socket.send(response)
    except Exception as e:
        logger.error(f"Unexpected error in delete version request: {str(e)}")
        handle_500(client_socket)


def handle_delete_file(client_socket, headers_data, PATH_TO_FOLDER):
    """Handle delete file requests"""
    logger.info("Handling delete file request")
    
    try:
        use_encryption = should_encrypt_response(headers_data)
        
        file_id = get_header(client_socket, headers_data, r'fileID:\s*(\S+)', "fileID")
        user_id = get_header(client_socket, headers_data, r'userID:\s*(\S+)', "userID")
        
        # Decrypt parameters if they're AES encrypted
        is_encrypted = get_header(client_socket, headers_data, r'encrypted:\s*(\S+)', "encrypted")
        if is_encrypted and is_encrypted.lower() == 'true':
            if isinstance(file_id, str) and isinstance(user_id, str):
                file_id = rsa_manager.decryptAES(file_id, str(global_AES_key))
                aes_key = file_db.get_aes_key(file_id)
                user_id = rsa_manager.decryptAES(user_id, str(aes_key))
            else:
                logger.error("Invalid file_id or user_id type")
                return
        
        if not file_id or not user_id:
            logger.error("Failed to decrypt parameters or missing parameters")
            return
        
        if not file_db.is_owner(int(file_id), int(user_id)):
            logger.error(f"User {user_id} is not owner of file {file_id}")
            error_data = "Not owner!!"
            response_data = encrypt_response_data(error_data, use_encryption)
            client_socket.send(ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json"))
            return

        logger.info(f"Deleting file {file_id}")
        file_result = file_db.delete_file(file_id)

        if file_result['status'] != 200:
            error_data = {"error": file_result['message']}
            response_data = encrypt_response_data(error_data, use_encryption)
            response = ready_to_send(str(file_result['status']), json.dumps(response_data), "application/json")
            client_socket.send(response)
            return

        permissions_result = file_permissions_db.delete_file_permissions(file_id)
        try:
            change_result = change_log_db.delete_file_changes(file_id)
            if change_result['staus'] == 200:
                logger.info(change_result['message'])
            else:
                 logger.error(change_result['message'])
        except:
            logger.error("Failed to delete file changes")
        if permissions_result['status'] != 200:
            error_data = {"error": permissions_result['message']}
            response_data = encrypt_response_data(error_data, use_encryption)
            response = ready_to_send(str(permissions_result['status']), json.dumps(response_data), "application/json")
            client_socket.send(response)
            return

        # Delete file from filesystem
        try:
            file_path = os.path.join(PATH_TO_FOLDER, "uploads", file_result['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted from filesystem: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file from filesystem: {str(e)}")

        success_data = {"message": "File deleted successfully"}
        response_data = encrypt_response_data(success_data, use_encryption)
        response = ready_to_send("200 OK", json.dumps(response_data), "application/json")
        client_socket.send(response)
        
    except Exception as e:
        logger.error(f"Error in delete-file: {str(e)}")
        error_data = {"error": str(e)}
        response_data = encrypt_response_data(error_data, use_encryption)
        response = ready_to_send("500 Internal Server Error", json.dumps(response_data), "application/json")
        client_socket.send(response)


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
    PATH_TO_FOLDER = r"/Users/hila/CEOs"
    FORBIDDEN = {
        f"{PATH_TO_FOLDER}/status_code/404.png",
        f"{PATH_TO_FOLDER}/status_code/life.txt",
        f"{PATH_TO_FOLDER}/status_code/500.png",
        f"{PATH_TO_FOLDER}/users.db",
        f"{PATH_TO_FOLDER}/__pycache__",
        f"{PATH_TO_FOLDER}/class_users.py",
        f"{PATH_TO_FOLDER}/notes.txt",
        f"{PATH_TO_FOLDER}/start_servers.py",
        f"{PATH_TO_FOLDER}/.venv",
        f"{PATH_TO_FOLDER}/.vscode",
        f"{PATH_TO_FOLDER}/.idea"
    }

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
                # Extract the path and query parameters
                request_parts = request.split('?', 1)
                path = request_parts[0]
                logger.info(f"{client_ip} → {method} {path}")

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
            client_socket.send(error_response)

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

def save_new_version(file_id, user_id, content, client_socket, use_encryption=False):
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
    
    # Encrypt response if needed
    response_data = encrypt_response_data({"message": result['message']}, use_encryption)
    response = ready_to_send(result['status'], json.dumps(response_data), "application/json")
    client_socket.send(response)

def delete_version(file_id, user_id, version, client_socket, use_encryption=False):
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
    
    # Encrypt response if needed
    response_data = encrypt_response_data({"message": result['message']}, use_encryption)
    response = ready_to_send(result['status'], json.dumps(response_data), "application/json")
    client_socket.send(response)

def handle_global_aes(client_socket, content_length):
    """Handle global AES key requests"""
    logger.info("Handling global AES key request")
    
    try:
        # Read the request body
        
        body = client_socket.recv(content_length).decode()
        data = json.loads(body)
        
        # Get client's public RSA key
        client_public_key = data.get('public_key_client')
        if not client_public_key:
            logger.error("Client public key not provided")
            response = ready_to_send("400 Bad Request", json.dumps({"error": "Client public key not provided"}), "application/json")
            client_socket.send(response)
            return
        
        # Encrypt the AES key with client's public RSA key
        encrypted_aes_key = rsa_manager.encryptWithClientKey(global_AES_key,client_public_key )
        
        # Send the encrypted AES key back to the client
        response_data = json.dumps({"AESKey": encrypted_aes_key})
        response = ready_to_send("200 OK", response_data, "application/json")
        client_socket.send(response)
        
        logger.info("Global AES key sent successfully: " + str(global_AES_key))
        
    except Exception as e:
        logger.error(f"Error handling global AES key request: {str(e)}")
        response = ready_to_send("500 Internal Server Error", json.dumps({"error": str(e)}), "application/json")
        client_socket.send(response)

if __name__ == "__main__":
    start_main_server()