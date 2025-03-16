from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='public')
CORS(app)

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'medical_records')
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

# Authentication Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        # For now, direct password comparison since admin password isn't hashed
        if password == user['password']:
            return jsonify({
                'user_id': user['id'],
                'username': user['username'],
                'full_name': user['fullname'],
                'email': user['email']
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    email = data.get('email')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = conn.cursor()
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            'INSERT INTO users (username, password, fullname, email) VALUES (%s, %s, %s, %s)',
            (username, hashed_password, full_name, email)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'})

    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry error
            return jsonify({'error': 'Username or email already exists'}), 400
        print(f"Database error: {err}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()

# Patient Routes
@app.route('/api/patients', methods=['GET'])
def get_patients():
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        query = '''
            SELECT 
                p.id as patient_id, 
                p.name, 
                p.age, 
                p.gender, 
                p.phone, 
                p.address,
                p.medicalHistory as medical_history,
                p.currentMedications as current_medications,
                p.allergies,
                p.lastUpdated as updated_at,
                p.updatedBy as updated_by,
                u.fullname as updated_by_name
            FROM patients p
            LEFT JOIN users u ON p.updatedBy = u.username
        '''
        
        if search:
            query += ' WHERE p.id LIKE %s OR p.name LIKE %s'
            search_pattern = f'%{search}%'
            cursor.execute(query, (search_pattern, search_pattern))
        else:
            cursor.execute(query)

        results = cursor.fetchall()
        return jsonify(results)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        query = '''
            SELECT 
                p.id as patient_id, 
                p.name, 
                p.age, 
                p.gender, 
                p.phone, 
                p.address,
                p.medicalHistory as medical_history,
                p.currentMedications as current_medications,
                p.allergies,
                p.lastUpdated as updated_at,
                p.updatedBy as updated_by,
                u.fullname as updated_by_name
            FROM patients p
            LEFT JOIN users u ON p.updatedBy = u.username
            WHERE p.id = %s
        '''
        cursor.execute(query, (patient_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Patient not found'}), 404
            
        return jsonify(result)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/patients', methods=['POST'])
def add_patient():
    data = request.json
    required_fields = ['patient_id', 'name', 'age', 'gender', 'phone', 'address']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = conn.cursor()
    try:
        query = '''
            INSERT INTO patients (
                id, name, age, gender, phone, address, 
                medicalHistory, currentMedications, allergies, 
                updatedBy
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        values = (
            data['patient_id'],
            data['name'],
            int(data['age']),
            data['gender'],
            data['phone'],
            data['address'],
            data.get('medical_history'),
            data.get('current_medications'),
            data.get('allergies'),
            data.get('updated_by')
        )
        
        cursor.execute(query, values)
        conn.commit()
        return jsonify({'message': 'Patient added successfully'})

    except mysql.connector.Error as err:
        if err.errno == 1062:  # Duplicate entry error
            return jsonify({'error': 'Patient ID already exists'}), 400
        print(f"Database error: {err}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/patients/<patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.json
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = conn.cursor()
    try:
        query = '''
            UPDATE patients 
            SET name = %s, age = %s, gender = %s, phone = %s, 
                address = %s, medicalHistory = %s, currentMedications = %s, 
                allergies = %s, updatedBy = %s
            WHERE id = %s
        '''
        values = (
            data['name'],
            data['age'],
            data['gender'],
            data['phone'],
            data['address'],
            data.get('medical_history'),
            data.get('current_medications'),
            data.get('allergies'),
            data.get('updated_by'),
            patient_id
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Patient not found'}), 404
            
        return jsonify({'message': 'Patient updated successfully'})

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/patients/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM patients WHERE id = %s', (patient_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Patient not found'}), 404
            
        return jsonify({'message': 'Patient deleted successfully'})

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/users/profile', methods=['GET'])
def get_user_profile():
    username = request.headers.get('x-user', 'admin')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            'SELECT id, username, fullname as full_name, email FROM users WHERE username = %s',
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify(user)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()

# Catch-all route to serve index.html for client-side routing
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory('public', 'index.html')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    app.run(host='0.0.0.0', port=port) 