# Importing Flask backend libraries
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import bcrypt
from datetime import datetime

# Flask app
app = Flask(__name__)
CORS(app)

# Database configuaration using user credentials
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your sql account password',
    'database': 'database name'
}

# Creating database connection
def create_connection():
    return mysql.connector.connect(**db_config)

# Register api endpoit for user registration
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data['username']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        email = data['email']

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                       (username, password, email))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'User registered successfully'}), 201

    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Login api endpoint for user login through credentials
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            return jsonify({'message': 'Login successful', 'user_id': user[0]}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Save chat api endpoint for saving the user chat
@app.route('/save_chat', methods=['POST'])
def save_chat():
    try:
        data = request.get_json()
        user_id = data['user_id']
        user_message = data['message']
        bot_response = data['response']
        timestamp = datetime.now()

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_id, message, response, timestamp) VALUES (%s, %s, %s, %s)",
                       (user_id, user_message, bot_response, timestamp))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Chat saved'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Chat history api endpoint for viewing user's chat history
@app.route('/history/<int:user_id>', methods=['GET'])
def chat_history(user_id):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT message, response, timestamp FROM conversations WHERE user_id = %s", (user_id,))
        conversations = cursor.fetchall()
        cursor.close()
        conn.close()

        history = [{'message': m, 'response': r, 'timestamp': str(t)} for m, r, t in conversations]
        return jsonify(history), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)