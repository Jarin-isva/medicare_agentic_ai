# Test Database Connectivity
# tests/test_database.py

import sqlite3
import json

def test_database_connection():
    """Test that database exists and is readable"""
    
    try:
        conn = sqlite3.connect("data/mediguide.db")
        cursor = conn.cursor()
        
        # Test: Count records
        disease_count = cursor.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
        
        if disease_count > 0:
            print("✅ Database connection successful")
            print(f"✅ Database has {disease_count} diseases")
            return True
        else:
            print("❌ Database is empty")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_disease_lookup():
    """Test disease lookup by name"""
    
    try:
        conn = sqlite3.connect("data/mediguide.db")
        cursor = conn.cursor()
        
        # Test: Look up dengue
        result = cursor.execute(
            "SELECT disease_name, severity_level, is_emergency FROM diseases WHERE disease_name = ?",
            ("Dengue Fever",)
        ).fetchone()
        
        if result:
            disease_name, severity, is_emergency = result
            print(f"\n✅ Disease lookup works")
            print(f"   Disease: {disease_name}")
            print(f"   Severity: {severity}")
            print(f"   Emergency: {'Yes' if is_emergency else 'No'}")
            return True
        else:
            print("❌ Disease not found")
            return False
            
    except Exception as e:
        print(f"❌ Disease lookup error: {e}")
        return False

def test_symptom_disease_association():
    """Test finding diseases by symptom"""
    
    try:
        conn = sqlite3.connect("data/mediguide.db")
        cursor = conn.cursor()
        
        # Test: Find diseases associated with fever
        results = cursor.execute("""
            SELECT d.disease_name, ds.association_strength 
            FROM disease_symptoms ds
            JOIN diseases d ON ds.disease_id = d.id
            JOIN symptoms s ON ds.symptom_id = s.id
            WHERE s.symptom_name = ?
            ORDER BY ds.association_strength DESC
            LIMIT 5
        """, ("fever",)).fetchall()
        
        if results:
            print(f"\n✅ Symptom-Disease lookup works")
            print(f"   Diseases with 'fever' (top 5):")
            for disease, strength in results:
                print(f"   - {disease}: {strength:.0%} confidence")
            return True
        else:
            print("❌ No associations found")
            return False
            
    except Exception as e:
        print(f"❌ Association lookup error: {e}")
        return False

def test_hospital_lookup():
    """Test hospital lookup by district"""
    
    try:
        conn = sqlite3.connect("data/mediguide.db")
        cursor = conn.cursor()
        
        # Test: Find hospitals in Chittagong
        results = cursor.execute("""
            SELECT hospital_name, specialties, rating 
            FROM hospitals 
            WHERE district = ?
            ORDER BY rating DESC
            LIMIT 3
        """, ("Chittagong",)).fetchall()
        
        if results:
            print(f"\n✅ Hospital lookup works")
            print(f"   Top hospitals in Chittagong:")
            for hospital, specialties, rating in results:
                print(f"   - {hospital} ({rating}/5) - {specialties}")
            return True
        else:
            print("❌ No hospitals found")
            return False
            
    except Exception as e:
        print(f"❌ Hospital lookup error: {e}")
        return False

def main():
    """Run all database tests"""
    
    print("=" * 60)
    print("🔍 MediGuide Database Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1
    all_passed &= test_database_connection()
    
    # Test 2
    all_passed &= test_disease_lookup()
    
    # Test 3
    all_passed &= test_symptom_disease_association()
    
    # Test 4
    all_passed &= test_hospital_lookup()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL DATABASE TESTS PASSED")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    main()