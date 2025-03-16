const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const path = require('path');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Database connection
const db = mysql.createConnection({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'medical_records'
});

db.connect((err) => {
    if (err) {
        console.error('Error connecting to the database:', err);
        return;
    }
    console.log('Connected to MySQL database');
});

// Serve index.html for the root route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Authentication Routes
app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;
    
    const query = 'SELECT * FROM users WHERE username = ?';
    db.query(query, [username], (err, results) => {
        if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Internal server error' });
        }
        
        if (results.length === 0) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        const user = results[0];
        // For now, we're doing direct password comparison since we haven't hashed the admin password
        if (password === user.password) {
            res.json({
                user_id: user.id,
                username: user.username,
                full_name: user.fullname,
                email: user.email
            });
        } else {
            res.status(401).json({ error: 'Invalid credentials' });
        }
    });
});

app.post('/api/register', async (req, res) => {
    const { username, password, full_name, email } = req.body;
    
    try {
        const hashedPassword = await bcrypt.hash(password, 10);
        const query = 'INSERT INTO users (username, password, fullname, email) VALUES (?, ?, ?, ?)';
        
        db.query(query, [username, hashedPassword, full_name, email], (err, result) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') {
                    return res.status(400).json({ error: 'Username or email already exists' });
                }
                console.error('Database error:', err);
                return res.status(500).json({ error: 'Internal server error' });
            }
            res.json({ message: 'User registered successfully' });
        });
    } catch (error) {
        console.error('Error hashing password:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Patient Routes
app.get('/api/patients', (req, res) => {
    const { search } = req.query;
    let query = `
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
    `;
    
    if (search) {
        query += ' WHERE p.id LIKE ? OR p.name LIKE ?';
        const searchPattern = `%${search}%`;
        db.query(query, [searchPattern, searchPattern], (err, results) => {
            if (err) {
                console.error('Database error:', err);
                return res.status(500).json({ error: 'Internal server error' });
            }
            res.json(results);
        });
    } else {
        db.query(query, (err, results) => {
            if (err) {
                console.error('Database error:', err);
                return res.status(500).json({ error: 'Internal server error' });
            }
            res.json(results);
        });
    }
});

app.get('/api/patients/:id', (req, res) => {
    const query = `
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
        WHERE p.id = ?
    `;

    db.query(query, [req.params.id], (err, results) => {
        if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Internal server error' });
        }
        if (results.length === 0) {
            return res.status(404).json({ error: 'Patient not found' });
        }
        res.json(results[0]);
    });
});

app.post('/api/patients', (req, res) => {
    const { 
        patient_id, 
        name, 
        age, 
        gender, 
        phone, 
        address, 
        medical_history, 
        current_medications, 
        allergies, 
        updated_by 
    } = req.body;

    if (!patient_id || !name || !age || !gender || !phone || !address) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    const query = `
        INSERT INTO patients (
            id, name, age, gender, phone, address, 
            medicalHistory, currentMedications, allergies, 
            updatedBy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

    const values = [
        patient_id, 
        name, 
        parseInt(age), 
        gender, 
        phone, 
        address,
        medical_history || null, 
        current_medications || null, 
        allergies || null,
        updated_by || null
    ];

    db.query(query, values, (err, result) => {
        if (err) {
            console.error('Database error:', err);
            if (err.code === 'ER_DUP_ENTRY') {
                return res.status(400).json({ error: 'Patient ID already exists' });
            }
            return res.status(500).json({ error: 'Internal server error' });
        }
        res.json({ message: 'Patient added successfully' });
    });
});

app.put('/api/patients/:id', (req, res) => {
    const { name, age, gender, phone, address, medical_history, current_medications, allergies, updated_by } = req.body;
    
    const query = `
        UPDATE patients 
        SET name = ?, age = ?, gender = ?, phone = ?, 
            address = ?, medicalHistory = ?, currentMedications = ?, 
            allergies = ?, updatedBy = ?
        WHERE id = ?
    `;

    db.query(query, [
        name, age, gender, phone, address,
        medical_history, current_medications, allergies,
        updated_by, req.params.id
    ], (err, result) => {
        if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Internal server error' });
        }
        if (result.affectedRows === 0) {
            return res.status(404).json({ error: 'Patient not found' });
        }
        res.json({ message: 'Patient updated successfully' });
    });
});

app.delete('/api/patients/:id', (req, res) => {
    const query = 'DELETE FROM patients WHERE id = ?';
    db.query(query, [req.params.id], (err, result) => {
        if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Internal server error' });
        }
        if (result.affectedRows === 0) {
            return res.status(404).json({ error: 'Patient not found' });
        }
        res.json({ message: 'Patient deleted successfully' });
    });
});

// Get user profile
app.get('/api/users/profile', (req, res) => {
    const username = req.headers['x-user'] || 'admin';
    
    const query = 'SELECT id, username, fullname as full_name, email FROM users WHERE username = ?';
    db.query(query, [username], (err, results) => {
        if (err) {
            console.error('Database error:', err);
            return res.status(500).json({ error: 'Internal server error' });
        }
        if (results.length === 0) {
            return res.status(404).json({ error: 'User not found' });
        }
        res.json(results[0]);
    });
});

// Catch-all route to serve index.html for client-side routing
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
}); 