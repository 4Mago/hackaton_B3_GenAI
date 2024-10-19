import streamlit as st
# from openai import OpenAI
from PIL import Image
import base64
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import requests
import json
load_dotenv()


 
with st.sidebar:
    openai_api_key = os.getenv('OPENAI_API_KEY')
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

_size = st.empty()
_mode = st.empty()
_format = st.empty()
_content = st.empty()
 
uploaded_file = st.file_uploader("Choose an imaeg: ", [".png", ".jpg", ".jpeg"] )
if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    #st.write(bytes_data)
 
    st.image(uploaded_file)
 
    # Show Image property
    im = Image.open(uploaded_file)
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

# Assuming you have a Retell AI API key
retell_ai_api_key = os.getenv('RETELL_AI_API_KEY')

# Prepare the data for the Retell AI API call
retell_ai_data = {
    "context": response.content,
    # Add any other parameters required by the Retell AI API
}

# Make the API call to Retell AI
retell_ai_url = "https://api.retell.ai/v1/generate"  # Replace with the actual Retell AI API endpoint
headers = {
    "Authorization": f"Bearer {retell_ai_api_key}",
    "Content-Type": "application/json"
}

try:
    retell_ai_response = requests.post(retell_ai_url, headers=headers, data=json.dumps(retell_ai_data))
    retell_ai_response.raise_for_status()  # Raise an exception for bad status codes
    
    # Parse the Retell AI response
    retell_ai_result = retell_ai_response.json()
    
    # Display the Retell AI result
    st.write("Retell AI Analysis:")
    st.write(retell_ai_result)
except requests.exceptions.RequestException as e:
    st.error(f"Error making request to Retell AI: {e}")
except json.JSONDecodeError:
    st.error("Error decoding response from Retell AI")