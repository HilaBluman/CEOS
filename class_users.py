import sqlite3
import random
import threading
import argon2
import base64
import json
import os
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.Util.Padding import pad, unpad
from typing import Optional, Union, Any, cast, Dict

class RSAManager:
    
    def __init__(self) -> None:
        try:
            key = RSA.generate(1024)
            self.private_key: Optional[RSA.RsaKey] = key
            self.public_key: Optional[RSA.RsaKey] = key.publickey()
        except Exception as e:
            print(f"Error generating RSA keys: {str(e)}")
            self.private_key = None
            self.public_key = None

    def get_public_key(self) -> Optional[str]:
        """Get public key in PEM format"""
        try:
            if not self.public_key:
                raise ValueError("Public key not initialized")
            return self.public_key.export_key().decode('utf-8')
        except Exception as e:
            print(f"Error getting public key: {str(e)}")
            return None

    def encryptRSA(self, message: Union[str, bytes]) -> Optional[str]:
        """Encrypt message using RSA"""
        try:
            if not self.public_key:
                raise ValueError("Public key not initialized")
            if isinstance(message, str):
                message = message.encode('utf-8')
            cipher = PKCS1_v1_5.new(self.public_key)
            encrypted = cipher.encrypt(message)
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"Error encrypting with RSA: {str(e)}")
            return None

    def decryptRSA(self, encrypted: str) -> Optional[str]:
        """Decrypt message using RSA"""
        try:
            if not self.private_key:
                raise ValueError("Private key not initialized")
            encrypted_bytes = base64.b64decode(encrypted)
            cipher = PKCS1_v1_5.new(self.private_key)
            decrypted = cipher.decrypt(encrypted_bytes, sentinel=None)
            if not decrypted:
                return None
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Error decrypting with RSA: {str(e)}")
            return None

    def generateAESKey(self) -> Optional[str]:
        """Generate a new AES key"""
        try:
            key = os.urandom(32)  # 256 bits
            return base64.b64encode(key).decode('utf-8')
        except Exception as e:
            print(f"Error generating AES key: {str(e)}")
            return None

    def encryptAES(self, message: Union[str, bytes], aes_key: str) -> Optional[str]:
        """Encrypt message using AES"""
        try:
            if isinstance(message, str):
                message = message.encode('utf-8')
            key_bytes = base64.b64decode(aes_key)
            # Generate a random IV
            iv = os.urandom(AES.block_size)
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            # Pad the message
            padded_data = pad(message, AES.block_size)
            # Encrypt the padded data
            encrypted = cipher.encrypt(padded_data)
            # Combine IV and encrypted data
            combined = iv + encrypted
            # Return base64 encoded result
            return base64.b64encode(combined).decode('utf-8')
        except Exception as e:
            print(f"Error encrypting with AES: {str(e)}")
            return None

    def decryptAES(self, encrypted: str, aes_key: str) -> Optional[str]:
        """Decrypt message using AES"""
        try:
            print(f"🔓 Server AES Decryption Debug:")
            print(f"- Encrypted data length: {len(encrypted)}")
            print(f"- Encrypted data (first 50 chars): {encrypted[:50]}...")
            print(f"- AES key length: {len(aes_key)}")
            
            if not aes_key:
                raise ValueError("AES key not provided")
                
            # Decode the base64 input
            encrypted_bytes = base64.b64decode(encrypted)
            print(f"- Decoded bytes length: {len(encrypted_bytes)}")
            
            key_bytes = base64.b64decode(aes_key)
            print(f"- Key bytes length: {len(key_bytes)}")
            
            # Extract IV and ciphertext
            iv = encrypted_bytes[:AES.block_size]
            ciphertext = encrypted_bytes[AES.block_size:]
            
            print(f"- IV length: {len(iv)} bytes")
            print(f"- Ciphertext length: {len(ciphertext)} bytes")
            print(f"- Expected IV length: {AES.block_size} bytes")
            
            # Create cipher and decrypt
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(ciphertext)
            
            print(f"- Decrypted bytes length: {len(decrypted)}")
            
            # Unpad the decrypted data
            try:
                unpadded_data = unpad(decrypted, AES.block_size)
                result = unpadded_data.decode('utf-8')
                print(f"- Final decrypted result: {result}")
                return result
            except ValueError as e:
                print(f"❌ Padding error: {str(e)}")
                print(f"- Decrypted bytes (hex): {decrypted.hex()}")
                return None
                
        except Exception as e:
            print(f"❌ Error decrypting with AES: {str(e)}")
            return None

    def get_public_key_string(self):
        if not self.public_key:
            raise ValueError("Public key not initialized")
        public_pem = self.public_key.export_key().decode('utf-8')
        return public_pem
    
    def encryptWithClientKey(self, message, client_public_key):
        """Encrypt data using a client's public RSA key"""
        try:
            # Import the client's public key
            public_key = RSA.import_key(client_public_key.encode('utf-8'))
            cipher_rsa = PKCS1_v1_5.new(public_key)
            
            # Prepare the message
            if isinstance(message, str):
                message_bytes = message.encode('utf-8')
            else:
                message_bytes = message
                
            # Encrypt the message
            encrypted = cipher_rsa.encrypt(message_bytes)
            
            # Return base64 encoded encrypted data
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            print(f"Client RSA encryption error: {e}")
            return None
    
    def decrypt_json_data(self, encrypted_data):
        decrypted_text = self.decryptRSA(encrypted_data)
        if decrypted_text:
            try:
                return json.loads(decrypted_text)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return None
        return None

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
        
        max_attempts = 100  # Prevent infinite loop
        attempts = 0
        
        try:
            while attempts < max_attempts:
                userID = random.randint(1000, 9999) 
                cursor.execute('SELECT COUNT(*) FROM users WHERE userID = ?', (userID,))
                count = cursor.fetchone()[0]
                if count == 0:  
                    return userID  
                attempts += 1
            
            
            raise Exception("Unable to generate unique userID after maximum attempts")
        finally:
            conn.close() 

    def signup(self, username, password,clientPublicRSA):
        if len(password) < 4:
            return {'status': 400, 'message': 'Password must be at least 4 characters long.'}

        try:
            userID = self.generate_unique_userID() 
        except Exception as e:
            return {'status': 500, 'message': 'Failed to generate unique user ID'}

        conn = self.get_db_connection()
        cursor = conn.cursor()

        public_key = RSA.import_key(clientPublicRSA.encode('utf-8'))
        cipher_rsa = PKCS1_v1_5.new(public_key)
        user_id_encrypted = base64.b64encode(cipher_rsa.encrypt(str(userID).encode('utf-8'))).decode('utf-8')

        
        password_hash = self.hash_password(password)
        try:
            cursor.execute('INSERT INTO users (userID, username, password) VALUES (?, ?, ?)', (userID, username, password_hash))
            conn.commit()
            return {'status': 201, 'message': 'User created successfully',userID :user_id_encrypted }
        except sqlite3.IntegrityError:
            return {'status': 409, 'message': 'Username already exists.'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()
            
    def login(self, username, password, clientPublicRSA):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        user_id = self.get_user_id(username)
        public_key = RSA.import_key(clientPublicRSA.encode('utf-8'))
        cipher_rsa = PKCS1_v1_5.new(public_key)
        user_id_encrypted = base64.b64encode(cipher_rsa.encrypt(str(user_id).encode('utf-8'))).decode('utf-8')

        
        if result and self.verify_password(result['password'], password):
            return {'status': 200, 'message': 'Login successful.', 'userId': user_id_encrypted}
        else:
            return {'status': 401, 'message': 'Invalid username or password.'}

    
        
    def get_user_id(self, username):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT userID FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        return int(result[0]) if result else None
    
    def hash_password(self,password):
        ph = argon2.PasswordHasher()
        hashed = ph.hash(password)
        return hashed

    def verify_password(self,hashed_password, input_password):
        ph = argon2.PasswordHasher()
        try:
            return ph.verify(hashed_password, input_password)
        except argon2.exceptions.VerifyMismatchError:
            return False

class FileInfoDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_file_info_table()

    def create_file_info_table(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Create fileInfo table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fileInfo (
                fileID INTEGER UNIQUE PRIMARY KEY,
                filename TEXT NOT NULL,
                ownerID INTEGER,
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

    def add_file(self, filename, ownerID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO fileInfo (filename, ownerID) VALUES (?, ?)', (filename, ownerID))
            conn.commit()
            return {'status': 201, 'message': 'File created successfully.'}
        except sqlite3.IntegrityError:
            return {'status': 409, 'message': 'File name already exists.'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()

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

    def is_viewer(self, file_id, user_id):
        """Check if a user has viewer role for a file"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role
            FROM filePermissions
            WHERE fileID = ? AND userID = ?
        ''', (file_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result and result['role'] == 'viewer'

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