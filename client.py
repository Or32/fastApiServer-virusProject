import asyncio
import websockets

async def connect_to_server():
    uri = "ws://localhost:8000/ws"  # Replace with the server address and port

    async with websockets.connect(uri) as websocket:
        # Receive the public key from the server
        public_key = await websocket.recv()
        print(f"Received public key: {public_key}")

        # Send an encrypted message to the server
        message = "Hello, server!"
        encrypted_message = encrypt_message(message, public_key)
        await websocket.send(encrypted_message)

        # Receive a message from the server
        response = await websocket.recv()
        print(f"Received response from server: {response}")

asyncio.run(connect_to_server())