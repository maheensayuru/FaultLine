import asyncio
import logging
import random
import sys

# Brutalist terminal logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [FAULTLINE] - %(message)s', datefmt='%H:%M:%S')

# Configuration
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 3307       
REMOTE_HOST = '127.0.0.1'
REMOTE_PORT = 3306      

# --- LIVE CHAOS STATE ---
INJECT_LATENCY = 0.0    # Seconds to delay
DROP_RATE = 0.0         # Percentage of requests to drop (0.0 to 1.0)

async def pipe(reader, writer, direction):
    """Shuttles raw bytes between the client and the database."""
    global INJECT_LATENCY, DROP_RATE
    try:
        while not reader.at_eof():
            data = await reader.read(4096)
            if not data:
                break

            # 🛑 THE CHAOS INJECTION ZONE 🛑
            if direction == "DB -> Client":
                # 1. Connection Drop Assassin
                if DROP_RATE > 0 and random.random() < DROP_RATE:
                    logging.error("💥 CHAOS TRIGGERED: Simulating random connection drop!")
                    writer.close()
                    return # Instantly sever the pipe
                
                # 2. Latency Injection
                if INJECT_LATENCY > 0:
                    logging.warning(f"⏳ Holding response... injecting {INJECT_LATENCY}s latency.")
                    await asyncio.sleep(INJECT_LATENCY)
            
            # Forward the bytes
            writer.write(data)
            await writer.drain()
            
    except ConnectionResetError:
        pass # Expected when connections drop
    except Exception as e:
        logging.error(f"Pipe error ({direction}): {e}")
    finally:
        writer.close()

async def handle_client(local_reader, local_writer):
    """Triggered every time a new database connection is attempted."""
    try:
        remote_reader, remote_writer = await asyncio.open_connection(REMOTE_HOST, REMOTE_PORT)
        client_to_db = asyncio.create_task(pipe(local_reader, remote_writer, "Client -> DB"))
        db_to_client = asyncio.create_task(pipe(remote_reader, local_writer, "DB -> Client"))
        await asyncio.gather(client_to_db, db_to_client)
    except Exception as e:
        logging.error(f"Failed to connect to upstream database: {e}")
    finally:
        local_writer.close()

async def command_center():
    """Live interactive terminal running in a separate thread."""
    global INJECT_LATENCY, DROP_RATE
    await asyncio.sleep(0.5) # Give the server a moment to print its startup text
    
    print("\n" + "="*50)
    print("🎛️  FAULTLINE COMMAND CENTER")
    print("Commands: 'latency <sec>', 'drop <0.0-1.0>', 'status', 'reset'")
    print("="*50)
    
    while True:
        # Offload the blocking input() function to a background thread
        cmd = await asyncio.to_thread(input, "faultline> ")
        parts = cmd.strip().lower().split()
        if not parts:
            continue
            
        action = parts[0]
        try:
            if action == "latency":
                INJECT_LATENCY = float(parts[1])
                print(f"✅ Active Latency set to {INJECT_LATENCY}s")
            elif action == "drop":
                DROP_RATE = float(parts[1])
                print(f"✅ Packet Drop Rate set to {int(DROP_RATE * 100)}%")
            elif action == "status":
                print(f"📊 Status: Latency = {INJECT_LATENCY}s | Drop Rate = {int(DROP_RATE * 100)}%")
            elif action == "reset":
                INJECT_LATENCY = 0.0
                DROP_RATE = 0.0
                print("✅ All chaos parameters reset to normal.")
            else:
                print("❌ Unknown command. Try: latency, drop, status, reset")
        except (IndexError, ValueError):
            print("❌ Invalid syntax. Example: 'latency 2.5' or 'drop 0.5'")

async def main():
    server = await asyncio.start_server(handle_client, LOCAL_HOST, LOCAL_PORT)
    logging.info(f"⚠️  FaultLine Engine Online. Intercepting port {LOCAL_PORT}")
    
    # Run the TCP Server AND the Command Center simultaneously
    server_task = asyncio.create_task(server.serve_forever())
    cmd_task = asyncio.create_task(command_center())
    
    await asyncio.gather(server_task, cmd_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down FaultLine.")