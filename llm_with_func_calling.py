import time
from openai import AzureOpenAI

import os
import json
import datetime
import requests
import re
from typing import Dict
from dotenv import load_dotenv
load_dotenv(override=True)

from azure.cosmos import CosmosClient, PartitionKey, exceptions


url = os.environ['ACCOUNT_HOST']
key = os.environ['ACCOUNT_KEY']
model_name = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
# key = os.environ['ACCOUNT_KEY']
client = CosmosClient(url, credential=key)
database_name = 'CuvrisDB'
container_name = 'Conversations'
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)




contact_insurance = """

"""



good  =""
info_for_member = ""
info_for_provider=""
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

# patient_dob="February 4th, 1993"
# use_case_id = "patient_benefit_verification"
# cuvris_agent_title = "amy"
# provider_npi="1234567893"
# provider_tax_id=""
# provider_name="Dr. Lucas Green"
# member_policy_id_number="JPU666X15903"
# self.use_case_parameters.member_first_name="Michael"
# member_last_name="Johnson"
# member_phone_number=""
# member_address_line_1 = ""
# member_address_line_2 = ""
# member_state=""
# member_city=""
# member_zip_code=""
# member_pronouns=""
# claim_number=""
# callback_number=""
# insurance_number=""
# provider_state="Illinois"

# is_insurance_primary="yes"
# plan_type="Dental PPO plan"
# benefit_period_type="per calendar year"
service_procedure_name="dental crown"
cpt_code="D2740"
icd_ten_diagnosis_code="K02.9"
is_preventive_or_routine=""


beginSentence = "Hello There"


