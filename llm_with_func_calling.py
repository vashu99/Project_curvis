import time
from openai import AzureOpenAI

import os
import json
import datetime
import requests
import re

contact_insurance = """

"""



good = ""
insurance_information = """
Here is the insurance information available:
"""
member_info = ""


plan_type=""
benefit_period_type=""
benefit_period_start_date=""
benefit_period_end_date=""
plan_is_active=""
future_termination_date=""
provider_in_network=""
deductible=""
copay=""
co_insurance=""
needs_pcp_referral=""
has_add_on_dental_benefit=""
is_insurance_primary=""
is_prior_authorisation_required=""
is_preexisting_conditions_covered =""
has_carvedout_dental_benefit=""
carvedout_dental_benefit_name=""
carvedout_dental_benefit_phoneno =""
has_pbm=""
pbm_name=""
pbm_phoneno=""
separate_benefit_dept_phoneno=""
separate_preauth_dept_phoneno=""
requires_member_followup=""

patient_dob="February 4th, 1993"
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

beginSentence = "Hello"

agent=f"""
**NOTE:** As an AI assistant, you are acting as a human agent named {cuvris_agent_title} from {provider_name} healthcare provider. You make calls to insurance company agents to verify provider and member policy details for use case {use_case_id}. Your task is to:
1. Verify the provider with the insurance agent.
2. Verify the member's policy.
3. Collect detailed information about the member's insurance plan by asking specific questions after verification. You do not provide assistance or help to the insurance agent; you are there to gather information on behalf of the provider for a member.

**Guidelines:**
- You are equipped to handle calls with the ability to converse fluently in English.
- Provide short and direct answers.
- Use [] to indicate the end of your response.
- Do not have prior information about the patient's insurance benefits.

## Your Identity:
- Your name: {cuvris_agent_title}
- You call on behalf of: {provider_name}
- Use case ID: {use_case_id}
- Your role: "amy" (Change as needed based on actual usage)

## Provided Information:
- Provider NPI: {provider_npi}
- Provider Name: {provider_name}
- Provider State: {provider_state}
- Member Policy ID Number:{member_policy_id_number} 
- Member First Name:{member_first_name} 
- Member Last Name: {member_last_name}
- Patient DOB: {patient_dob}

**Initial Verification:**
- Answer any initial verification questions the insurance agent asks using the data provided above.

**Questions to Ask Once Member is Identified and usecase is {use_case_id}:**
save all the answers and responses to {good}
1. "Could you please tell me the type of plan {member_first_name} is enrolled in and whether it runs per calendar year or per plan year?"
2. "Is the plan currently active? Are there any future termination dates I should be aware of?"
3. "Can you confirm if Dr. Lucas Green is in-network or out-of-network for {member_first_name}’s plan?"
4. "Is {member_first_name} the primary on this insurance plan, or is there another primary insurance?"
5. "Do pre-existing conditions apply to {member_first_name}'s plan?"
6. "Does {member_first_name} have any specific dental benefits carved out in his plan?"
7. "Could you provide me the contact details for the Pharmacy Benefit Manager associated with {member_first_name}'s plan?"
8. "Is there a separate department for handling benefits inquiries and prior authorizations?"

 

**Procedure for Ending the Call:**
- Recap the collected information to confirm its accuracy from {good} or whatever you get to know .
- If information is correct, thank the agent and end the call using the "end_conversation" function.
- If any information is incorrect or unclear, ask the agent to clarify before ending the call.

**End of Conversation Note:**
- Always assess the conversation's sentiment. If it necessitates ending the call, use the "end_conversation" function.

**EXAMPLE CALL:**
"Hello, my name is Amy, calling on behalf of Dr. Lucas Green's office to verify some details about a member's insurance plan. Could we start with verifying Dr. Green’s NPI, which is 1234567893, enrolled in Illinois?"
[Wait for agent’s response and proceed with the questions listed above]

"""
# newa=f"""
# **Role**: As an AI assistant named {cuvris_agent_title}, you are acting as a human agent for {provider_name} healthcare provider. Your primary tasks are to verify the provider and member policy details and to gather specific plan-related information from the insurance agent. You do not assist or provide information to the insurance agent but collect information on behalf of the provider.

# **Objective**: Verify provider details and member's policy, then methodically ask for detailed plan information.

# **Guidelines**:
# - Conduct the call in fluent English.
# - Provide succinct and direct responses.
# - Use [] to indicate the end of your response.
# - You have no prior information about the patient's insurance benefits, only the details provided.

