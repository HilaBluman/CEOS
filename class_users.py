import json
import sqlite3
import random


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
                password TEXT NOT NULL
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
            return {'status': 201, 'message': 'User  created successfully with userID: {}'.format(userID)}
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
        
        if user:
            userID = user['userID']  # Get the userID from the fetched user
            return {'status': 200, 'message': 'Login successful.', 'userId': userID}  # Include userID in the response
        else:
            return {'status': 401, 'message': 'Invalid username or password.'}
        
        conn.close()

import sqlite3

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
                FOREIGN KEY (ownerID) REFERENCES users(userID)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_file(self, filename, ownerID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO fileInfo (name, ownerID) VALUES (?, ?)', (filename, ownerID))
            conn.commit()
            return {'status': 201, 'message': 'File created successfully.'}
        except sqlite3.IntegrityError:
            return {'status': 409, 'message': 'File name already exists.'}
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

    def grant_access(self, fileID, userID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO filePermissions (fileID, userID) VALUES (?, ?)', (fileID, userID))
            conn.commit()
            return {'status': 201, 'message': 'Access granted successfully.'}
        except sqlite3.IntegrityError:
            return {'status': 409, 'message': 'User  already has access to this file.'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
        finally:
            conn.close()

    def revoke_access(self, fileID, userID):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM filePermissions WHERE fileID = ? AND userID = ?', (fileID, userID))
        conn.commit()
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