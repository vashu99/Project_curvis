import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.websockets import WebSocketState
from llm import LlmClient
from llm_with_func_calling import LlmClient
from twilio_server import TwilioClient
from retellclient.models import operations
from twilio.twiml.voice_response import VoiceResponse
import asyncio
from openai import AzureOpenAI
import datetime
import requests
load_dotenv(override=True)

app = FastAPI()

twilio_client = TwilioClient()
use_case_id = "patient_eligibility_verification"
cuvris_agent_title = "amy"
provider_npi="1234567893"
provider_tax_id=""
provider_name="Dr. Lucas Green"
member_policy_id_number="JPU666X15903"
member_first_name="Michael"
member_last_name="Johnson"
member_phone_number=""
member_address_line_1 = ""
member_address_line_2 = ""
member_state=""
member_city=""
member_zip_code=""
member_pronouns=""
claim_number=""
callback_number=""
insurance_number=""
provider_state="Illinois"
# twilio_client.create_phone_number(213, os.environ['RETELL_AGENT_ID'])
# twilio_client.delete_phone_number("+12133548310")
# twilio_client.register_phone_agent("+14154750418", os.environ['RETELL_AGENT_ID'])
twilio_client.create_phone_call("+447700153715", "+917303571379", os.environ['RETELL_AGENT_ID'])



@app.post("/twilio-voice-webhook/{agent_id_path}")
async def handle_twilio_voice_webhook(request: Request, agent_id_path: str):
    try:
        # Check if it is machine
        post_data = await request.form()
        # if 'AnsweredBy' in post_data and post_data['AnsweredBy'] == "machine_start":
        #     twilio_client.end_call(post_data['CallSid'])
        #     return PlainTextResponse("")
        if 'AnsweredBy' in post_data:
            return PlainTextResponse("") 

        call_response = twilio_client.retell.register_call(operations.RegisterCallRequestBody(
            agent_id=agent_id_path, 
            audio_websocket_protocol="twilio", 
            audio_encoding="mulaw", 
            sample_rate=8000
        ))
        if call_response.call_detail:
            print(call_response)
            print(call_response.call_detail)
            response = VoiceResponse()
            start = response.connect()
            start.stream(url=f"wss://api.retellai.com/audio-websocket/{call_response.call_detail.call_id}")
            print(PlainTextResponse(str(response), media_type='text/xml'))
            return PlainTextResponse(str(response), media_type='text/xml')
    except Exception as err:
        print(f"Error in twilio voice webhook: {err}")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})


@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    await websocket.accept()
    print(f"Handle llm ws for: {call_id}")
    print(f"😁😁😁😁😁 {websocket}")

    llm_client = LlmClient()

    # send first message to signal ready of server
    response_id = 0
    first_event = llm_client.draft_begin_messsage()
    await websocket.send_text(json.dumps(first_event))

    async def stream_response(request):
        nonlocal response_id
        for event in llm_client.draft_response(request):
            await websocket.send_text(json.dumps(event))
            if request['response_id'] < response_id:
                return # new response needed, abondon this one
    try:
        while True:
            message = await websocket.receive_text()
            request = json.loads(message)
            # print out transcript
            # os.system('cls' if os.name == 'nt' else 'clear')
            # print(json.dumps(request, indent=4))
            
            if 'response_id' not in request:
                continue # no response needed, process live transcript update if needed
            response_id = request['response_id']
            asyncio.create_task(stream_response(request))
    except WebSocketDisconnect:
        print(f"LLM WebSocket disconnected for {call_id}")
    except Exception as e:
        print(f'LLM WebSocket error for {call_id}: {e}')
    finally:
        summarize_transcript(request['transcript'])
        for utterance in request['transcript']:
            if utterance["role"] == "agent":
                print(f"Agent:- {utterance['content']}")
            else:
                print(f"User:- {utterance['content']}")
        print("🤢🤢🤢🤢", request['transcript'])
        print(f"LLM WebSocket connection closed for {call_id}")
# client = OpenAI(
#             organization=os.environ['OPENAI_ORGANIZATION_ID'],
#             api_key=os.environ['OPENAI_API_KEY'],
#         )
client  = AzureOpenAI(
           azure_endpoint = os.environ['AZURE_OPENAI_ENDPOINT'],
            api_key=os.environ['AZURE_OPENAI_KEY'],
            api_version="2024-02-01"
            
        )
def summarize_transcript( transcript):
    messages = ""
    for utterance in transcript:
        if utterance["role"] == "agent":
            messages += f'Agent: {utterance["content"]}\n'
        else:
            messages += f'User: {utterance["content"]}\n'
    prompt = [{
        "role": "system",
        "content": "You are a conversational AI tasked with summarizing the following conversation between a user and an agent.\n"
        "The user and agent messages are provided in the format: 'User: [message]' and 'Agent: [message]'.\n"
        "Please generate a brief summary of the conversation based on the provided transcript.\n"
        "Summary:"
        },
        {
        "role": "user",
        "content": messages
        }]
    # stream = client.chat.completions.create(
    #         model="gpt-3.5-turbo-1106",
    #         messages=prompt,
    #         stream=False,
    #     )
    stream = client.chat.completions.create(
        # model = "gpt-3.5-turbo-1106",
        model=os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'],
        messages=prompt,
        stream=False,
        )
    # url_to_create_token = f"https://accounts.zoho.{zoho_location}/oauth/v2/token?refresh_token={zoho_crm_refresh_token}&client_id={zoho_client_id}&client_secret={zoho_client_secret}&grant_type=refresh_token"
    # getting_token = requests.post(url_to_create_token)
    # getting_token_json = getting_token.json()
    # print("🦊🦊🦊", getting_token_json)
    now = datetime.datetime.now()

    # # Subtract 10 minutes from the current datetime
    # ten_minutes_ago = now - datetime.timedelta(minutes=10)
    # # Format datetime as a string
    # formatted_date_time = ten_minutes_ago.strftime('%Y-%m-%dT%H:%M:%S')+ "+05:30"
    # print("🙏🙏🙏 ",formatted_date_time)
    # headers = {
    #     "Authorization": f"Bearer {getting_token_json['access_token']}",
    #     "Content-Type": "Content-Type"
    # }
    # try:
    #     url = f"https://www.zohoapis.{zoho_location}/crm/v6/Calls"
    #     data = {
    #         "data": [
    #         {
    #             "Description": f"{stream.choices[0].message.content}",
    #             "Call_Start_Time": formatted_date_time,
    #             "Subject": "AI Based Call",
    #             "Call_Type": "Inbound",
    #             "Call_Duration": "10:00"
    #         }
    #     ]
    #     }
    #     json_data = json.dumps(data)
    #     response = requests.post(url, headers=headers, data=json_data)
    #     if response.status_code == 200:
    #         print("🦊🦊🦊", response.text)
    #     else:
    #         print("🦊🦊🦊", response.status_code, response.text)
    # except Exception as err:
    #     print(f"Error in twilio voice webhook: {err}")