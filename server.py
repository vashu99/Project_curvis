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
from typing import Dict, List
load_dotenv(override=True)

app = FastAPI()
clientAzure = AzureOpenAI(
    azure_endpoint = os.environ['AZURE_OPENAI_ENDPOINT'],
    api_key=os.environ['AZURE_OPENAI_KEY'],
    api_version="2024-02-01"
    # azure_endpoint = "https://curvisagentai.openai.azure.com/",
    # api_key="9812c9489d1442c4989cef682be0001d",
    # api_version="2024-02-01",
    
)
url = os.environ['ACCOUNT_HOST']
key = os.environ['ACCOUNT_KEY']
# key = os.environ['ACCOUNT_KEY']
client = CosmosClient(url, credential=key)
database_name = 'CuvrisDB'
container_name = 'Conversations'
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)
model_name = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']


twilio_client = TwilioClient()

# twilio_client.create_phone_number(213, os.environ['RETELL_AGENT_ID'])
# twilio_client.delete_phone_number("+12133548310")
# # # twilio_client.register_phone_agent("+14154750418", os.environ['RETELL_AGENT_ID'])
# twilio_client.create_phone_call("+447700153715", "+917303571379", os.environ['RETELL_AGENT_ID'])
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


class ConversationResponse(BaseModel):
    conversation_status: str
    conversation_messages: List
    use_case_outputs: Dict

class GetConversationInfoResponse(BaseModel):
    conversation_status: str
    conversation_messages: List
    use_case_outputs: list



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




@app.post("/conversation/query", response_model=QueryResponse)
async def query_conversation(request: QueryRequest):
    start_time = time.time()

    # Check if the conversation exists and is open
    
    conversation = container.read_item(item=request.conversation_id, partition_key=request.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Here you might simulate a response or integrate with your AI logic
    # Simulated response for demonstration
    response_text = conversation_query(conversation['output'][0], conversation['transcript'], request.query_text)
    response_time = f"{time.time() - start_time:.2f} seconds"

    # Optionally, update the status of the conversation based on some logic
    # For example, conversation["status"] = "closed" if some condition is met

    return QueryResponse(
        query_response_text=response_text,
        query_response_time=response_time,
        conversation_status=conversation["status"]
    )


@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    
    conversation = container.read_item(item=conversation_id, partition_key=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_status": conversation["status"],
        "conversation_messages": conversation["transcript"],
        "use_case_outputs": conversation["output"][0]
    }



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

            # Update the conversation with the new call_id
            conversation['call_id'] = call_response.call_detail.call_id

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




# This function should be inside or accessible by your llm_with_function_calling.py logic
def update_conversation_answers(call_id, transcript, output):
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

    conversation_item['transcript'] = transcript
    conversation_item['output'] = [output]
    conversation_item['status'] = 'closed'
    # if 'answers' in conversation_item:
    #     conversation_item['answers'] += f"{answers}"  # Append new answers
    # else:
    #     conversation_item['answers'] = answers  # Initialize if not present

    # Upsert the updated item back into the database
    try:
        container.upsert_item(conversation_item)
        
        return True
    except Exception as e:
        print(f"Failed to update conversation: {e}")
        return False



def conversation_query(fetched_variables, transcript, query):
    try:
        prompt = f"""Given the output variables from a call and the transcript of the call, provide a comprehensive response to the query. Use the following information:

                    1. **Output Variables:** {fetched_variables}

                    2. **Call Transcript:** {transcript}

                    3. **Query:** {query}

                    **Your Task:**
                    Analyze the provided output variables and call transcript to answer the query comprehensively and accurately. Ensure that your response incorporates all relevant details from the output variables and aligns with the context given in the call transcript.
                """
        
        res = clientAzure.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=False,
        )
        response_content = res.choices[0].message.content
        return response_content
    except Exception as e:
        print("Error in Generating Response for Conversation Query:", e)



