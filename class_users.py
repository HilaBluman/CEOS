import json
import sqlite3
import random
import threading
import secrets
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class EncryptionHandler:
    @staticmethod
    def encrypt_data(data, aes_key):
        """
        Encrypt data using AES-256-CBC with the provided key.
        Returns base64 encoded encrypted data.
        """
        try:
            # Convert the base64 key back to bytes
            key = base64.b64decode(aes_key)
            
            # Generate a random IV
            iv = secrets.token_bytes(16)
            
            # Create cipher
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # Pad and encrypt the data
            padded_data = pad(data.encode(), AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Combine IV and encrypted data and encode to base64
            return base64.b64encode(iv + encrypted_data).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {str(e)}")
            return None

    @staticmethod
    def decrypt_data(encrypted_data, aes_key):
        """
        Decrypt AES-256-CBC encrypted data using the provided key.
        Returns the decrypted string.
        """
        try:
            # Convert the base64 key back to bytes
            key = base64.b64decode(aes_key)
            
            # Decode the encrypted data from base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract IV and ciphertext
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            # Create cipher
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # Decrypt and unpad the data
            decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {str(e)}")
            return None

    @staticmethod
    def encrypt_connection_data(data, aes_key):
        """
        Encrypt data for connection and return a dictionary with encrypted data and status.
        """
        if not data or not aes_key:
            return {'status': 400, 'message': 'Missing data or AES key'}
        
        encrypted_data = EncryptionHandler.encrypt_data(data, aes_key)
        if not encrypted_data:
            return {'status': 500, 'message': 'Encryption failed'}
        
        return {
            'status': 200,
            'encrypted_data': encrypted_data
        }

    @staticmethod
    def decrypt_connection_data(encrypted_data, aes_key):
        """
        Decrypt data from connection and return a dictionary with decrypted data and status.
        """
        if not encrypted_data or not aes_key:
            return {'status': 400, 'message': 'Missing encrypted data or AES key'}
        
        decrypted_data = EncryptionHandler.decrypt_data(encrypted_data, aes_key)
        if not decrypted_data:
            return {'status': 500, 'message': 'Decryption failed'}
        
        return {
            'status': 200,
            'decrypted_data': decrypted_data
        }

class UserDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_user_database()

    def create_user_database(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Create users table with userID as a numeric type
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                userID INTEGER UNIQUE PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def generate_unique_userID(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        while True:
            userID = random.randint(1000, 9999)  # Generate a random userID
            cursor.execute('SELECT COUNT(*) FROM users WHERE userID = ?', (userID,))
            count = cursor.fetchone()[0]
            if count == 0:  # If userID is unique
                return userID  # Return the unique userID

    def signup(self, username, password):
        # Check password length
        if len(password) < 4:
            return {'status': 400, 'message': 'Password must be at least 4 characters long.'}

        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        userID = self.generate_unique_userID()  # Get a unique userID

        try:
            # Insert the userID, username, and password
            cursor.execute('INSERT INTO users (userID, username, password) VALUES (?, ?, ?)', (userID, username, password))
            conn.commit()
            return {'status': 201, 'message': 'User created successfully with userID: {}'.format(userID)}
        except sqlite3.IntegrityError:
            return {'status': 409, 'message': 'Username already exists.'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()

    def login(self, username, password):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT userID FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            userID = user['userID']  # Get the userID from the fetched user
            return {'status': 200, 'message': 'Login successful.', 'userId': userID}  # Include userID in the response
        else:
            return {'status': 401, 'message': 'Invalid username or password.'}
        
    def get_user_id(self, username):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT userID FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        return int(result[0]) if result else None

class FileInfoDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_file_info_table()

    def encrypt_data(self, data, aes_key):
        """
        Encrypt data using AES-256-CBC with the provided key.
        Returns base64 encoded encrypted data.
        """
        try:
            # Convert the base64 key back to bytes
            key = base64.b64decode(aes_key)
            
            # Generate a random IV
            iv = secrets.token_bytes(16)
            
            # Create cipher
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # Pad and encrypt the data
            padded_data = pad(data.encode(), AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Combine IV and encrypted data and encode to base64
            return base64.b64encode(iv + encrypted_data).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {str(e)}")
            return None

    def decrypt_data(self, encrypted_data, aes_key):
        """
        Decrypt AES-256-CBC encrypted data using the provided key.
        Returns the decrypted string.
        """
        try:
            # Convert the base64 key back to bytes
            key = base64.b64decode(aes_key)
            
            # Decode the encrypted data from base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract IV and ciphertext
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            # Create cipher
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # Decrypt and unpad the data
            decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
            
            return decrypted_data.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {str(e)}")
            return None

    def generate_aes_key(self):
        """
        Generates a secure AES key using cryptographically strong random bytes.
        Returns a base64 encoded string of 32 bytes (256 bits) which is suitable for AES-256.
        """
        key_bytes = secrets.token_bytes(32)
        key_string = base64.b64encode(key_bytes).decode('utf-8')
        return key_string

    def create_file_info_table(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Create fileInfo table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fileInfo (
                fileID INTEGER UNIQUE PRIMARY KEY,
                filename TEXT NOT NULL,
                ownerID INTEGER,
                aes_key TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ownerID) REFERENCES users(userID)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_owner_id(self, file_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT ownerID FROM fileInfo WHERE fileID = ?', (file_id,))
            result = cursor.fetchone()
            return result['ownerID'] if result else None
        except Exception as e:
            print(f"Error getting owner ID: {str(e)}")
            return None
        finally:
            conn.close()

    def is_owner(self, fileID, userID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT ownerID FROM fileInfo WHERE fileID = ?', (fileID,))
        owner = cursor.fetchone()
        conn.close()
        if owner and owner['ownerID'] == userID:
            return True  # The user is the owner of the file
        else:
            return False  # The user is not the owner of the file

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_aes_key(self, file_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT aes_key FROM fileInfo WHERE fileID = ?', (file_id,))
            result = cursor.fetchone()
            return result['aes_key'] if result else None
        except Exception as e:
            print(f"Error getting AES key: {str(e)}")
            return None
        finally:
            conn.close()

    def check_file_exists(self, ownerID, filename):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT fileID FROM fileInfo 
                WHERE ownerID = ? AND filename = ?
            ''', (ownerID, filename))
            
            result = cursor.fetchone()
            if result:
                return result['fileID']  # Return the fileID if file exists
            return None  # Return None if file doesn't exist
                
        except Exception as e:
            print(f"Error checking file existence: {str(e)}")
            return None
        finally:
            conn.close()

    def check_aes_key_exists(self, aes_key):
        """
        Checks if an AES key already exists in the database.
        Returns True if the key exists, False otherwise.
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM fileInfo WHERE aes_key = ?', (aes_key,))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            return False
        finally:
            conn.close()

    def add_file(self, filename, ownerID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        while True:
            aes_key = self.generate_aes_key()
            if not self.check_aes_key_exists(aes_key):
                break
        
        try:
            cursor.execute('INSERT INTO fileInfo (filename, ownerID, aes_key) VALUES (?, ?, ?)', 
                         (filename, ownerID, aes_key))
            conn.commit()
            return {'status': 201, 'message': 'File created successfully.', 'AES_key': aes_key}
        except sqlite3.IntegrityError:
            return {'status': 409, 'message': 'File name already exists.', 'AES_key': aes_key }
        except Exception as e:
            return {'status': 500, 'message': str(e), 'AES_key': aes_key }
        finally:
            conn.close()

    # not in use add use.
    def update_file_timestamp(self, fileID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE fileInfo SET updated_at = CURRENT_TIMESTAMP WHERE fileID = ?', (fileID,))
            conn.commit()
            return {'status': 200, 'message': 'File timestamp updated successfully.'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()

    def get_file(self, fileID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM fileInfo WHERE fileID = ?', (fileID,))
        file = cursor.fetchone()
        
        if file:
            return dict(file)  # Return file details as a dictionary
        else:
            return None

    def get_filename_by_id(self, fileID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT filename FROM fileInfo WHERE fileID = ?', (fileID,))
            result = cursor.fetchone()
            
            if result:
                return {'status': 200, 'filename': result['filename']}
            else:
                return {'status': 404, 'filename': 'File not found'}
                
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()

    def get_file_details(self, file_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT filename, ownerID FROM fileInfo WHERE fileID = ?', (file_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'filename': result[0],
                'owner_id': result[1]
            }
        return None

    def delete_file(self, file_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # First get the filename to delete the actual file
            cursor.execute('SELECT filename FROM fileInfo WHERE fileID = ?', (file_id,))
            result = cursor.fetchone()
            if not result:
                return {'status': 404, 'message': 'File not found'}
            
            filename = result['filename']
            
            # Delete from fileInfo table
            cursor.execute('DELETE FROM fileInfo WHERE fileID = ?', (file_id,))
            conn.commit()
            
            return {'status': 200, 'message': 'File deleted successfully', 'filename': filename}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()

class FilePermissionsDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_file_permissions_table()

    def create_file_permissions_table(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Create filePermissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filePermissions (
                fileID INTEGER,
                userID INTEGER,
                role TEXT,
                PRIMARY KEY (fileID, userID),
                FOREIGN KEY (fileID) REFERENCES fileInfo(fileID),
                FOREIGN KEY (userID) REFERENCES users(userID)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def grant_access(self, fileID, userID, role=None):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            if role is not None:
                cursor.execute('INSERT INTO filePermissions (fileID, userID, role) VALUES (?, ?, ?)', (fileID, userID, role))
            else:
                cursor.execute('INSERT INTO filePermissions (fileID, userID) VALUES (?, ?)', (fileID, userID))
            conn.commit()
            return {'status': 201, 'message': 'Access granted successfully.'}
        except sqlite3.IntegrityError:
            return {'status': 409, 'message': 'User already has access to this file.'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()

    def revoke_access(self, fileID, userID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        if not self.has_access(fileID, userID):
            conn.close()
            return {'status': 400, 'message': 'User does not have access to this file.'}
        
        cursor.execute('DELETE FROM filePermissions WHERE fileID = ? AND userID = ?', (fileID, userID))
        conn.commit()
        conn.close()
        return {'status': 200, 'message': 'Access revoked successfully.'}

    def get_user_access_files(self, userID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fp.fileID, fileInfo.filename
            FROM filePermissions fp
            JOIN fileInfo ON fp.fileID = fileInfo.fileID
            WHERE fp.userID = ?
        ''', (userID,))
        
        files = cursor.fetchall()
        return [{'fileID': file[0], 'filename': file[1]} for file in files]  # Return list of files as dictionaries

    def has_access(self, fileID, userID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) AS accessCount
            FROM filePermissions
            WHERE fileID = ? AND userID = ?
        ''', (fileID, userID))
        
        access_count = cursor.fetchone()['accessCount']
        
        if access_count > 0:
            return True  # User has access to the file
        else:
            return False  # User does not have access to the file
    
    def is_editor_or_owner(self, fileID, userID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role
            FROM filePermissions as fp
            WHERE fp.fileID = ? AND fp.userID = ?
        ''', (fileID, userID))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            if result['role'] == 'editor' or result['role'] == 'owner':
                return True  
            else:
                return False 
        else:
            return False  

    def get_users_with_access(self, file_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.username, fp.role 
            FROM filePermissions fp
            JOIN users u ON fp.userID = u.userID
            WHERE fp.fileID = ?
        ''', (file_id,))
        results = cursor.fetchall()
        conn.close()
        
        return [{'username': row[0], 'role': row[1] or 'user'} for row in results]

    def delete_file_permissions(self, file_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM filePermissions WHERE fileID = ?', (file_id,))
            conn.commit()
            return {'status': 200, 'message': 'File permissions deleted successfully'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()

class ChangeLogDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.Lock()  # Create a lock for thread safety
        self.create_change_log_table()

    def create_change_log_table(self):
        with self.lock:  # Ensure that table creation is thread-safe
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create changeLog table with modification as TEXT
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS changeLog (
                    fileID INTEGER,
                    modification TEXT NOT NULL,
                    modBy INTEGER,
                    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ModID INTEGER PRIMARY KEY AUTOINCREMENT,
                    FOREIGN KEY (fileID) REFERENCES fileInfo(fileID),
                    FOREIGN KEY (modBy) REFERENCES users(userID)
                )
            ''')
            
            conn.commit()
            conn.close()

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_last_mod_id(self, fileID):
        with self.lock:  # Ensure that getting the last ModID is thread-safe
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT MAX(ModID) AS lastModID FROM changeLog 
                WHERE fileID = ?
            ''', (fileID,))
            
            last_mod_id = cursor.fetchone()
            if last_mod_id and last_mod_id['lastModID']:
                return last_mod_id['lastModID']
            else:
                return 0  # Return 0 if no modifications have been made

    def get_changes_for_user(self, fileID, lastModID, userID):
        with self.lock:  # Ensure that reading changes is thread-safe
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT modification, ModID FROM changeLog 
                WHERE fileID = ? AND ModID > ? AND modBy != ?
            ''', (fileID, lastModID,userID))
            
            changes = cursor.fetchall()
            return [{'modification': json.loads(change['modification']), 'ModID': change['ModID']} for change in changes]  # Deserialize JSON

    def get_changes_by_fileID(self, fileID):
        with self.lock:  # Ensure that reading changes is thread-safe
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM changeLog 
                WHERE fileID = ?
            ''', (fileID,))
            
            changes = cursor.fetchall()
            return [self._deserialize_change(change) for change in changes]  # Deserialize JSON

    def add_modification(self, fileID, modification, modBy):
        with self.lock:  # Ensure that adding a modification is thread-safe
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Ensure modification is a JSON-serializable object
            modification_json = json.dumps(modification)
            
            try:
                cursor.execute('''
                    INSERT INTO changeLog (fileID, modification, modBy) 
                    VALUES (?, ?, ?)
                ''', (fileID, modification_json, modBy))
                conn.commit()
                return {'status': 201, 'message': 'Modification added successfully.'}
            except Exception as e:
                return {'status': 500, 'message': str(e)}
            finally:
                conn.close()

    def _deserialize_change(self, change):
        """Convert the change dictionary to include deserialized JSON."""
        change_dict = dict(change)
        change_dict['modification'] = json.loads(change_dict['modification'])  # Deserialize JSON
        return change_dict
    
class VersionDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.Lock()

    def create_version_table(self):
        with self.lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS versionsLog (
                    version INTEGER,
                    fileID INTEGER,
                    timeStamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content TEXT,
                    PRIMARY KEY (version, fileID),
                    FOREIGN KEY (fileID) REFERENCES fileInfo (fileID)
                )
            ''')
            conn.commit()
            conn.close()

    def delete_version(self, version, fileID):
        with self.lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    DELETE FROM versionsLog 
                    WHERE version = ? AND fileID = ?
                ''', (version, fileID))
                conn.commit()
                if cursor.rowcount > 0:
                    return {'status': 200, 'message': f'Version {version} deleted successfully.'}
                else:
                    return {'status': 404, 'message': 'Version not found.'}
            except Exception as e:
                return {'status': 500, 'message': str(e)}
            finally:
                conn.close()

    def add_version(self, fileID, content):
        with self.lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            try:
                # Get latest version for this fileID
                cursor.execute('''
                    SELECT MAX(version) as max_version FROM versionsLog WHERE fileID = ?
                ''', (fileID,))
                row = cursor.fetchone()
                next_version = (row[0] or 0) + 1

                # Insert with manually incremented version
                cursor.execute('''
                    INSERT INTO versionsLog (version, fileID, content)
                    VALUES (?, ?, ?)
                ''', (next_version, fileID, content))

                conn.commit()
                return {'status': 201, 'message': f'Version {next_version} added successfully.'}
            except Exception as e:
                return {'status': 500, 'message': str(e)}
            finally:
                conn.close()

    def get_version(self, version, fileID):
        with self.lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM versionsLog 
                WHERE version = ? AND fileID = ?
            ''', (version, fileID))
            version = cursor.fetchone()
            return version

    def get_version_fullcontent(self, version, fileID):
        with self.lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content FROM versionsLog 
                WHERE version = ? AND fileID = ?
            ''', (version, fileID))
            content = cursor.fetchone()
            return content

    def get_versions_by_fileID(self, fileID):
        with self.lock:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT version,
                       date(timeStamp) as date,
                       time(timeStamp) as time
                FROM versionsLog 
                WHERE fileID = ?
                ORDER BY version ASC
            ''', (fileID,))
            versions = cursor.fetchall()
            return versions

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        return conn




    
def main():
    ChangeLogDatabase("/Users/hila/CEOs/users.db").create_change_log_table()
    FilePermissionsDatabase("/Users/hila/CEOs/users.db").create_file_permissions_table()
    FileInfoDatabase("/Users/hila/CEOs/users.db").create_file_info_table()
    UserDatabase("/Users/hila/CEOs/users.db").create_user_database()
    VersionDatabase("/Users/hila/CEOs/users.db").create_version_table()
    


    
    print("fin")

if __name__ == "__main__":
    main()