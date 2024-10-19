import asyncio
import websockets
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load the API key from an environment variable (recommended for security)
RETELL_API_KEY = os.getenv('RETELL_API_KEY')

# If you haven't set an environment variable, you can hardcode it (less secure):
# RETELL_API_KEY = 'your_api_key_here'

# Initialize the set of connected clients
connected_clients = set()

async def connect_to_retell():
    # Include the API key in the WebSocket URL
    retell_ws_url = f"wss://api.retellai.com/v1/call?api_key={RETELL_API_KEY}"
    
    try:
        return await websockets.connect(retell_ws_url)
    except Exception as e:
        logging.error(f"Failed to connect to Retell: {e}")
        raise

async def handle_client(websocket, path):
    connected_clients.add(websocket)
    try:
        retell_ws = await connect_to_retell()
        try:
            async def forward_to_retell():
                async for message in websocket:
                    await retell_ws.send(message)

            async def forward_to_client():
                async for message in retell_ws:
                    await websocket.send(message)

            await asyncio.gather(forward_to_retell(), forward_to_client())
        finally:
            await retell_ws.close()
    except Exception as e:
        logging.error(f"Error in handle_client: {e}")
    finally:
        connected_clients.remove(websocket)

async def main():
    server = await websockets.serve(handle_client, "localhost", 8765)
    logging.info("Server started on localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
