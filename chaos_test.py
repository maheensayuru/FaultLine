import time
import mysql.connector
from mysql.connector import Error

# Configuration
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,          
    "user": "root",
    "password": "Mmsql@21",
    "database": "microlms_db",
    "ssl_disabled": True
}

def establish_connection():
    """Infinitely loops until a connection is secured."""
    while True:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            print("\n✅ [SYSTEM] Connection established! Commencing data stream...")
            return conn
        except Error as e:
            print(f"🔄 [SYSTEM] Database unreachable ({e.msg}). Retrying in 2 seconds...")
            time.sleep(2)

print("🛡️  RESILIENT CLIENT ONLINE")
print("-" * 50)

# Initial Connection
conn = establish_connection()

while True:
    try:
        # Pre-flight check to ensure the connection hasn't been quietly dropped
        conn.ping(reconnect=False)
        cursor = conn.cursor()
        
        start_time = time.time()
        cursor.execute("SELECT 1")
        cursor.fetchall()
        latency = time.time() - start_time
        
        if latency > 1.0:
            print(f"⚠️  [CRITICAL] Database locked! Latency: {latency:.2f}s")
        else:
            print(f"⚡ [OK] Query executed in {latency:.4f}s")
            
        cursor.close()
        time.sleep(1) 

    except Error as e:
        # The exact moment FaultLine attacks
        print(f"\n💥 [FATAL] CONNECTION LOST: {e.msg}")
        print("🛠️  [SYSTEM] Initiating auto-recovery sequence...")
        
        # Clean up the dead connection
        try:
            conn.close()
        except:
            pass
            
        # Trigger the self-healing loop
        conn = establish_connection()
        
    except KeyboardInterrupt:
        print("\nShutting down client.")
        break