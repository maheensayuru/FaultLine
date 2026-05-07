import time
import mysql.connector

print("🔌 Connecting to database via FaultLine (Port 3307)...")
try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3307,          
        user="root",
        password="Mmsql@21",
        database="microlms_db"
    )
    cursor = conn.cursor()
    print("✅ Connection successful!")

    print("\n🚀 Commencing live query stream. Watch the latency...")
    print("-" * 50)
    
    # Infinite loop to keep pinging the database
    while True:
        start_time = time.time()
        
        # We will just run a simple query that works on any database
        cursor.execute("SELECT 1")
        rows = cursor.fetchall()
        
        end_time = time.time()
        latency = end_time - start_time
        
        if latency > 1.0:
            print(f"⚠️  [CRITICAL] Database locked! Query took {latency:.2f} seconds!")
        else:
            print(f"⚡ [OK] Query executed in {latency:.4f} seconds.")
            
        time.sleep(1) 

except Exception as e:
    print(f"❌ Connection Failed: {e}")