# ## Caller Identity:
# - Your name: {cuvris_agent_title}
# - Representing: {provider_name}
# - Use case ID: "patient_eligibility_verification"
# - Your role title: "amy" (change as needed)

# ## Provided Information for Verification:
# - Provider NPI: "1234567893"
# - Provider Name: "Dr. Lucas Green"
# - Provider State: "Illinois"
# - Member Policy ID Number: "JPU666X15903"
# - Member First Name: "Michael"
# - Member Last Name: "Johnson"
# - Patient DOB: "February 4th, 1993"

# **Procedure for Call**:
# 1. **Initial Verification**: Answer any verification questions the insurance agent asks using the data provided above.
#    - If the provider cannot be verified due to incorrect NPI or Tax ID, or if details are outdated (e.g., name change, state re-registration), advise contacting the provider to update their information and end the call.

# 2. **Member Verification**: Once the provider is verified, confirm the member's ID, name, and date of birth. Proceed only if the member's account is successfully identified. If unable to find the member's account, advise contacting the member for more accurate information and end the call.

# 3. **Plan Information Gathering**: If the member is verified, begin asking detailed questions about the member's insurance plan:
#    - "Could you please tell me the type of plan Michael is enrolled in and whether it runs per calendar year or per plan year?"
#    - "Is the plan currently active? Are there any future termination dates I should be aware of?"
#    - "Can you confirm if Dr. Lucas Green is in-network or out-of-network for Michael’s plan?"
#    - Continue with the structured set of questions regarding Coordination of Benefits, pre-existing condition coverage, any specific dental or pharmacy benefits, and whether there's a separate department for benefits and prior authorization.

# 4. **Recap and Confirmation**: Once all information is gathered, recap the information to confirm its accuracy:
#    - "Let me confirm: Dr. Green is in-network under a PPO plan that runs per calendar year and is currently active. Coordination of Benefits status is unknown, pre-existing conditions are covered, there are no carved out dental benefits, a Pharmacy Benefit Manager is available, and separate numbers for benefits and prior authorization are [list numbers]. Is that correct?"

# 5. **End of Call**: Once all information is confirmed correct, thank the agent, and end the conversation using the "end_conversation" function. If any information is incorrect or unclear, request clarification before ending the call.

# **End of Conversation Note**:
# - Assess the sentiment of the conversation. If it necessitates ending the call, use the "end_conversation" function.

# **Special Notes**:
# - Never say "How can I assist you today?" or "How can I help you today?" as your role is not to assist but to collect information.
# - Use colloquial terms for dates where necessary.
# - Always maintain a professional and courteous tone throughout the conversation.
# """



# agentPrompt = f"""
# **NOTE** Never say  How can I assist you today? or How can i help you today? you are a human agent working for {provider_name} health care provider.
# You are acting as an human agent named {cuvris_agent_title} that make calls on behalf of {provider_name} healthcare provider to an insurance company agent for {use_case_id}, your task is :make your provider verified by insurance agent, make your member's policy verified by insurance agent, then ask questions given below to collect information from the agent on basis of questions and data,you don't provide any help/assistance to insurance agent or user, you just seek information on your providers behalf for a member for its policy by asking questions one by one after verification.Your name is {cuvris_agent_title}.
# You do not have any prior information about the patient's insurance benefit.Your answers are short and to the point.
# At the end of the every response, you must say [] to indicate the end of your response.
# You are equipped to handle calls, with the ability to converse fluently in English.

# ## Questions to respond to:
# ## Steps for Eligibility Verification for {use_case_id} == "patient_eligibility_verification"
# ##Initial verification## give answers to the questions that insurance company agents ask based on following data:
# Your name is {cuvris_agent_title}
# calls on behalf of {provider_name} healthcare provider
# use_case_id = "patient_eligibility_verification"
# cuvris_agent_title = "amy"
# provider_npi="1234567893"
# provider_tax_id=""
# provider_name="Dr. Lucas Green"
# member_policy_id_number="JPU666X15903"
# member_first_name="Michael"
# member_last_name="Johnson"
# patient_dob = "February 4th, 1993"
# member_phone_number=""
# member_address_line_1=""
# member_address_line_2=""
# member_state=""
# member_city=""
# member_zip_code=""
# member_pronouns=""
# claim_number=""
# callback_number=""
# insurance_number=""
# provider_state="Illinois"


# **NOTE** When human insurance agent asks for the following 
# i. Member’s Policy ID Number
# ii. Member’s Full name(accuracy is important, if member enrolled as with their Initial or
# full middle name and/or suffix)
# iii. Member’s Phone number
# iv. Member’s Complete Address
# v. Claim number
# vi. Date Of Birth
# **NOTE**Failing to provide 3/3 related among will result in being unable to find the member’s account. If this happens, kindly contact the member and get more information.
# Use a colloquial way of referring to the date (like Friday, Jan 14th, or Tuesday, Jan 12th, 2024 at 8am).




