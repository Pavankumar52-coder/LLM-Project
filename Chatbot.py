from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
from mysql.connector import Error
import bcrypt
from flask_cors import CORS
import cohere

# Initialize the Cohere client with your API key
cohere_client = cohere.Client('GxLm55qUaAMAKSGzOPpzjlgj0Iaa5yOGDrMAGZvJ')


app = Flask(__name__)
CORS(app) 

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'PrAs@Son*00',
    'database': 'mentalhealthdb'
}

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
    except Error as e:
        print('Error:{e}')
    return connection

def get_db_connection():
    return mysql.connector.connect(**db_config)
def get_conversation_history(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT prompt, response FROM conversation WHERE session_id = %s"
    cursor.execute(query, (session_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    history = '\n'.join([f"User: {row['prompt']}\nBot: {row['response']}" for row in rows])
    return history

def update_conversation_history(session_id, user_message, bot_response):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO conversation (session_id, prompt, response) VALUES (%s, %s, %s)"
    cursor.execute(query, (session_id, user_message, bot_response))
    conn.commit()
    cursor.close()
    conn.close()


@app.route('/register', methods = ['POST'])
def register():
    data = request.json
    username = data['username']
    password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    email = data['email']
    
    connection = create_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute('INSERT INTO users (username, password, email) values (%s, %s, %s)', (username, password, email))
        connection.commit()
        return jsonify({'messages': 'User has been registered successfully'}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        connection.close()
        
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    
    connection = create_connection()
    cursor = connection.cursor()
    
    cursor.execute('SELECT id, password from users where username = %s', (username,))
    user = cursor.fetchone()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        return jsonify({'message': 'User has logged in successfully', 'user_id': user[0]}), 200
    else:
        return jsonify({'error': 'Invalid Credentials'}), 401
    
@app.route('/message', methods = ['POST', 'GET'])
def message():
    data = request.get_json()

    # Log incoming request data
    print("Received data:", data)

    if 'message' not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message = data['message']

    try:
        # Generate a response using Cohere
        response = cohere_client.generate(
            model='command-xlarge',  # Ensure this model exists
            prompt=user_message,
            max_tokens=50
        )

        # Access the generated text
        bot_response = response.generations[0].text.strip()

        return jsonify({"response": bot_response}), 200
    except Exception as e:
        # Log the exception
        print("Error generating response:", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/history/<int:user_id>', methods=['GET'])
def history(user_id):
    connection = create_connection()
    cursor = connection.cursor()
    
    cursor.execute('SELECT message, response, timestamp FROM conversations WHERE user_id = %s', (user_id,))
    conversations = cursor.fetchall()
    
    history = [{'message': convo[0], 'response':convo[1], 'timestamp':convo[2]} for convo in conversations]
    
    cursor.close()
    connection.close()
    
    return jsonify(history), 200

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)