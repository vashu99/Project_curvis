import json
import os
from dotenv import load_dotenv
from fastapi.exceptions import HTTPException
from uuid import uuid4

load_dotenv()
from azure.cosmos import CosmosClient, PartitionKey, exceptions

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

url = os.environ['ACCOUNT_HOST']
key = os.environ['ACCOUNT_KEY']
# key = os.environ['ACCOUNT_KEY']
client = CosmosClient(url, credential=key)
database_name = 'CuvrisDB'
container_name = 'Conversations'
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)



twilio_client = TwilioClient()

# twilio_client.create_phone_number(213, os.environ['RETELL_AGENT_ID'])
# twilio_client.delete_phone_number("+12133548310")
# # # twilio_client.register_phone_agent("+14154750418", os.environ['RETELL_AGENT_ID'])
# twilio_client.create_phone_call("+447700153715", "+917303571379", os.environ['RETELL_AGENT_ID'])

from pydantic import BaseModel, Field

class UseCaseParameters(BaseModel):

    cuvris_agent_title: str
    provider_npi: str = Field(..., min_length=10, max_length=10)  # Example of using Field for validation
    provider_tax_id: str
    provider_name: str
    member_policy_id_number: str
    patient_dob: str
    member_first_name: str
    member_last_name: str
    member_phone_number: str
    member_address_line_1: str
    member_address_line_2: str
    member_state: str
    member_city: str
    member_zip_code: str
    member_pronouns: str
    claim_number: str
    callback_number: str
    insurance_number: str
    provider_state: str





class ConversationStartRequest(BaseModel):
    use_case_id: str
    use_case_parameters: UseCaseParameters





class QueryRequest(BaseModel):
    conversation_id: str
    query_text: str

class QueryResponse(BaseModel):
    query_response_text: str
    query_response_time: str
    conversation_status: str


conversations = {}

@app.post("/conversation", response_model=dict)
async def start_conversation(request: ConversationStartRequest):
    conversation_id = str(uuid4())
    conversation_data = {
        "id": conversation_id,
        "conversation_id": conversation_id,
        "use_case_id": request.use_case_id,
        "parameters": request.use_case_parameters.dict(),
        "status": "open",
        "messages": [],
        "call_id": None,
        "answers": "",
        "transcript": ""
    }

    
    container.upsert_item(conversation_data)

        # Trigger a phone call to the agent using Twilio
    try:
        call_response = twilio_client.create_phone_call("+447700153715", request.use_case_parameters.dict().get('member_phone_number'), os.environ['RETELL_AGENT_ID'],conversation_id=conversation_id)
        print(f"Call initiated successfully: {call_response}")
    except Exception as e:
        print(f"Failed to initiate call: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate phone call")

    return {"conversation_id": conversation_id}


# @app.post("/conversation", response_model=dict)
# async def start_conversation(request: ConversationStartRequest):
#     conversation_id = str(uuid4())
#     conversation_data = {
#         "id": conversation_id,
#         "use_case_id": request.use_case_id,
#         "parameters": request.use_case_parameters.dict(),
#         "status": "open",
#         "messages": [],
#         "call_id": ""
#     }
#     try:
        
#         url = f"https://48bc-115-241-34-101.ngrok-free.app/twilio-voice-webhook/{os.environ['RETELL_AGENT_ID']}?conversation_id={conversation_id}"

#         call_response = twilio_client.create_phone_call("+447700153715", "+917303571379", url=url)
#         print(f"Call initiated successfully: {call_response}")
#         # Store the call_id in the conversation data
#         # conversation_data['call_id'] = call_response['call_id']
#         # Upsert conversation data into Cosmos DB container
#         container.upsert_item(conversation_data)
#     except Exception as e:
#         print(f"Failed to initiate call: {e}")
#         raise HTTPException(status_code=500, detail="Failed to initiate phone call")
#     return {"conversation_id": conversation_id}

# @app.post("/conversation", response_model=dict)
# async def start_conversation(request: ConversationStartRequest):
#     conversation_id = str(uuid4())
#     conversation_data = {
#         "id": conversation_id,
#         "use_case_id": request.use_case_id,
#         "parameters": request.use_case_parameters.dict(),
#         "status": "open",
#         "messages": [],
#         "call_id": None  # Placeholder for call_id to be updated after call initiation
#     }

