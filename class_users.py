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
            userID = random.randint(10000, 999999)  # Generate a random userID
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