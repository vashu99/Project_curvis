from openai import OpenAI
client = OpenAI()

client.fine_tuning.jobs.create(
  training_file="file-e7djPzBugtcISFxpUaz6avEY", 
  model="gpt-3.5-turbo"
)