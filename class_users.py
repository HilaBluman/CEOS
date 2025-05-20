import json
import sqlite3
import random
import threading


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
        return result[0] if result else None

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
    
def main():
    ChangeLogDatabase("/Users/hila/CEOs/users.db").create_change_log_table()
    FilePermissionsDatabase("/Users/hila/CEOs/users.db").create_file_permissions_table()
    FileInfoDatabase("/Users/hila/CEOs/users.db").create_file_info_table()
    UserDatabase("/Users/hila/CEOs/users.db").create_user_database()
    print("fin")

if __name__ == "__main__":
    main()