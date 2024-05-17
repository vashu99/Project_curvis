import json
import os
from dotenv import load_dotenv
from fastapi.exceptions import HTTPException
from uuid import uuid4
import time

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
from typing import Dict
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


session_states: Dict[str, Dict] = {}
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
    print(os.environ['RETELL_AGENT_ID'], "aaaaaaakkfkfklrkklergoi4jgtrjgoi[tj]")
        # Trigger a phone call to the agent using Twilio
    try:
        call_response = twilio_client.create_phone_call("+447700153715", request.use_case_parameters.dict().get('member_phone_number'), os.environ['RETELL_AGENT_ID'],conversation_id=conversation_id)
        print(f"Call initiated successfully: {call_response}")
    except Exception as e:
        print(f"Failed to initiate call: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate phone call")

    return {"conversation_id": conversation_id}



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

    
        if call_response.call_detail:

            conversation = container.read_item(item=conversation_id, partition_key=conversation_id)
            
            conversation['call_id'] = call_response.call_detail.call_id
            
            container.upsert_item(conversation)

            response = VoiceResponse()
            start = response.connect()
            start.stream(url=f"wss://api.retellai.com/audio-websocket/{call_response.call_detail.call_id}")
           
            return PlainTextResponse(str(response), media_type='text/xml')
    except Exception as err:
        print(f"Error in twilio voice webhook: {err}")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})



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


@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    timea = time.time()
    await websocket.accept()
    print(time.time() - timea, "WebSocket Accept")

    # Perform a cross-partition query to find the conversation by call_id
    query = "SELECT * FROM c WHERE c.call_id = @call_id"
    parameters = [{"name": "@call_id", "value": call_id}]
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    print(time.time() - timea, "DB Query")

    
    if not items:
        print(f"No conversation found for call_id: {call_id}")
        await websocket.close(code=1011)  # Internal error
        return
    
    async def generate_response(query, session_id):
        # Update session history
        print("thereeeeeeeeeeeeee")
        session = session_states[session_id]
        session['history'].append(query)
        # Construct the prompt based on the session state and query
        prompt = construct_prompt(query, session)

        # Call Azure OpenAI API
        stream = client.chat.completions.create(
            # model = "gpt-3.5-turbo-1106",
            model=os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'],
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": ""
                }
            ],
            stream=True,
            stop=None,
            temperature=0.5
        )
        for chunk in stream:
            response_text = chunk.choices[0].delta.content.strip()
            session['history'].append(response_text)
            update_session_state(session_id)  # Update the session state based on the response
            yield response_text


    try:
        while True:
            print("hereeeeeeeeeeeeee")
            data = await websocket.receive_text()
            async for response in generate_response(data, call_id):
                await websocket.send_text(response)
           



    except WebSocketDisconnect:
        print(f"LLM WebSocket disconnected for {call_id}")
    except Exception as e:
        print(f'LLM WebSocket error for {call_id}: {e}')
    finally:
        pass
        
client = AzureOpenAI(
    azure_endpoint = os.environ['AZURE_OPENAI_ENDPOINT'],
    api_key=os.environ['AZURE_OPENAI_KEY'],
    api_version="2024-02-01"
    
)



async def generate_response(query, session_id):
    # Update session history
    print("thereeeeeeeeeeeeee")
    session = session_states[session_id]
    session['history'].append(query)
    # Construct the prompt based on the session state and query
    prompt = construct_prompt(query, session)

    # Call Azure OpenAI API
    stream = client.chat.completions.create(
        # model = "gpt-3.5-turbo-1106",
        model=os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'],
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": ""
            }
        ],
        stream=True,
        stop=None,
        temperature=0.5
    )
    for chunk in stream:
        response_text = chunk.choices[0].delta.content.strip()
        session['history'].append(response_text)
        update_session_state(session_id)  # Update the session state based on the response
        yield response_text

def construct_prompt(session: Dict) -> str:
    step = session['step']
    history = session['history']

    # Introduction and context setup for OpenAI
    prompt = f"Agent conversation history:\n{'. '.join(history)}\n\n"

    # Agent introduces the purpose of the call
    if step == 1:
        prompt += "You are an agent calling a healthcare provider's office to verify a member's eligibility and benefits. "
        prompt += "Your task is to provide the necessary member details and respond accurately to the provider's questions to verify information.\n"
        prompt += "Start by introducing yourself and explaining the purpose of the call.\n\n"
        prompt += "Agent: Good morning, this is [Your Name] calling from [Your Company]. I am calling to verify the eligibility and benefit details for one of our members under your care.\n"

    # Dynamics of conversation based on what the provider's agent asks
    if 'last_provider_question' in session:
        # Handling of provider's questions based on the last interaction recorded
        provider_question = session['last_provider_question']
        prompt += f"Provider's last question: {provider_question}\n"
        prompt += "Respond to the provider's question with the necessary details. For example:\n"
        if 'NPI' in provider_question or 'provider details' in provider_question.lower():
            prompt += "Agent: The provider's NPI is [NPI Number], and the name under the NPI is [Provider's Name]. The state of registration is [State].\n"
        elif 'member ID' in provider_question or 'date of birth' in provider_question.lower():
            prompt += "Agent: The member’s Policy ID Number is [Policy ID], their full name is [Member's Name], and their date of birth is [DOB].\n"
        else:
            prompt += "Agent: Could you please specify what particular details you need for the verification?\n"
    else:
        # Initial interaction if no questions have been recorded yet
        prompt += "Wait for the provider to ask the first question. Prepare to provide details such as the member's policy ID, name, date of birth, etc.\n"

    # Suggest how to continue the conversation based on the playbook
    prompt += "\nContinue the conversation, ensuring you provide accurate and complete responses to verify the member's information.\n"

    return prompt

def update_session_state(session_id: str):
    # Update the state logic based on response and current step
    session = session_states[session_id]
    session['step'] += 1  # This is a simplified example of advancing the conversation step
