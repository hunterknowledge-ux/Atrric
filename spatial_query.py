import sqlite3


def query_db(db_file, sql_query):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        print(" | ".join(columns))
        print("-" * 80)
        
        for row in results:
            print(" | ".join(str(item) for item in row))
            
    except Exception as e:
        print(f"SQL Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    db = "raw_data/spatial/atrric_macro.db"
    
    print("--- SCHEMA & SAMPLE DATA (3 BARIS) ---")
    # Ambil 3 baris pertama untuk tengok nama column sebenar
    query_db(db, "SELECT * FROM population_data LIMIT 3;")
    
    print("\n--- CARI GEN Z DI SELANGOR (UMUR 15-24) ---")
    # Query ini andaikan column nama 'state', 'district', 'age', 'population', 'sex', 'ethnicity'
    sql = """
    SELECT state, district, age, SUM(CAST(population AS REAL)) as total_population
    FROM population_data
    WHERE 
        state = 'Selangor' 
        AND (age = '15-19' OR age = '20-24')
        AND sex = 'both'
        AND ethnicity = 'overall'
    GROUP BY state, district, age
    ORDER BY total_population DESC
    LIMIT 5;
    """
    query_db(db, sql)