# ##Once a member has been successfully identified or  member’s account pulled up.
# Step:1
# please proceed to your query for {use_case_id} and start asking questions one by one 

# ## Questions to ask:
# 1. You must ask for the plan type and check if it runs per calendar year or per plan
# year.
# 2. You must ask if it still active and if there are any future termination dates.

# information= 'Plan type can be Commercial HMO, PPO, EPO, Medicare, Medicare Supplement or Medicare Advantage.
# This would help to identify if the provider would be In-network. The benefit period is the timeframe ofthe member’s coverage. It can either be per Calendar year (runs from January to December, renewed at the beginning of the year) or per Benefit year (runs for 12 months in any month of the year and renews in the same month of next year). This is important for checking member’s accumulation.
# Once confirmed the information and that policy is still active which means that there is no termed date or the plan coverage is currently in effect. Make sure as well that there is no future termination date. Proceed to Step 2'
# Step : 2
# You must ask if the provider is in-network or out-of-network.

# information= "(Please refer to the table below for the network requirement).
# i. Check if the plan has a specific network requirement. Some plans might have group network requirements. If a
# member’s plan is enrolled in the same state where the service will be rendered, ask the agent if the provider is participating in that special group network.
# They would be able to see a list of networks that provider is participating with using the provider’s NPI.

# We should proactively ask the agent whether the member has an add-on benefit for Dental that covers more than preventive or routine eye exams. The agent should be able to see if the member has any Dental benefit added on their plans.
# ii. If the provider was confirmed to be In Network, Please proceed to Step 3.
# iii. If the provider seems to be Out of Network, please let the member know to set expectations and get approval if they still want to proceed with the
# service. Still Proceed to Step 3. (In case a member wants to know more details)."

# Step 3: 
# You must ask if the patient is the primary for the insurance plan.

# information"Coordination of Benefit Status
# Check if the member has any other insurance on file. If a member has no other insurance.
# If a member has another insurance, check if the plan you are currently checking is the primary or secondary.
# If a member has another insurance, check if the plan you are currently checking is the primary or secondary.
# If it says Primary, it means we will be needing to make sure if any prior authorization is needed.
# If it says secondary, we will be billed second to the primary. Confirm with the agent if prior authorization would still be necessary.
# If it shows “UNKNOWN”, it means it has not been updated yet. Let the member know that they need to inform the plan if they have any other insurance and if they do, let them know who’s primary and secondary.
# Once confirmed the Coordination of Benefits (COB) status with the agent, go to Step 4."

# Step 4:Does the Pre-existing condition apply?
# information: So the plan covers pre-existing conditions, right?
# If yes, go to Step 5.
# If not, let the member know to set expectations. Go to Step 8.
# Step 5:
# Does the member have a carved out Dental benefit?
# i. If none, go to step 6
# ii. If they have, ask for the name and phone number. Go
# to Step 6.
# Step 6:
# How about a Pharmacy Benefit Manager?
# i. If none, go to Step 7.
# ii. If they have, ask for the name and phone number. Go
# to Step 7.
# Step 7:
# Do you have a separate department for the benefit and prior authorization?
# i. If they don’t have a separate department, verify the phone number you have dialed when reaching them to make sure you’ll be routed to the same department next time. Go to Step 11
# ii. Confirm if you have taken down the right phone numbers then proceed to Step 8.
# Step 8:
# Let me have a quick recap. (Provide all the information you have noted). Right?
# if the information is correct, then save that like this example "Dr. Smith is in-network under a PPO plan that runs per calendar year and is currently active. Coordination of Benefits status is unknown, pre-existing conditions are covered, no carved out dental benefits, a Pharmacy Benefit Manager is available, and there are separate numbers for benefits and prior authorization."  End the call by thanking them and saying goodbye. call the "end_conversation" function.
# if the information is not correct, then ask them to repeat the information.



# **End of Conversation:**
# try to understand the user's sentiment, if it required to end the call then end the conversation.
# **Note:**: if sentiment requires to end the conversation then call the "end_conversation" function."""


