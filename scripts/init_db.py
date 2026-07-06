# Database Initialization Script
# scripts/init_db.py

import sqlite3
import csv
import os
from pathlib import Path

def get_database_path():
    """Get database path from environment or use default"""
    db_path = "data/mediguide.db"
    return db_path

def create_database():
    """Create SQLite database with schema"""
    
    db_path = get_database_path()
    
    # Create data directory if it doesn't exist
    Path("data").mkdir(exist_ok=True)
    
    print(f"📦 Creating database at: {db_path}")
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read and execute schema statement by statement
    with open("config/database_schema.sql", "r", encoding="utf-8") as schema_file:
        schema = schema_file.read()

    statements = []
    current = []
    for line in schema.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if line.strip().endswith(";"):
            statement = "\n".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

    create_statements = []
    index_statements = []
    for statement in statements:
        if statement.upper().startswith("CREATE INDEX"):
            index_statements.append(statement)
        else:
            create_statements.append(statement)

    for statement in create_statements:
        cursor.execute(statement)

    conn.commit()

    for statement in index_statements:
        cursor.execute(statement)
    
    print("✅ Database schema created successfully")
    
    conn.commit()
    conn.close()
    
    return db_path

def load_diseases_data(db_path):
    """Load diseases from CSV"""
    
    print("\n📄 Loading diseases data...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open("data/diseases.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        
        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO diseases 
                    (icd11_code, disease_name, common_name, description, severity_level, 
                     typical_duration, treatment_class, is_emergency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['icd11_code'],
                    row['disease_name'],
                    row['common_name'],
                    row['description'],
                    row['severity_level'],
                    row['typical_duration'],
                    row['treatment_class'],
                    int(row['is_emergency'])
                ))
                count += 1
            except sqlite3.IntegrityError:
                pass  # Skip duplicates
        
        conn.commit()
        print(f"✅ Loaded {count} diseases")
    
    conn.close()

def load_symptoms_data(db_path):
    """Load symptoms from CSV"""
    
    print("\n📄 Loading symptoms data...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open("data/symptoms.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        
        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO symptoms 
                    (symptom_name, medical_term, category, severity_indicators)
                    VALUES (?, ?, ?, ?)
                """, (
                    row['symptom_name'],
                    row['medical_term'],
                    row['category'],
                    row['severity_indicators']
                ))
                count += 1
            except sqlite3.IntegrityError:
                pass  # Skip duplicates
        
        conn.commit()
        print(f"✅ Loaded {count} symptoms")
    
    conn.close()

def load_disease_symptoms_associations(db_path):
    """Load disease-symptom associations from CSV"""
    
    print("\n📄 Loading disease-symptom associations...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open("data/disease_symptoms.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        
        for row in reader:
            try:
                # Get disease ID
                disease = cursor.execute(
                    "SELECT id FROM diseases WHERE disease_name = ?",
                    (row['disease_name'],)
                ).fetchone()
                
                # Get symptom ID
                symptom = cursor.execute(
                    "SELECT id FROM symptoms WHERE symptom_name = ?",
                    (row['symptom_name'],)
                ).fetchone()
                
                if disease and symptom:
                    cursor.execute("""
                        INSERT INTO disease_symptoms 
                        (disease_id, symptom_id, association_strength, is_primary_symptom, 
                         typical_onset_days, prevalence_percentage)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        disease[0],
                        symptom[0],
                        float(row['association_strength']),
                        int(row['is_primary_symptom']),
                        int(row['typical_onset_days']),
                        float(row['prevalence_percentage'])
                    ))
                    count += 1
            except (sqlite3.IntegrityError, ValueError) as e:
                pass  # Skip errors
        
        conn.commit()
        print(f"✅ Loaded {count} disease-symptom associations")
    
    conn.close()

def load_hospitals_data(db_path):
    """Load hospital registry from CSV"""
    
    print("\n📄 Loading hospital registry...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open("data/hospitals_bangladesh.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        
        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO hospitals 
                    (hospital_name, address, city, district, phone, latitude, longitude, 
                     specialties, available_beds, rating, is_emergency_facility, average_wait_time, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                """, (
                    row['hospital_name'],
                    row['address'],
                    row['city'],
                    row['district'],
                    row['phone'],
                    float(row['latitude']),
                    float(row['longitude']),
                    row['specialties'],
                    int(row['available_beds']),
                    float(row['rating']),
                    int(row['is_emergency_facility']),
                    int(row['average_wait_time'])
                ))
                count += 1
            except sqlite3.IntegrityError:
                pass  # Skip duplicates
        
        conn.commit()
        print(f"✅ Loaded {count} hospitals")
    
    conn.close()

def verify_database(db_path):
    """Verify database has data"""
    
    print("\n🔍 Verifying database...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count records
    disease_count = cursor.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
    symptom_count = cursor.execute("SELECT COUNT(*) FROM symptoms").fetchone()[0]
    association_count = cursor.execute("SELECT COUNT(*) FROM disease_symptoms").fetchone()[0]
    hospital_count = cursor.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0]
    
    conn.close()
    
    print(f"   Diseases: {disease_count}")
    print(f"   Symptoms: {symptom_count}")
    print(f"   Disease-Symptom Associations: {association_count}")
    print(f"   Hospitals: {hospital_count}")
    
    if all([disease_count > 0, symptom_count > 0, association_count > 0, hospital_count > 0]):
        print("\n✅ DATABASE VERIFICATION PASSED")
        return True
    else:
        print("\n❌ DATABASE VERIFICATION FAILED - Some tables are empty")
        return False

def main():
    """Main initialization routine"""
    
    print("=" * 60)
    print("🏥 MediGuide Database Initialization")
    print("=" * 60)
    
    try:
        # Step 1: Create database
        db_path = create_database()
        
        # Step 2: Load data
        load_diseases_data(db_path)
        load_symptoms_data(db_path)
        load_disease_symptoms_associations(db_path)
        load_hospitals_data(db_path)
        
        # Step 3: Verify
        success = verify_database(db_path)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ DATABASE INITIALIZATION COMPLETE")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("⚠️  DATABASE INITIALIZATION PARTIALLY COMPLETE")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()