#     # Store initial conversation data
#     container.upsert_item(conversation_data)

#     # Trigger a phone call to the agent using Twilio
#     try:
#         call_response = twilio_client.create_phone_call("+447700153715", "+917303571379", os.environ['RETELL_AGENT_ID'])
#         print(f"Call initiated successfully: {call_response}")

#         # Assuming call_response contains call_id

#         call_respons2 = twilio_client.retell.register_call(operations.RegisterCallRequestBody(
#             agent_id=os.environ['RETELL_AGENT_ID'], 
#             audio_websocket_protocol="twilio", 
#             audio_encoding="mulaw", 
#             sample_rate=8000
#         ))
#         conversation_data['call_id'] = call_respons2.call_detail.call_id
#         container.upsert_item(conversation_data)  # Update the item with call_id

#     except Exception as e:
#         print(f"Failed to initiate call: {e}")
#         raise HTTPException(status_code=500, detail="Failed to initiate phone call")

#     return {"conversation_id": conversation_id, "call_id": call_response['call_id']}


# @app.post("/conversation", response_model=dict)
# async def start_conversation(request: ConversationStartRequest):
#     conversation_id = str(uuid4())
#     conversations[conversation_id] = {
#         "use_case_id": request.use_case_id,
#         "parameters": request.use_case_parameters.dict(),
#         "status": "open",
#         "messages": []
#     }


#     return {"conversation_id": conversation_id}


# import time

# @app.post("/conversation/query", response_model=QueryResponse)
# async def query_conversation(request: QueryRequest):
#     start_time = time.time()

#     # Check if the conversation exists and is open
#     conversation = conversations.get(request.conversation_id)
#     if not conversation:
#         raise HTTPException(status_code=404, detail="Conversation not found")
#     if conversation["status"] == "closed":
#         raise HTTPException(status_code=400, detail="Conversation is closed")

#     # Here you might simulate a response or integrate with your AI logic
#     # Simulated response for demonstration
#     response_text = "Simulated response to the query: " + request.query_text
#     response_time = f"{time.time() - start_time:.2f} seconds"

#     # Update the conversation history (if needed)
#     conversation["messages"].append({
#         "query": request.query_text,
#         "response": response_text
#     })

#     # Optionally, update the status of the conversation based on some logic
#     # For example, conversation["status"] = "closed" if some condition is met

#     return QueryResponse(
#         query_response_text=response_text,
#         query_response_time=response_time,
#         conversation_status=conversation["status"]
#     )



# twilio_client = TwilioClient()

# twilio_client.create_phone_number(213, os.environ['RETELL_AGENT_ID'])
# twilio_client.delete_phone_number("+12133548310")
# twilio_client.register_phone_agent("+14154750418", os.environ['RETELL_AGENT_ID'])
# twilio_client.create_phone_call("+14154750418", "+13123156212", os.environ['RETELL_AGENT_ID'])

@app.post("/twilio-voice-webhook/{agent_id_path}")
async def handle_twilio_voice_webhook(request: Request, agent_id_path: str, conversation_id: str):
    conversation_id = conversation_id
    print(f"Conversation ID: {conversation_id}")
    try:
        # Check if it is machine
        post_data = await request.form()
     
        if 'AnsweredBy' in post_data and post_data['AnsweredBy'] == "machine_start":
            twilio_client.end_call(post_data['CallSid'])
            return PlainTextResponse("")
        elif 'AnsweredBy' in post_data:
            return PlainTextResponse("") 

        call_response = twilio_client.retell.register_call(operations.RegisterCallRequestBody(
            agent_id=agent_id_path, 
            audio_websocket_protocol="twilio", 
            audio_encoding="mulaw", 
            sample_rate=8000
        ))

        # conversation_id = post_data.get('ConversationId')  # Assume you pass the ConversationId in the form data
        # conversation = container.read_item(item=conversation_id, partition_key=conversation_id)
        # conversation['call_id'] = call_response.call_detail.call_id
        # container.upsert_item(conversation)
        
        if call_response.call_detail:

            conversation = container.read_item(item=conversation_id, partition_key=conversation_id)
            # print(conversation)
            # print(call_response.call_detail.call_id)
            # Update the conversation with the new call_id
            conversation['call_id'] = call_response.call_detail.call_id
            # print(conversation['call_id'])
            # Upsert the updated conversation back into the database
            container.upsert_item(conversation)

            response = VoiceResponse()
            start = response.connect()
            start.stream(url=f"wss://api.retellai.com/audio-websocket/{call_response.call_detail.call_id}")

            # container.upsert_item(body={"call_id": call_response.call_detail.call_id})
     
           
            return PlainTextResponse(str(response), media_type='text/xml')
    except Exception as err:
        print(f"Error in twilio voice webhook: {err}")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})



