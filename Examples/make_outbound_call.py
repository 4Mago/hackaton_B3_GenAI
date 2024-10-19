import os
from twilio_server import TwilioClient
from dotenv import load_dotenv
load_dotenv()
twilio_client = TwilioClient()
twilio_client.create_phone_call("", "", os.environ['RETELL_AGENT_ID'])#from,to