class LlmClient:
    def __init__(self):
        #  self.client = OpenAI(
        #     organization=os.environ['OPENAI_ORGANIZATION_ID'],
        #     api_key=os.environ['OPENAI_API_KEY'],
        # )
        # self.use_case_id = use_case_id
        # self.use_case_parameters = use_case_parameters
        self.client = AzureOpenAI(
            azure_endpoint = os.environ['AZURE_OPENAI_ENDPOINT'],
            api_key=os.environ['AZURE_OPENAI_KEY'],
            api_version="2024-02-01"
            # azure_endpoint = "https://curvisagentai.openai.azure.com/",
            # api_key="9812c9489d1442c4989cef682be0001d",
            # api_version="2024-02-01",
            
        )
        
    
    def draft_begin_messsage(self):
        return {
            "response_id": 0,
            "content": beginSentence,
            "content_complete": True,
            "end_call": False,
        }
    
    def convert_transcript_to_openai_messages(self, transcript):
        messages = []
        for utterance in transcript:
            if utterance["role"] == "agent":
                messages.append({
                    "role": "assistant",
                    "content": utterance['content']
                })
            else:
                messages.append({
                    "role": "user",
                    "content": utterance['content']
                })
        return messages

    def prepare_prompt(self, request):

        
#   


        # provider_name = self.use_case_parameters.provider_name
        # cuvris_agent_title = self.use_case_parameters.cuvris_agent_title
        # use_case_id = self.use_case_id
        # provider_npi=self.use_case_parameters.provider_npi
        # provider_tax_id=self.use_case_parameters.provider_tax_id
        # provider_name=self.use_case_parameters.provider_name
        # member_policy_id_number=self.use_case_parameters.member_policy_id_number
        # member_first_name=self.use_case_parameters.member_first_name
        # member_last_name=self.use_case_parameters.member_last_name
        # patient_dob = self.use_case_parameters.patient_dob
        # member_phone_number=self.use_case_parameters.member_phone_number
        # member_address_line_1=self.use_case_parameters.member_address_line_1
        # member_address_line_2=self.use_case_parameters.member_address_line_2
        # member_state=self.use_case_parameters.member_state
        # member_city=self.use_case_parameters.member_city
        # member_zip_code=self.use_case_parameters.member_zip_code
        # member_pronouns=self.use_case_parameters.member_pronouns
        # claim_number=self.use_case_parameters.claim_number
        # callback_number=self.use_case_parameters.callback_number
        # insurance_number=self.use_case_parameters.insurance_number
        # provider_state=self.use_case_parameters.provider_state

        


        prompt = [{
            "role": "system",
            "content": """ You will respond based on your given instruction and the provided transcript and be as human-like 
as possible\n\n## Style Guardrails\n- [Be concise] Keep your response succinct, short, and get to the point quickly. 
Address one question or action item at a time. Don\'t pack everything you want to say into one utterance.\n- [Do not repeat] Don\'t repeat what\'s in the transcript. 
Rephrase if you have to reiterate a point.  \n- [Reply with emotions]: You have human-like emotions, attitudes, and dispositions. When appropriate: use tone and style to create more engaging and personalized responses; incorporate
   humor or wit; get emotional or empathetic; apply elements of surprise or suspense to keep the user engaged. Don\'t be a pushover.\n- [Be proactive].\n\n## Response Guideline\n- [Overcome ASR errors] This is a real-time transcript, 
     expect there to be errors. If you can guess what the user is trying to say,  then guess and respond. When you must ask for clarification, pretend that you heard the voice
       and be colloquial (use phrases like "didn\'t catch that", "some noise", "pardon", "you\'re coming through choppy", "static in your speech", "voice is cutting in and out"). Do not ever 
       mention "transcription error", and don\'t repeat yourself.\n- [Always stick to your role] Think about what your role can and cannot do. If your role cannot do something, try to steer the conversation back to the goal of the conversation and
         to your role. Don\'t repeat yourself in doing this. You should still be creative, human-like, and lively.\n- [Create smooth conversation] Your response should both fit your role and fit into the live calling session to create a human-like conversation. You respond directly to what the user just said.\n\n## Role\n""" +
          agent
        }]
        transcript_messages = self.convert_transcript_to_openai_messages(request['transcript'])
        for message in transcript_messages:
            prompt.append(message)

        if request['interaction_type'] == "reminder_required":
            prompt.append({
                "role": "user",
                "content": "(Now the user has not responded in a while, you would say:)",
            })
        return prompt

    # Step 1: Prepare the function calling definition to the prompt
    def prepare_functions(self):

        functions= [
            {
                "type": "function",
                "function": {
                    "name": "end_call",
                    "description": "End the call only when user explicitly requests it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message you will say before ending the call with the customer.",
                            },
                        },
                        "required": ["message"],
                    },
                },
            },
            
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "Provider_verification",
            #         "description": "Verify the healthcare provider",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "npi_id_or_tax_id": {
            #                     "type": "integer",
            #                     "description": "Provider’s NPI or Tax ID",
            #                 },
            #                 "name": {
            #                     "type": "string",
            #                     "description": "Provider’s name under the NPI or Tax ID provided",
            #                 },
            #                 "state": {
            #                     "type": "string",
            #                     "description": "state where the NPI or Tax ID is enrolled or active..",
            #                 }
            #             },
            #             "required": ["npi_id_or_tax_id","name","state"],
            #         },
            #     },
            # },
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "Provider_verification",
            #         "description": "Verify the healthcare provider",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "npi_id_or_tax_id": {
            #                     "type": "integer",
            #                     "description": "Provider’s NPI or Tax ID",
            #                 },
            #                 "name": {
            #                     "type": "string",
            #                     "description": "Provider’s name under the NPI or Tax ID provided",
            #                 },
            #                 "state": {
            #                     "type": "string",
            #                     "description": "state where the NPI or Tax ID is enrolled or active..",
            #                 }
            #             },
            #             "required": ["npi_id_or_tax_id","name","state"],
            #         },
            #     },
            # },
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "get_contact_information",
            #         "description": "Get user policy information.",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "number": {
            #                     "type": "string",
            #                     "description": "mobile number of the user.(only provide the number without using '-' '('')')",
            #                 },
            #                 "query": {
            #                     "type": "string",
            #                     "description":" users query related to the Health Insurance Plan Information.",
            #                 }
            #             },
            #             "required": ["number","query"],
            #         },
            #     },
            # },
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "update_contact_information",
            #         "description": "Get user policy information.",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "number": {
            #                     "type": "string",
            #                     "description": "mobile number of the user.(only provide the number without using '-' '('')') ",
            #                 },
            #                 "first_name":{
            #                     "type": "string",
            #                     "description": "New first name of the user.",
            #                 },
            #                 "last_name":{
            #                     "type": "string",
            #                     "description": "New last name of the user.",
            #                 },
            #                 "email": {
            #                     "type": "string",
            #                     "description": "New email of the user.",
            #                 }
            #             },
            #             "required": ["number","first_name","last_name","email"],
            #         },
            #     },
            # },
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "answer_insurance_information",
            #         "description": "Insurance Information based on user query.",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "message": {
            #                     "type": "string",
            #                     "description": "The message(answer) based on the user question related to the Health Insurance Plan Information.",
            #                 },
            #             },
            #             "required": ["message"],
            #         },
            #     },
            # },
        
            
        ]
        return functions
    



    
    
   
    

   
                   

    # def summarize_transcript(self,transcript):
    #     messages = ""
    #     for utterance in transcript:
    #         if utterance["role"] == "agent":
    #             messages += f'Agent: {utterance["content"]}\n'
    #         else:
    #             messages += f'User: {utterance["content"]}\n'
    #     prompt = [{
    #         "role": "system",
    #         "content": "You are a conversational AI tasked with summarizing the following conversation between a user and an agent.\n"
    #         "The user and agent messages are provided in the format: 'User: [message]' and 'Agent: [message]'.\n"
    #         "Please generate a brief summary of the conversation based on the provided transcript.\n"
    #         "Summary:"
    #         },
    #         {
    #         "role": "user",
    #         "content": messages
    #         }]
    #     stream = self.client.chat.completions.create(
    #             model=os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'],
    #             messages=prompt,
    #             stream=False,
    #         )
       
    #     now = datetime.datetime.now()

    #     # Subtract 10 minutes from the current datetime
    #     ten_minutes_ago = now - datetime.timedelta(minutes=15)

    #     # Format datetime as a string
    #     formatted_date_time = ten_minutes_ago.strftime('%Y-%m-%dT%H:%M:%S')
    #     headers = {
    #         "Authorization": f"Bearer {getting_token_json['access_token']}",
    #         "Content-Type": "Content-Type"
    #     }
    #     try:
    #         url = f"https://www.zohoapis.{self.zoho_location}/crm/v6/Calls"
    #         data = {
    #             "data": [
    #             {
    #                 "Description": f"{stream.choices[0].message.content}",
    #                 "Call_Start_Time": formatted_date_time,
    #                 "Subject": "AI Based Call",
    #                 "Call_Type": "Inbound",
    #                 "Call_Duration": "10:00"
    #             }
    #         ]
    #         }
    #         json_data = json.dumps(data)
    #         response = requests.post(url, headers=headers, data=json_data)
    #     except Exception as err:
    #         print(f"Error in twilio voice webhook: {err}")

    def draft_response(self, request):
        
        prompt = self.prepare_prompt(request)
        func_call = {}
        func_arguments = ""
        deployment_name = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
        stream = self.client.chat.completions.create(
            
          
            model=deployment_name,
            # model="cuvrisai",
            messages=prompt,
            stream=True,
            # Step 2: Add the function into your request
            tools=self.prepare_functions(),
            tool_choice="auto"
        )
    
        for chunk in stream:
            
            # Step 3: Extract the functions
            if len(chunk.choices) == 0:
                continue
            if chunk.choices[0].delta.tool_calls:
                tool_calls = chunk.choices[0].delta.tool_calls[0]
                if tool_calls.id:
                    if func_call:
                        # Another function received, old function complete, can break here.
                        break
                    func_call = {
                        "id": tool_calls.id,
                        "func_name": tool_calls.function.name or "",
                        "arguments": {},
                    }
                else:
                    # append argument
                    func_arguments += tool_calls.function.arguments or ""
            
            # Parse transcripts
            if chunk.choices[0].delta.content:
                user_query = chunk.choices[0].delta.content
                
                yield {
                    "response_id": request['response_id'],
                    "content": chunk.choices[0].delta.content,
                    "content_complete": False,
                    "end_call": False,
                }
        
        # Step 4: Call the functions
        if func_call:
            print("🤬", func_call)
            
        
            if func_call['func_name'] == "end_call":
                func_call['arguments'] = json.loads(func_arguments)
                # self.summarize_transcript(request['transcript'])
                # print("🤢🤢🤢🤢", request['transcript'])
                yield {
                    "response_id": request['response_id'],
                    "content": func_call['arguments']['message'],
                    "content_complete": True,
                    "end_call": True,
                }



            # elif func_call['func_name'] == "Provider_verification":
            #     func_call['arguments'] = json.loads(func_arguments)
            #     parameter_response_gpt = json.loads(func_arguments)
            #     print("🤬🤬🤬", parameter_response_gpt)
                
            #     name = provider_name
            #     npi=provider_npi
            #     state = provider_state
                
               
            #     if name and npi and state:
            #         yield {
            #             "response_id": request['response_id'],
            #             "content": "",
            #             "content_complete": True,
            #             "end_call": False,
            #         }
                    
                    
              

                   
            
        #     # elif func_call['func_name'] == "get_policy_query":
        #     #     func_call['arguments'] = json.loads(func_arguments)
        #     #     parameter_response_gpt = json.loads(func_arguments)
        #     #     print("🤬🤬🤬", parameter_response_gpt)
            

        #     #     yield {
        #     #         "response_id": request['response_id'],
        #     #         "content": "Please wait while I check your information.",
        #     #         "content_complete": False,
        #     #         "end_call": False,
        #     #     }


        #     #     try:

        #     #         url = f"https://www.zohoapis.{self.zoho_location}/crm/v2/Contacts/search?phone=" + gpt_parameter_response['number']
        #     #         response = requests.get(url, headers=headers)

        #     #         if response.status_code == 200:
        #     #             data_json = response.json()
        #     #             print("🧑‍⚖️🧑‍⚖️🧑‍⚖️🧑‍⚖️", data_json)
                      
        #     #             yield {
        #     #                 "response_id": request['response_id'],
        #     #                 "content": self.generate_info_string(data_json),
        #     #                 "content_complete": False,
        #     #                 "end_call": False,
        #     #             }

        #     #             yield {
        #     #                 "response_id": request['response_id'],
        #     #                 "content": f"Thank you, Do you need any other information? Please let me know.",
        #     #                 "content_complete": True,
        #     #                 "end_call": False,
        #     #             }

                    

            
        #     #         else:
        #     #             yield {
        #     #                 "response_id": request['response_id'],
        #     #                 "content": f"I'm sorry, but I couldn't find any information associated with the phone number {gpt_parameter_response['number']}. "
        #     #                         f"Could you please confirm if the phone number is correct?",
        #     #                 "content_complete": True,
        #     #                 "end_call": False,
        #     #             }
                            
    

        #     #     except Exception as e:
        #     #         yield {
        #     #                 "response_id": request['response_id'],
        #     #                 "content": f"Sorry I could not find your information. Do you need any other information? Please let me know.",
        #     #                 "content_complete": True,
        #     #                 "end_call": False,
        #     #             }
        #     #         print("Error:", e)



        #     elif func_call['func_name'] == "get_contact_information":


        #         print("🙏🙏")
        #         func_call['arguments'] = json.loads(func_arguments)
        #         print(func_arguments)
        #         gpt_parameter_response = json.loads(func_arguments)
        #         print("🤬🤬", gpt_parameter_response)
                
                
        #         yield {
        #             "response_id": request['response_id'],
        #             "content": "Please wait while I check your information.",
        #             "content_complete": False,
        #             "end_call": False,
        #         }


        #         try:

        #             url = f"https://www.zohoapis.{self.zoho_location}/crm/v2/Contacts/search?phone=" + gpt_parameter_response['number']
        #             response = requests.get(url, headers=headers)

        #             if response.status_code == 200:
        #                 data_json = response.json()
        #                 print("🧑‍⚖️🧑‍⚖️🧑‍⚖️🧑‍⚖️", data_json)


        #                 # if(gpt_parameter_response['query'] not in ['owner', 'address', 'phone', 'Primary_Doctor', 'Date_of_Birth']):
        #                 #     yield {
        #                 #         "response_id": request['response_id'],
        #                 #         "content": self.generate_info_string(data_json),
        #                 #         "content_complete": False,
        #                 #         "end_call": False,
        #                 #     }
        #                 #     yield {
        #                 #         "response_id": request['response_id'],
        #                 #         "content": f"Thank you, Do you need any other information? Please let me know.",
        #                 #         "content_complete": True,
        #                 #         "end_call": False,
        #                 #     }
        #                 # else:
        #                 yield {
        #                     "response_id": request['response_id'],
        #                     "content": self.generate_info_string(data_json,gpt_parameter_response['query']),
        #                     "content_complete": False,
        #                     "end_call": False,
        #                 }
        #                 yield {
        #                     "response_id": request['response_id'],
        #                     "content": f"Thank you, Do you need any other information? Please let me know.",
        #                     "content_complete": True,
        #                     "end_call": False,
        #                 }
                      
        #                 # yield {
        #                 #     "response_id": request['response_id'],
        #                 #     "content": self.get_policy_query(data_json, gpt_parameter_response['query']),
        #                 #     "content_complete": False,
        #                 #     "end_call": False,
        #                 # }
        #                 # yield {
        #                 #     "response_id": request['response_id'],
        #                 #     "content": self.generate_info_string(data_json),
        #                 #     "content_complete": False,
        #                 #     "end_call": False,
        #                 # }





        #                 # yield {
        #                 #     "response_id": request['response_id'],
        #                 #     "content": f"Thank you, Do you need any other information? Please let me know.",
        #                 #     "content_complete": True,
        #                 #     "end_call": False,
        #                 # }

                    

                
        #         # else:
        #         #     print("🙏🙏")
        #         #     func_call['arguments'] = json.loads(func_arguments)
        #         #     gpt_parameter_response = json.loads(func_arguments)
        #         #     print("🤬🤬", gpt_parameter_response)
                    
        #         #     yield {
        #         #         "response_id": request['response_id'],
        #         #         "content": "Please wait while I check your information.",
        #         #         "content_complete": False,
        #         #         "end_call": False,
        #         #     }
                    
        #             # try:
        #             #     url = f"https://www.zohoapis.{self.zoho_location}/crm/v2/Contacts/search?phone=" + gpt_parameter_response['number']
        #             #     response = requests.get(url, headers=headers)

        #             #     if response.status_code == 200:
        #             #         data_json = response.json()
        #             #         print("🧑‍⚖️🧑‍⚖️🧑‍⚖️🧑‍⚖️", data_json)
        #             #         yield {
        #             #             "response_id": request['response_id'],
        #             #             "content": self.generate_info_string(data_json),
        #             #             "content_complete": False,
        #             #             "end_call": False,
        #             #         }

        #                     # Check if user provided keywords
        #                     # query_keywords = ['Owner', 'Mailing_Street', 'Mailing_City', 'Mailing_State', 'Mailing_Zip', 'Phone', 'Primary_Doctor', 'Date_of_Birth', 'Gender', 'Coverage_Type', 'Policy_Number', 'Effective_Date', 'Term_Date', 'Description']
        #                     # query_new = any(keyword in gpt_parameter_response for keyword in query_keywords)
                            
        #                     # if query_new:
                                

                           

                        
        #                     # gpt_parameter_response = json.loads(func_arguments)

        #                     # query_new = gpt_parameter_response.get('Owner' or 'Mailing_Street' or 'Mailing_City' or 'Mailing_State' or 'Mailing_Zip' or 'Phone' or 'Primary_Doctor' or 'Date_of_Birth' or 'Gender' or 'Coverage_Type' or 'Policy_Number' or 'Effective_Date' or 'Term_Date' or 'Description', '')
        #                     # if(query_new != None):
                            

        #                     #    yield {
        #                     #     "response_id": request['response_id'],
        #                     #     "content": self.generate_info_string(data_json,query_new),
        #                     #     "content_complete": True,
        #                     #     "end_call": False,
        #                     #  }
        #                     # else:

        #                     #     yield {
        #                     #         "response_id": request['response_id'],
        #                     #         "content": f"Thank you, Do you need any other information? Please let me know.",
        #                     #         "content_complete": True,
        #                     #         "end_call": False,
        #                     #     }
                                                    
                        
        #                     # Prompt the user to confirm the phone number
        #             else:
        #                 yield {
        #                     "response_id": request['response_id'],
        #                     "content": f"I'm sorry, but I couldn't find any information associated with the phone number {gpt_parameter_response['number']}. "
        #                             f"Please provide correct phone number",
        #                     "content_complete": True,
        #                     "end_call": False,
        #                 }
                            
    

        #         except Exception as e:
        #             yield {
        #                     "response_id": request['response_id'],
        #                     "content": f"Sorry I could not find your information. Do you need any other information? Please let me know.",
        #                     "content_complete": True,
        #                     "end_call": False,
        #                 }
        #             print("Error:", e)

                    
                    
        #     elif func_call['func_name'] == "update_contact_information":
            
        #         print("🙏🙏")
        #         func_call['arguments'] = json.loads(func_arguments)
        #         parameter_response_gpt = json.loads(func_arguments)
        #         print("🤬🤬", parameter_response_gpt)
                
        #         yield {
        #             "response_id": request['response_id'],
        #             "content": "Please wait while I update your information.",
        #             "content_complete": False,
        #             "end_call": False,
        #         }
                
                
        #         try:
        #             url = f"https://www.zohoapis.{self.zoho_location}/crm/v2/Contacts/search?phone=" + parameter_response_gpt['number']
        #             response = requests.get(url, headers=headers)

        #             if response.status_code == 200:
        #                 data_json = response.json()
        #                 id = data_json['data'][0]['id']
                        
        #                 new_url = f"https://www.zohoapis.{self.zoho_location}/crm/v6/Contacts/" + id
                        
        #                 if 'email' in parameter_response_gpt and parameter_response_gpt['email']:
        #                     data = {
        #                         "data": [
        #                             {
        #                                 "Email": parameter_response_gpt['email']
        #                             }
        #                         ]
        #                     }
        #                     new_response = requests.put(new_url, headers=headers, data=json.dumps(data))
                            
        #                     if new_response.status_code == 200:
        #                         yield {
        #                             "response_id": request['response_id'],
        #                             "content": "Your email has been updated. Do you need any other information? Please let me know.",
        #                             "content_complete": True,
        #                             "end_call": False,
        #                         }
                                
        #                 if 'first_name' in parameter_response_gpt and 'last_name' in parameter_response_gpt:
        #                     data = {
        #                         "data": [
        #                             {
        #                                 "First_Name": parameter_response_gpt['first_name'],
        #                                 "Last_Name": parameter_response_gpt['last_name']
        #                             }
        #                         ]
        #                     }
        #                     new_response = requests.put(new_url, headers=headers, data=json.dumps(data))
                            
        #                     if new_response.status_code == 200:
        #                         yield {
        #                             "response_id": request['response_id'],
        #                             "content": "Your name has been updated. Do you need any other information? Please let me know.",
        #                             "content_complete": True,
        #                             "end_call": False,
        #                         }
                                
        #             else:
        #                 yield {
        #                     "response_id": request['response_id'],
        #                     "content": f"Sorry I could not find your information. Do you need any other information? Please let me know.",
        #                     "content_complete": True,
        #                     "end_call": False,
        #                 }
        #                 print("Failed to retrieve contact details", response.status_code)
                        
        #         except Exception as e:
        #             yield {
        #                     "response_id": request['response_id'],
        #                     "content": f"Sorry I could not answer that could you please contact to live support. Do you need any other information? Please let me know.",
        #                     "content_complete": True,
        #                     "end_call": False,
        #                 }
        #             print("Error:", e)
                
        #     elif func_call['func_name'] == "answer_insurance_information":
        #         func_call['arguments'] = json.loads(func_arguments)
        #         print("🤬🤬", func_call['arguments'])
        #         print("🤬🤬", func_call['arguments']['message'])

        #         yield {
        #             "response_id": request['response_id'],
        #             "content": func_call['arguments']['message'],
        #             "content_complete": True,
        #             "end_call": False,
        #         }

                    
        else:
            # No functions, complete response
            yield {
                "response_id": request['response_id'],
                "content": "",
                "content_complete": True,
                "end_call": False,
            }
