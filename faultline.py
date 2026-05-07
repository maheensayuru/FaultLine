import asyncio
import logging

# Brutalist terminal logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [FAULTLINE] - %(message)s', datefmt='%H:%M:%S')

# Configuration
LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 3307       # Your backend connects here
REMOTE_HOST = '127.0.0.1'
REMOTE_PORT = 3306      # The real MySQL database port

# --- CHAOS PARAMETERS ---
INJECT_LATENCY = 3.0    # Set to 3.0 to simulate a locked database

async def pipe(reader, writer, direction):
    """Shuttles raw bytes between the client and the database."""
    try:
        while not reader.at_eof():
            data = await reader.read(4096)
            if not data:
                break

            # 🛑 THE CHAOS INJECTION ZONE 🛑
            if direction == "DB -> Client" and INJECT_LATENCY > 0:
                logging.warning(f"Holding database response... injecting {INJECT_LATENCY}s latency.")
                await asyncio.sleep(INJECT_LATENCY)
            
            # Forward the bytes to their destination
            writer.write(data)
            await writer.drain()
            
    except ConnectionResetError:
        logging.warning(f"Connection dropped ({direction})")
    except Exception as e:
        logging.error(f"Pipe error ({direction}): {e}")
    finally:
        writer.close()

async def handle_client(local_reader, local_writer):
    """Triggered every time a new database connection is attempted."""
    client_addr = local_writer.get_extra_info('peername')
    logging.info(f"Intercepted database connection from {client_addr}")

    try:
        # Open a connection to the REAL database
        remote_reader, remote_writer = await asyncio.open_connection(REMOTE_HOST, REMOTE_PORT)
        
        # Create bi-directional, concurrent pipes
        client_to_db = asyncio.create_task(pipe(local_reader, remote_writer, "Client -> DB"))
        db_to_client = asyncio.create_task(pipe(remote_reader, local_writer, "DB -> Client"))
        
        # Run both pipes simultaneously
        await asyncio.gather(client_to_db, db_to_client)
        
    except Exception as e:
        logging.error(f"Failed to connect to upstream database: {e}")
    finally:
        local_writer.close()

async def main():
    server = await asyncio.start_server(handle_client, LOCAL_HOST, LOCAL_PORT)
    logging.info(f"⚠️  FaultLine Chaos Engine Online.")
    logging.info(f"[*] Intercepting on port {LOCAL_PORT}...")
    logging.info(f"[*] Forwarding to upstream database at {REMOTE_HOST}:{REMOTE_PORT}")
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down FaultLine engine.")