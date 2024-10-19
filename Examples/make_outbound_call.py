import socket
import json
import time

class RetellAIUDPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.conversation_id = None

    def start_conversation(self, initial_context):
        message = {
            "type": "start",
            "payload": {
                "context": initial_context
            }
        }
        self._send_message(message)
        response = self._receive_message()
        self.conversation_id = response.get("conversation_id")
        return response

    def send_message(self, text):
        if not self.conversation_id:
            raise ValueError("Conversation not started. Call start_conversation first.")
        
        message = {
            "type": "message",
            "payload": {
                "conversation_id": self.conversation_id,
                "text": text
            }
        }
        self._send_message(message)
        return self._receive_message()

    def _send_message(self, message):
        self.sock.sendto(json.dumps(message).encode(), (self.host, self.port))

    def _receive_message(self):
        data, _ = self.sock.recvfrom(4096)
        return json.loads(data.decode())

    def close(self):
        self.sock.close()

# Example usage
if __name__ == "__main__":
    client = RetellAIUDPClient("api.retell.ai", 12345)  # Replace with actual host and port
    
    # Start conversation
    initial_context = "This conversation is about a picture of a sunset over the ocean."
    response = client.start_conversation(initial_context)
    print("Conversation started:", response)

    # Send a message
    user_message = "What can you tell me about the sunset in the picture?"
    response = client.send_message(user_message)
    print("AI response:", response)

    # Close the connection
    client.close()