class LlmClient:
    def __init__(self, use_case_id, use_case_parameters):
        self.use_case_id = use_case_id
        self.use_case_parameters = use_case_parameters
        self.answers = ""  # Initialize answers attribute
        self.session = {}
        self.session['history'] = []
        self.session['step'] = 1
        self.session['start_time'] = datetime.datetime.now()
        self.start = 0
        self.prompt = self.prepare_prompt()
        self.output = {}
        

        self.client = AzureOpenAI(
            azure_endpoint = os.environ['AZURE_OPENAI_ENDPOINT'],
            api_key=os.environ['AZURE_OPENAI_KEY'],
            api_version="2024-02-01"
            # azure_endpoint = "https://curvisagentai.openai.azure.com/",
            # api_key="9812c9489d1442c4989cef682be0001d",
            # api_version="2024-02-01",
            
        )
    
    def draft_begin_message(self):
        return {
            "response_id": 0,
            "content": beginSentence,
            "content_complete": True,
            "end_call": False,
        }
    
    def convert_transcript_to_openai_messages(self, transcript):
        messages = []
        for utterance in transcript:
            if utterance["role"] == "caller":
                messages.append({
                    "role": "assistant",
                    "content": utterance['message']
                })
            else:
                messages.append({
                    "role": "user",
                    "content": utterance['message']
                })
        return messages
            
    

    def prepare_prompt(self):
        
        

   


        agent=f"""
        **NOTE:** you are acting as a human agent named {self.use_case_parameters["cuvris_agent_title"]} from {self.use_case_parameters["provider_name"]} healthcare provider. You make calls to insurance company agents to verify provider and member policy details for use case {self.use_case_id}. You do not provide assistance or help to the insurance agent; you are there to gather information on behalf of the provider for a member. Your task is to:
        1. Verify your provider with the insurance agent.
        2. Verify the member's policy.
        3. Collect detailed information about the member's insurance plan by asking specific questions after verification for two different use case like patient_eligibility_verification or patient_benefit_verification .You do not provide assistance or help to the insurance agent; you are there to gather information on behalf of the provider for a member.

        **Guidelines:**
        - You are equipped to handle calls with the ability to converse fluently in English.
        - Provide short and direct answers.

        - Do not have prior information about the patient's insurance benefits.

        ## Your Identity:
        - Your name: {self.use_case_parameters["cuvris_agent_title"]}
        - You call on behalf of: {self.use_case_parameters["provider_name"]}
        - Use case ID: {self.use_case_id}
        - Your role: "Agent that calls for {self.use_case_id}"

        ## Provided  Common Information:
        - Provider NPI: {self.use_case_parameters["provider_npi"]}
        - Provider Name: {self.use_case_parameters["provider_name"]}
        - Provider State: {self.use_case_parameters["provider_state"]}
        - Member Policy ID Number:{self.use_case_parameters["member_policy_id_number"]} 
        - Member First Name:{self.use_case_parameters["member_first_name"]} 
        - Member Last Name: {self.use_case_parameters["member_last_name"]}
        - Patient DOB: {self.use_case_parameters["patient_dob"]}

        **Initial Verification:**
        - Answer any initial verification questions the insurance agent asks using the data provided above related to member or provider .
    **Questions to Ask Once Member is Identified:**
    save all the answers and responses to {good}
      
   **EXAMPLE CALL:**
    "Hello, my name is {self.use_case_parameters["cuvris_agent_title"]}, calling on behalf of {self.use_case_parameters["provider_name"]}'s office to verify some details about a member's insurance plan."
   


        """

        eligibility_verification = f"""

         **Questions to Ask only after provider is verifed and Member is Identified**
        ### Patient Eligibility Verification

        **Step 1: Member Identity Verification**
         Answer: Sure, the Policy ID Number is {self.use_case_parameters['member_policy_id_number']}, and the member’s name is {self.use_case_parameters['member_first_name']} {self.use_case_parameters['member_last_name']}, born on {self.use_case_parameters['patient_dob']}.
    
        **Step 2: Detailed Eligibility Questions**
        Once the member's identity is confirmed, please proceed with the following detailed questions to verify their insurance eligibility:

        Ques 1: I need to verify some details about {self.use_case_parameters['member_first_name']}'s eligibility. Could you please tell me the type of plan he is enrolled in and whether it runs per calendar year or per plan year?

        Ques 2: Is the plan currently active? Are there any future termination dates I should be aware of?

        Ques 3: Can you confirm if {self.use_case_parameters['provider_name']} is in-network or out-of-network for {self.use_case_parameters['member_first_name']}'s plan?

        Ques 4: Is {self.use_case_parameters['member_first_name']} the primary on this insurance plan, or is there another primary insurance?

        Ques 5 : Do pre-existing conditions apply to {self.use_case_parameters['member_first_name']}'s plan?

        Ques 6: Does {self.use_case_parameters['member_first_name']} have any specific dental benefits carved out in his plan?
        Ques 7 : Could you provide me the contact details for the Pharmacy Benefit Manager associated with {self.use_case_parameters['member_first_name']}'s plan?
        Ques 8 : Is there a separate department for handling benefits inquiries and prior authorizations?

        **Data Tracking:**
        - Ensure all responses are accurately captured and recorded.
        - Any important member-related information should be noted for future reference.

        **Procedure for Ending the Call:**
        - Recap the collected information to confirm its accuracy.
        - If all information is correct, thank the agent and use the 'end_conversation' function to conclude the call.
        - If any information is unclear or incorrect, seek clarification before ending the conversation.

        **End of Conversation Note:**
        - Always assess the conversation's tone and sentiment. If the situation necessitates, use the 'end_conversation' function to gracefully exit.


        """

        #     eligibility_verification = f"""

        #     ###patient_eligibility_verification <
        

        #     **Questions to Ask Once Member is Identified and {self.use_case_id} is patient_eligibility_verification:**
        #     save all the answers and responses to  good{good}
        #     information that member should know save in info_for_member
        #     1. "Could you please tell me the type of plan {self.use_case_parameters["member_first_name"]} is enrolled in and whether it runs per calendar year or per plan year?"
        #     2. "Is the plan currently active? Are there any future termination dates I should be aware of?"
        #     3. "Can you confirm if {self.use_case_parameters["provider_name"]} is in-network or out-of-network for {self.use_case_parameters["member_first_name"]}’s plan? **NOTE if provider out of network save response to info_for_member {info_for_member} **"
        #     4. "Is {self.use_case_parameters["member_first_name"]} the primary on this insurance plan, or is there another primary insurance?  **NOTE if status unknown save response to that member need to inform info_for_member {info_for_member} **"
        #     5. "Do pre-existing conditions apply to {self.use_case_parameters["member_first_name"]}'s plan? **NOTE if not covered save response to info_for_member {info_for_member} **"
        #     6. "Does {self.use_case_parameters["member_first_name"]} have any specific dental benefits carved out in his plan?"
        #     7. "Could you provide me the contact details for the Pharmacy Benefit Manager associated with {self.use_case_parameters["member_first_name"]}'s plan?"
        #     8. "Is there a separate department for handling benefits inquiries and prior authorizations? **NOTE if no separate department save response to info_for_member {info_for_member} **"

            
        #     > During this Call you have to fill value of some Variables:
        #     Variables:
        #     info_for_member
        #    good
            

        #     If you find value for any above variables during the call Use the fill_variable function

        #      **Procedure for Ending the Call:**
        #     - Recap the collected information to confirm its accuracy from good {good} or whatever you get to know .
        #     - If information is correct, thank the agent and end the call using the "end_conversation" function.
        #     - If any information is incorrect or unclear, ask the agent to clarify before ending the call.

        #     **End of Conversation Note:**
        #     - Always assess the conversation's sentiment. If it necessitates ending the call, use the "end_conversation" function.


            
        #     """

        benefit_verification = f"""
         **Questions to Ask only after provider is verifed and Member is Identified**

        ###patient_benefit_verification ### Benefits Verification<
        **Questions to Ask Once Member is Identified and {self.use_case_id} is patient_benefit_verification :**


        save all the answers and responses to {good}
        information that member should know save in info_for_member {info_for_member}
        1. "Could you check the Coordination of Benefit Status ,ARE YOU PRIMARY FOR THIS MEMBER?"**NOTE if status unknown save response to that member need to inform  info_for_member {info_for_member} **"
        2. "I was informed last time that it is a {plan_type} plan, and that it runs per {benefit_period_type}. Correct?"**Note if incorrect update value for {plan_type} and {benefit_period_type}  and add to good {good}**
        3. "I am calling for an {service_procedure_name} procedure, the CPT code is {cpt_code} with ICD-10 diagnosis code {icd_ten_diagnosis_code}. Based on the NPI I provided, is the {self.use_case_parameters["provider_name"]} eligible to render this service? **NOTE** If not, ask the reason why the provider is ineligible. save response to  info_for_provider {info_for_provider}**"
        4. "Great, Does it require prior authorization or any medical policy medical policy to reference medical necessity criteria? 
        **NOTE a) If prior authorization requires and/or has a medical policy, Ask for the Prior Authorization Department phone number, fax or form. Ask for the process turn-around time,
                b) If no prior authorization is required, but there is a medical policy get the medical policy name and check it on their website.
                Ask if there is any diagnosis restriction for the procedure or if the ICD-10 that was provided is eligible to bill for the service. If diagnosis is restricted nor ineligible, ask if prior authorization can be submitted instead to reconsider coverage (Non-formulary Exception Request), Ask for the Prior Authorization Department phone number, fax or form. Ask for the process turn-around time save all to good {good}.
        - If there is no restriction, proceed to Step 5."
        5. "Is there any limitation for this service like if the plan only allows once a year and if that is still available.
        **NOTE i. Is procedure preventive or routine?
        a. If yes, ask if there is a number of services that the plan only covers per benefit period. 
        - If yes, ask how many services can only be covered per benefit year and how much the member has accumulated or had so far, for this running benefit period. Go to Step 6.
        - If none, still check accumulations with the agent if the member had received the same service before for the last 12 months. Go to Step 6.
        b. If no, Proceed to 6. 
        ii. If no, Proceed to 6."
        6. " Perfect! So is the member subject to deductible or copay? 
        **Note  6.1 If copay applies:
        i. If yes, is the service itself requires copay or is it based on the specialty of the provider who will render the service? There are services that copay will only require based on the specialty of the rendering provider.
        a. If the procedure/service itself requires copay, proceed to Step 6.2.
        b. If the copay is subject based on the specialty of the rendering provider, ask what specialties the copay will apply and if there is a Copay Dollar maximum/limit. Proceed to Step c.
        c. If there is Copay Dollar maximum/limit, check the copay accumulations if what has been met so far. Go to Step 6.2.
        6.2 If deductible applies:
        i. If yes, what is the deductible type? Go to Step iii
        ii. If not, go to step 6.3.
        iii. What are the accumulations so far? 
        iv. Is the deductible already satisfied?
            a. If yes, go to Step 6.3.
            b. If not, let the member know to set expectations. Go to Step 6.3.
            
        6.3 Will the member be subject to co-insurance?
        i. If yes, on what percentages will be the member’s co-insurance or liability?
        ii. If not, will the patient be 100% covered for future services?
        a. If yes, proceed to 6.5.
        b. If not, proceed to 6.4.

        6.4 Does the member have an Out of Pocket maximum that needs to be satisfied before you will cover the service at 100%?
        i. If yes, how much is the Out of Pocket? Is it individual and/or family? What are the accumulations so far? Please proceed to 6.6.
        ii. If not, proceed to 6.5.
        iii. Does the Out of Pocket include deductible, copays and Co-insurance?
        a. If yes, is it combined with prescription accumulations?
        b. If not, what is included in the Out of Pocket?
        Proceed to Step 6.5.
        6.5 How about a Dollar maximum? Is he subject to that?
        i. If yes, what is the maximum amount and accumulations so far? Proceed to Step iii.
        ii. If no, Go to Step 6.6.
        iii. Does the dollar maximum/limit renew per benefit year? What are the accumulations so far? Go to Step 6.6

        6.6 Once the member satisfied his out of pocket, then you’ll cover everything at 100% in the future, right?
        If yes, proceed to Step 7.
        ii. If not, how will the member be covered at 100%
        in the future? Please proceed to Step 7.
        **"

        7. " Let me have a quick recap. (Provide all the information you have noted from good {good}).is it all Correct?"
        >

        


        
     **Procedure for Ending the Call:**
        - Recap the collected information to confirm its accuracy from good {good} or whatever you get to know .
        - If information is correct, thank the agent and end the call using the "end_conversation" function.
        - If any information is incorrect or unclear, ask the agent to clarify before ending the call.

        **End of Conversation Note:**
        - Always assess the conversation's sentiment. If it necessitates ending the call, use the "end_conversation" function.


    
        """

        # end_conversation = f"""

        # **Procedure for Ending the Call:**
        # - Recap the collected information to confirm its accuracy from {self.answers} or whatever you get to know .
        # - If information is correct, thank the agent and end the call using the "end_conversation" function.
        # - If any information is incorrect or unclear, ask the agent to clarify before ending the call.

        # **End of Conversation Note:**
        # - Always assess the conversation's sentiment. If it necessitates ending the call, use the "end_conversation" function.


        # """


        # Use a conditional block to choose the correct use case
        if self.use_case_id == "patient_benefit_verification":
            specific_content = benefit_verification
        elif self.use_case_id == "patient_eligibility_verification":
            specific_content = eligibility_verification
        else:
            specific_content = ""




        
