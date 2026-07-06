-- MediGuide Medical Database Schema
-- SQLite Database Structure

PRAGMA foreign_keys = ON;

-- ============================================
-- DISEASES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS diseases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    icd11_code TEXT UNIQUE NOT NULL,
    disease_name TEXT NOT NULL,
    common_name TEXT,
    description TEXT,
    severity_level TEXT CHECK (severity_level IN ('mild', 'moderate', 'severe', 'critical')),
    typical_duration TEXT,
    complications TEXT,
    treatment_class TEXT,
    is_emergency INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SYMPTOMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symptom_name TEXT UNIQUE NOT NULL,
    medical_term TEXT,
    category TEXT,
    severity_indicators TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DISEASE-SYMPTOM ASSOCIATIONS
-- ============================================
CREATE TABLE IF NOT EXISTS disease_symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_id INTEGER NOT NULL,
    symptom_id INTEGER NOT NULL,
    association_strength REAL CHECK (association_strength >= 0 AND association_strength <= 1),
    is_primary_symptom INTEGER DEFAULT 0,
    typical_onset_days INTEGER,
    prevalence_percentage REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (disease_id) REFERENCES diseases (id) ON DELETE CASCADE,
    FOREIGN KEY (symptom_id) REFERENCES symptoms (id) ON DELETE CASCADE,
    UNIQUE (disease_id, symptom_id)
);

-- ============================================
-- HOSPITALS TABLE (Bangladesh)
-- ============================================
CREATE TABLE IF NOT EXISTS hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    district TEXT,
    phone TEXT,
    latitude REAL,
    longitude REAL,
    specialties TEXT,
    available_beds INTEGER DEFAULT 5,
    rating REAL DEFAULT 4.0,
    status TEXT CHECK (status IN ('active', 'inactive')),
    is_emergency_facility INTEGER DEFAULT 0,
    average_wait_time INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- MEDICATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_name TEXT UNIQUE NOT NULL,
    generic_name TEXT,
    drug_class TEXT,
    typical_dosage TEXT,
    contraindications TEXT,
    side_effects TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DRUG INTERACTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS drug_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_1_id INTEGER NOT NULL,
    medication_2_id INTEGER NOT NULL,
    severity TEXT CHECK (severity IN ('mild', 'moderate', 'severe')),
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medication_1_id) REFERENCES medications (id) ON DELETE CASCADE,
    FOREIGN KEY (medication_2_id) REFERENCES medications (id) ON DELETE CASCADE,
    UNIQUE (medication_1_id, medication_2_id)
);

-- ============================================
-- AUDIT LOGS TABLE (For Compliance)
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    action TEXT,
    table_name TEXT,
    record_id INTEGER,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CREATE INDEXES (For Fast Queries)
-- ============================================
CREATE INDEX IF NOT EXISTS idx_disease_name ON diseases (disease_name);
CREATE INDEX IF NOT EXISTS idx_disease_emergency ON diseases (is_emergency);
CREATE INDEX IF NOT EXISTS idx_symptom_name ON symptoms (symptom_name);
CREATE INDEX IF NOT EXISTS idx_disease_symptoms ON disease_symptoms (disease_id, symptom_id);
CREATE INDEX IF NOT EXISTS idx_hospital_district ON hospitals (district);
CREATE INDEX IF NOT EXISTS idx_hospital_specialty ON hospitals (specialties);
CREATE INDEX IF NOT EXISTS idx_medication_name ON medications (medication_name);