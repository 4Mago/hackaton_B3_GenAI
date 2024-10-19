from retell import Retell
import os

client = Retell(
    api_key="key_a44383eeb59170321d311be3f219",
)
web_call_response = client.call.create_web_call(
    agent_id="agent_272f318329a62259f8e9d8179f",
)
print(web_call_response.agent_id)