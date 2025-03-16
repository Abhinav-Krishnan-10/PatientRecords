-- Drop existing database and recreate
DROP DATABASE IF EXISTS medical_records;
CREATE DATABASE medical_records;
USE medical_records;

-- Create users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    fullname VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create patients table
CREATE TABLE patients (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    medicalHistory TEXT,
    currentMedications TEXT,
    allergies TEXT,
    lastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updatedBy VARCHAR(255),
    FOREIGN KEY (updatedBy) REFERENCES users(username)
);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password, fullname, email) 
VALUES ('admin', 'admin123', 'Administrator', 'admin@hospital.com');