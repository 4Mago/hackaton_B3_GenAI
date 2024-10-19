import streamlit as st
from PIL import Image
import base64
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import requests
import json
import os
import asyncio
import websockets
from dotenv import load_dotenv
load_dotenv()


with st.sidebar:
    openai_api_key = os.getenv('OPENAI_API_KEY')
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

# Title of the app
st.title("Capture and Display Image")

# Capture image from camera
captured_image = st.camera_input("Take a picture")

async def connect_websocket(call_data):
    """
    Establish a WebSocket connection using the information from the call_data.
    
    Parameters:
    - call_data (dict): The response data from which the access_token and websocket_url will be extracted.
    """
    try:
        # Extract access_token and websocket_url from the call_data
        access_token = call_data.get('access_token')
        
        if not access_token:
            raise ValueError("Missing access_token or websocket_url in call_data")

        # Establish WebSocket connection
        async with websockets.connect(f"wss://https://api.retellai.com/v2/create-web-call") as ws:
            # Send the access token for authentication
            await ws.send(json.dumps({
                "type": "connect",
                "access_token": access_token
            }))
            
            # Wait for the connection to be established
            response = await ws.recv()
            print("WebSocket connection established successfully")
            print(f"Received: {response}")
            
            # You can keep the connection open or handle further communication here
            # For example, continuously listen to the WebSocket
            while True:
                message = await ws.recv()
                print(f"Received message: {message}")
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")


_size = st.empty()
_mode = st.empty()
_format = st.empty()
_content = st.empty()


if captured_image is not None:
    # Display the captured image
    bytes_data = captured_image.getvalue()
    st.image(captured_image, caption='Captured Image', use_column_width=True)

    # Show Image property
    im = Image.open(captured_image)
    # im.show()
    _size.markdown(f"<h6>Image size : {str(im.size)}</h6>", unsafe_allow_html=True)
    _mode.text("Image mode : " + str(im.mode))
    _format.text("Image mode : " + str(im.format))
    
    image_base64 = base64.b64encode(bytes_data).decode("utf-8")
    # _content.markdown(f"<h6>Image content : {image_base64}</h6>", unsafe_allow_html=True)
 
    model = ChatOpenAI(model="gpt-4o", openai_api_key=openai_api_key)
 
    message = HumanMessage(
        content=[
            {"type": "text", "text": "describe the weather in this image"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            },
        ],
    )
    response = model.invoke([message])
    st.write("Image Analysis:")
    st.write(response.content)

    agent_id = os.getenv('RETELL_AGENT_ID')
    retell_ai_api_key = os.getenv('RETELL_API_KEY')
    body = {
        "agent_id": agent_id,
        "inputText": response.content,
    }

    metadata = st.text_area("Enter Metadata (JSON format)", value="{}")

    # Make the API call to Retell AI
    retell_ai_url = "https://api.retellai.com/v2/create-web-call"
    headers = {
        "Authorization": f"Bearer {retell_ai_api_key}",
        "Content-Type": "application/json"
    }



    if st.button("Create Web Call") and all([agent_id, metadata]):
        try:
            data = {
                "agent_id": agent_id,
                "metadata": json.loads(metadata),
            }
            
            response = requests.post(
                "https://api.retellai.com/v2/create-web-call",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 201:
                st.success(response.json())
                call_data = response.json()
                
                # Extract the access token
                asyncio.run(connect_websocket(call_data))
                    
                print("WebSocket connection established successfully")


            else:
                st.error(f"Failed to create web call. Status code: {response.status_code}")
                st.json(response.json())
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