# @app.websocket("/llm-websocket/{call_id}")
# async def websocket_handler(websocket: WebSocket, call_id: str):
#     await websocket.accept()
#     print(f"Handle llm ws for: {call_id}")
    
#     # conversation = conversations.get(request.conversation_id)
#     # # Extract parameters
#     # use_case_parameters = conversations[call_id]['parameters']
#     # use_case_id = conversations[call_id]['use_case_id']

#     # Initialize LlmClient with the extracted parameters
#     llm_client = LlmClient()

#     # Send first message to signal readiness of server
#     response_id = 0
#     first_event = llm_client.draft_begin_message()
#     await websocket.send_text(json.dumps({"message": first_event}))

#     async def stream_response(request):
#         nonlocal response_id
#         for event in llm_client.draft_response(request):
#             await websocket.send_text(json.dumps(event))
#             if request['response_id'] < response_id:
#                 return  # New response needed, abandon this one
            











# from azure.cosmos.exceptions import CosmosResourceNotFoundError

# @app.websocket("/llm-websocket/{call_id}")
# async def websocket_handler(websocket: WebSocket, call_id: str):
#     await websocket.accept()

#     try:
#         # Query to find the conversation item by call_id
#         query = "SELECT * FROM c WHERE c.call_id = @call_id"
#         items = list(container.query_items(
#             query=query,
#             parameters=[{"name": "@call_id", "value": call_id}],
#             enable_cross_partition_query=True
#         ))
#         if not items:
#             raise CosmosResourceNotFoundError

#         conversation_data = items[0]
#         print(f"Conversation data fetched successfully: {conversation_data}")

#     except CosmosResourceNotFoundError:
#         print("Conversation not found in the database.")
#         await websocket.close(code=1002)
#         return
#     except Exception as e:
#         print(f"Error fetching conversation data: {e}")
#         await websocket.close(code=1011)
#         return

#     # # Fetch the conversation details from Cosmos DB
#     # try:
#     #     conversation_data = container.read_item(item=call_id, partition_key=call_id)
#     #     print(f"Conversation data fetched successfully: {conversation_data}")
#     # except CosmosResourceNotFoundError:
#     #     print("Conversation not found in the database.")
#     #     await websocket.close(code=1002)  # Close the connection with appropriate WebSocket close code
#     #     return
#     # except Exception as e:
#     #     print(f"Error fetching conversation data: {e}")
#     #     await websocket.close(code=1011)  # Unexpected condition that prevented the request from being fulfilled
#     #     return

#     # Use llm_client configured with fetched data
#     llm_client = LlmClient(conversation_data['use_case_id'], conversation_data['parameters'])

#     # send first message to signal readiness of server
#     response_id = 0
#     first_event = llm_client.draft_begin_message()  # Ensure this function exists and is correctly named
#     await websocket.send_text(json.dumps(first_event))

#     async def stream_response(request):
#         nonlocal response_id
#         for event in llm_client.draft_response(request):
#             await websocket.send_text(json.dumps(event))
#             if request['response_id'] < response_id:
#                 return  # new response needed, abandon this one