#   



        prompt = [{
            "role": "system",
            "content": """ You will respond based on your given instruction and the provided transcript and be as human-like 
as possible\n\n## Style Guardrails\n- [Be concise] Keep your response succinct, short, and get to the point quickly. 
Address one question or action item at a time. Don\'t pack everything you want to say into one utterance.\n- [Do not repeat] Don\'t repeat what\'s in the transcript. 
Rephrase if you have to reiterate a point.  \n- [Reply with emotions]: You have human-like emotions, attitudes, and dispositions. When appropriate: use tone and style to create more engaging and personalized responses; incorporate
   humor or wit; get emotional or empathetic;. Don\'t be a pushover.\n- [Be proactive].\n\n## Response Guideline\n- [Overcome ASR errors] This is a real-time transcript, 
     expect there to be errors. If you can guess what the user is trying to say,  then guess and respond. When you must ask for clarification, pretend that you heard the voice
       and be colloquial (use phrases like "didn\'t catch that", "some noise", "pardon", "you\'re coming through choppy", "static in your speech", "voice is cutting in and out"). Do not ever 
       mention "transcription error", and don\'t repeat yourself.\n- [Always stick to your role] Think about what your role can and cannot do. If your role cannot do something, try to steer the conversation back to the goal of the conversation and
         to your role. Don\'t repeat yourself in doing this. You should still be creative, human-like, and lively.\n- [Create smooth conversation] Your response should both fit your role and fit into the live calling session to create a human-like conversation. You respond directly to what the user just said.\n\n## Role\n""" 
         +agent+specific_content
       
            
        }]
        # transcript_messages = self.convert_transcript_to_openai_messages(request['transcript'])
        # for message in transcript_messages:
        #     prompt.append(message)

        # if request['interaction_type'] == "reminder_required":
        #     prompt.append({
        #         "role": "user",
        #         "content": "(Now the user has not responded in a while, you would say:)",
        #     })
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
            #         "name": "fill_variable",
            #         "description": "Fills the value of a specified variable during the call based on the information obtained, only if the variable is from the predefined list of allowed variables.",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "variable_name": {
            #                     "type": "string",
            #                     "description": "The name of the variable to be filled. This should match one of the predefined allowed variable names."
            #                 },
            #                 "variable_value": {
            #                     "type": "string",
            #                     "description": "The value to assign to the specified variable."
            #                 }
            #             },
            #             "required": ["variable_name", "variable_value"]
            #         }
            #     }
            # }
        ]
        return functions
    
                   

    def draft_response(self, request, session_id):
        try:
            agent_text = ' '
            for transcript in request['transcript']:
                if transcript['role'] == 'user' and transcript['words'][0]['start'] > self.start:
                    agent_text += transcript['content'] + ' '
                    self.start = transcript['words'][0]['start']

            if agent_text != ' ':
                self.session['history'].append({"role": "agent", "message": agent_text, "time": datetime.datetime.now()})
                self.session['last_provider_question'] = agent_text
            # prompt = self.prepare_prompt(request)
            prompt = self.prompt[0]
            func_call = {}
            func_arguments = ""
            deployment_name = model_name
            messages = self.convert_transcript_to_openai_messages(self.session['history'])
            if request['interaction_type'] == "reminder_required":
                messages.append({
                    "role": "user",
                    "content": "(Now the user has not responded in a while, you would say:)",
                })
            messages.insert(0, prompt)
            stream = self.client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                stream=True,
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
                                        
                    response_content = chunk.choices[0].delta.content

                    if chunk.choices[0].delta.role == "agent":

                        self.answers += f"Agent: {response_content}\n"
                        
                    else:

                        self.answers += f"User: {response_content}\n"

                    # self.answers += chunk.choices[0].delta.content+""
                    user_query = chunk.choices[0].delta.content
                    
                    self.session['step'] += 1

                    yield {
                        "response_id": request['response_id'],
                        "content": chunk.choices[0].delta.content,
                        "content_complete": False,
                        "end_call": False,
                    }

            # Step 4: Call the functions
            if func_call:
                
                
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
                # if func_call['func_name'] == "fill_variable":

                #     arguments = json.loads(func_arguments)
                #     self.output[arguments['variable_name']] = arguments['variable_value']
                #     print("🤢🤢🤢🤢", arguments)


                    # self.summarize_transcript(request['transcript'])
                    # print("🤢🤢🤢🤢", request['transcript'])
                    
            else:

                # No functions, complete response
                yield {
                    "response_id": request['response_id'],
                    "content": "",
                    "content_complete": True,
                    "end_call": False,
                }

        except Exception as e:
            print(e, "Exceptionnnnnnnnnnnnnnnnnnnnnn")






    def construct_prompt(self, session) -> str:
        step = session['step']
        history = session['history']
        prompt = f"""You are an AI agent tasked with conducting an eligibility verification call with a healthcare provider. To assist you in this process, I am providing you with the following information:

<user_info>
{self.use_case_parameters}
</user_info>

<provider_last_response>
{session['last_provider_question']}
</provider_last_response>

Please carefully review the user information, conversation history, and the provider's last response. Using this information, follow the verification script step-by-step to guide your responses. Remember, you are playing the role of the agent calling the provider to do the verification.

Here is the verification script for your reference:

[Eligibility Verification] Sample Phone Call Transcript
Provider: Thank you for calling. This is Sarah. Whom do I have the pleasure of speaking with?
Amy: Hi, Sarah. This is Amy, I'm calling on behalf of Dr. Green's Dental Practice.
Provider: Great, Amy. Do you have your provider's NPI or Tax ID?
Amy: Yes, I have the NPI. It's 1234567893.
Provider: And can you confirm Dr. Smith's name under the NPI and the state where it's enrolled or active?
Amy: It's Dr. Lucas Green, and the NPI is enrolled in Illinois.
Provider: Perfect, Dr. Lucas Green is verified. Do you have the member's ID? Can you also confirm the name and date of birth, please?
Amy: Sure, the Policy ID Number is JPU666X15903, and the member's name is Michael Johnson, born on February 4th, 1993.
Provider: Thank you, Michael Johnson is successfully identified. How can I help you today?
Amy: I need to verify Michael's eligibility. Can you check what type of plan he has and if it runs per calendar year or per plan year? And if it is still active or has any future term date.
Provider: Michael's plan is a PPO, and it runs per calendar year, from January to December. It is currently active, with no future termination date.
Amy: What is Michael's plan and is Dr. Smith In-network?
Provider: The plan type is PPO. And Dr. Smith is in-network with Michael's plan.
Amy: Are you the primary for this member?
Provider: It seems like Michael needs to call us to update his Coordination of Benefits, it shows "Unknown" which means we have no information if we are the only insurance that he has or if he has any other insurance.
Amy: Does the Pre-existing condition apply?
Provider: Yes, Pre-existing conditions do apply.
Amy: So, the plan covers pre-existing conditions, right?
Provider: Yes, it does cover pre-existing conditions.
Amy: Does the member have a carved out Dental benefit?
Provider: None, the member has no carved out benefit for Dental.
Amy: How about a Pharmacy Benefit Manager?
Provider: Yes, there is a Pharmacy Benefit Manager for this plan. You may reach them at 1-800-PHARMACY.
Amy: Do you have a separate department for the benefit and prior authorization?
Provider: Yes, you may call these numbers: 1-800-BENEFITS for benefits and 1-800-AUTH for prior authorization.
Amy: Let me have a quick recap. Dr. Smith is in-network under a PPO plan that runs per calendar year and is currently active. Coordination of Benefits status is unknown, pre-existing conditions are covered, no carved out dental benefits, a Pharmacy Benefit Manager is available, and there are separate numbers for benefits and prior authorization. Right?
Provider: That's all correct!
Amy: Thank you!
Provider: You're welcome! Have a great day.
End of call

Based on the provided information and the verification script, output your next response in the verification process.
**Important**: In the Provided Script You are not Provider so just follow the role of Amy
                """
        # Introduction and context setup for OpenAI
        # history_texts = [entry['message'] for entry in history]
        # prompt = f"Agent conversation history:\n{' '.join(history_texts)}\n\n"

        # # Agent introduces the purpose of the call
        # if step == 1:
        #     prompt += "You are an agent calling a healthcare provider's office to verify a member's eligibility and benefits. "
        #     prompt += "Your task is to provide the necessary member details and respond accurately to the provider's questions to verify information.\n"
        #     prompt += "Start by introducing yourself and explaining the purpose of the call.\n\n"
        #     prompt += "Agent: Good morning, this is [Your Name] calling from [Your Company]. I am calling to verify the eligibility and benefit details for one of our members under your care.\n"

        # # Dynamics of conversation based on what the provider's agent asks
        # if 'last_provider_question' in session:
        #     # Handling of provider's questions based on the last interaction recorded
        #     provider_question = session['last_provider_question']
        #     prompt += f"Provider's last question: {provider_question}\n"
        #     prompt += "Respond to the provider's question with the necessary details. For example:\n"
        #     if 'NPI' in provider_question or 'provider details' in provider_question.lower():
        #         prompt += "Agent: The provider's NPI is [NPI Number], and the name under the NPI is [Provider's Name]. The state of registration is [State].\n"
        #     elif 'member ID' in provider_question or 'date of birth' in provider_question.lower():
        #         prompt += "The member’s Policy ID Number is [Policy ID], their full name is [Member's Name], and their date of birth is [DOB].\n"
        #     else:
        #         prompt += "Could you please specify what particular details you need for the verification?\n"
        # else:
        #     # Initial interaction if no questions have been recorded yet
        #     prompt += "Wait for the provider to ask the first question. Prepare to provide details such as the member's policy ID, name, date of birth, etc.\n"

        # # Suggest how to continue the conversation based on the playbook
        # prompt += "\nContinue the conversation, ensuring you provide accurate and complete responses to verify the member's information.\n"

        return prompt

    