def get_output_variables(fetched_variables, transcript):
    try:
        allowed_variables = ["member_has_account", "plan_type", "benefit_period_type", "benefit_period_start_date",
                "benefit_period_end_date", "plan_is_active", "future_termination_date", "provider_in_network",
                "deductible", "copay", "co_insurance", "needs_pcp_referral", "has_add_on_dental_benefit", 
                "is_insurance_primary", "is_prior_authorisation_required", "is_preexisting_conditions_covered",
                "has_carved_out_dental_benefit", "carved_out_dental_benefit_name", "carved_out_dental_benefit_phone_no",
                "has_pbm", "pbm_name", "pbm_phone_no", "separate_benefit_dept_phone_no", "separate_preauth_dept_phone_no",
                "requires_member_followup"]

        prompt = f"""Using the provided dictionary of variables and the transcript of a call, extract and return the values for the predefined list of allowed variables in a valid JSON format. If a value for an allowed variable can be found in the provided data or inferred from the call transcript, include it in the output. If no value can be found, omit that variable from the output. The response must be a valid JSON only, formatted as:
                    {{
                    "variable_name": "variable_value",
                    "variable_name": "variable_value"
                    }}

                    The allowed variables are:
                    {allowed_variables}

                    Provided data includes:
                    Variables: {fetched_variables}

                    Transcript:
                    {transcript}

                    Response in JSON:
                """
        res = clientAzure.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=False,
        )
        response_content = res.choices[0].message.content
        return json.loads(response_content)
    except Exception as e:
        print("Error in Generating Output Variables:", e)
        return {"error": "An internal error occured in output generation"}

    

@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    await websocket.accept()

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
    llm_client.session['history'].append({"role": "caller", "message": first_event['content'], "time": datetime.datetime.now()})

    async def stream_response(request):
        nonlocal response_id
        res = ""
        for event in llm_client.draft_response(request, call_id):
            await websocket.send_text(json.dumps(event))
            res += event['content']
            if request['response_id'] < response_id:
                return # new response needed, abondon this one
        if res != "":
            llm_client.session['history'].append({"role": "caller", "message": res, "time": datetime.datetime.now()})

    try:
        while True:
            message = await websocket.receive_text()
            request = json.loads(message)
            
            if 'response_id' not in request:
                continue # no response needed, process live transcript update if needed
            response_id = request['response_id']
            await stream_response(request)
           



    except WebSocketDisconnect:
        print(f"LLM WebSocket disconnected for {call_id}")
    except Exception as e:
        print(f'LLM WebSocket error for {call_id}: {e}')
    finally:
        transcript = []
        for utterance in request['transcript']:
            if utterance["role"] == "agent":
                # print(f"Agent:- {utterance['content']}")
                transcript.append(f"Agent:- {utterance['content']}")
            else:
                # print(f"Provider:- {utterance['content']}")
                transcript.append(f"Provider:- {utterance['content']}")
        output_variables = get_output_variables(llm_client.output, transcript)
        allowed_variables = ["error", "member_has_account", "plan_type", "benefit_period_type", "benefit_period_start_date", "benefit_period_end_date", "plan_is_active", "future_termination_date", "provider_in_network", "deductible", "copay", "co_insurance", "needs_pcp_referral", "has_add_on_dental_benefit", "is_insurance_primary", "is_prior_authorisation_required", "is_preexisting_conditions_covered", "has_carvedout_dental_benefit", "carved_out_dental_benefit_name", "carved_out_dental_benefit_phone_no", "has_pbm", "pbm_name", "pbm_phone_no", "separate_benefit_dept_phone_no", "separate_preauth_dept_phone_no", "requires_member_followup"]
        output = {}
        for variable in output_variables:
            if variable in allowed_variables:
                output[variable] = output_variables[variable]
        update_conversation_answers(call_id, transcript, output)
        print(f"LLM WebSocket connection closed for {call_id}")
