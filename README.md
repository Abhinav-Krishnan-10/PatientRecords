# Medical Records Management System - Python Backend

This is a Flask-based backend for the Medical Records Management System. It provides APIs for user authentication and patient management.

## Prerequisites

- Python 3.8 or higher
- MySQL Server
- pip (Python package installer)

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables by creating a `.env` file:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=medical_records
PORT=3000
```

4. Make sure your MySQL server is running and the database is created:
```sql
CREATE DATABASE medical_records;
```

5. Import the database schema from `database.sql`

## Running the Server

Start the server with:
```bash
python server.py
```

The server will run on http://localhost:3000 by default.

## API Endpoints

### Authentication
- POST `/api/login` - User login
- POST `/api/register` - User registration

### Patient Management
- GET `/api/patients` - List all patients (with optional search)
- GET `/api/patients/:id` - Get patient details
- POST `/api/patients` - Add new patient
- PUT `/api/patients/:id` - Update patient
- DELETE `/api/patients/:id` - Delete patient

### User Profile
- GET `/api/users/profile` - Get user profile

## Frontend

The frontend files should be placed in the `public` directory. The server will serve static files from this directory. 