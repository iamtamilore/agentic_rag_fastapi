-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create a robust patients table
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(50),
    phone_number VARCHAR(50),
    address TEXT,
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(50),
    medical_plan VARCHAR(255),
    medical_plan_id VARCHAR(255),
    UNIQUE(first_name, last_name, date_of_birth)
);

-- Create a table for medical events, now with a structured SOAP note format
CREATE TABLE IF NOT EXISTS medical_events (
    id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    event_date DATE NOT NULL,
    attending_physician VARCHAR(255),
    subjective TEXT,
    objective TEXT,
    assessment TEXT,
    plan TEXT,
    content TEXT,
    embedding vector(768),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    UNIQUE(patient_id, event_date, content)
);

-- Create a table to log user queries for analysis
CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    patient_id INT,
    user_question TEXT NOT NULL,
    retrieved_context TEXT,
    llm_answer TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create a table for doctor accounts
CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'clinician'
);

-- Create a table for logging security-sensitive actions
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    doctor_id INT NOT NULL,
    patient_id INT,
    action TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- Grant all privileges to our application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rag_user;