#     try:
#         while True:
#             message = await websocket.receive_text()
#             request = json.loads(message)
#             if 'response_id' not in request:
#                 continue  # no response needed, process live transcript update if needed
#             response_id = request['response_id']
#             asyncio.create_task(stream_response(request))
#     except WebSocketDisconnect:
#         print(f"WebSocket disconnected for {call_id}")
#     except Exception as e:
#         print(f'WebSocket error for {call_id}: {e}')
#     finally:
#         # Optional: summarize and log the transcript
#         if 'transcript' in request:
#             summarize_transcript(request['transcript'])
#             for utterance in request['transcript']:
#                 if utterance["role"] == "agent":
#                     print(f"Agent:- {utterance['content']}")
#                 else:
#                     print(f"User:- {utterance['content']}")
#             print("Conversation transcript processed", request['transcript'])
#         print(f"WebSocket connection closed for {call_id}")

# This function should be inside or accessible by your llm_with_function_calling.py logic
def update_conversation_answers(call_id, answers):
    # Perform a cross-partition query to find the conversation by call_id
    query = "SELECT * FROM c WHERE c.call_id = @call_id"
    parameters = [{"name": "@call_id", "value": call_id}]
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))

    if not items:
        print(f"No conversation found for call_id: {call_id}")
        return False

    # Assuming the first match is what you need
    conversation_item = items[0]

    # Update the conversation item with new answers

    
    if 'answers' in conversation_item:
        conversation_item['answers'] += f"{answers}"  # Append new answers
    else:
        conversation_item['answers'] = answers  # Initialize if not present

    # Upsert the updated item back into the database
    try:
        container.upsert_item(conversation_item)
        
        return True
    except Exception as e:
        print(f"Failed to update conversation: {e}")
        return False


# def full_transcript(call_id,transcript):
#     query = "SELECT * FROM c WHERE c.call_id = @call_id"
#     parameters = [{"name": "@call_id", "value": call_id}]
#     items = list(container.query_items(
#         query=query,
#         parameters=parameters,
#         enable_cross_partition_query=True
#     ))

#     if not items:
#         print(f"No conversation found for call_id: {call_id}")
#         return False

#     # Assuming the first match is what you need
#     conversation_item = items[0]

#     # Update the conversation item with new answers

    
#     if 'answers' in conversation_item:
#         conversation_item['answers'] += f"{answers}"  # Append new answers
#     else:
#         conversation_item['answers'] = answers  # Initialize if not present

#     # Upsert the updated item back into the database
#     try:
#         container.upsert_item(conversation_item)
        
#         return True
#     except Exception as e:
#         print(f"Failed to update conversation: {e}")
#         return False
    

@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    await websocket.accept()
    print(f"Handle llm ws for: {call_id}")
    print(f"😁😁😁😁😁 {websocket}")

    
    # Perform a cross-partition query to find the conversation by call_id
    query = "SELECT * FROM c WHERE c.call_id = @call_id"
    parameters = [{"name": "@call_id", "value": call_id}]
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))


    if not items:
        print(f"No conversation found for call_id: {call_id}")
        await websocket.close(code=1011)  # Internal error
        return

    # Assuming the first match is what you need
    conversation = items[0]
    use_case_id = conversation['use_case_id']
    use_case_parameters = conversation['parameters']

 

    # Initialize LlmClient with fetched data
    llm_client = LlmClient(use_case_id=use_case_id, use_case_parameters=use_case_parameters )


    # llm_client = LlmClient()

    # send first message to signal ready of server
    response_id = 0
    first_event = llm_client.draft_begin_message()
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
            await stream_response(request)
            # asyncio.create_task(stream_response(request))
            print(f"🤣{llm_client.answers}")
           



    except WebSocketDisconnect:
        print(f"LLM WebSocket disconnected for {call_id}")
    except Exception as e:
        print(f'LLM WebSocket error for {call_id}: {e}')
    finally:
        
        update_conversation_answers(call_id, llm_client.answers)
       ##upload full transcript to azure
        # print(f"🤣🤣🤣🤣🤣🤣🤣🤣🤣🤣🤣{request['transcript']}")

        # print(request['transcript']['content'])
       
        # update_conversation_answers(call_id,request['transcript'])
        # summarize_transcript(request['transcript'])
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


# ggne;