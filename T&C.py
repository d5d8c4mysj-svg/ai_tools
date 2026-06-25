import cohere

API_KEY = ""

co = cohere.ClientV2(API_KEY)

system_prompt = """You are a legal document analyzer. When given terms and conditions text, extract the following information:
1. Key user obligations
2. Cancellation/refund policy
3. Any fees mentioned
4. Data privacy points
5. Termination conditions

Format your response as a clear numbered list under these exact headings. If any section isn't mentioned in the text, write Not specified. Additionally, add a final section called Needs Attention where you flag anything unusual, one-sided, or particularly important that the user should pay close attention to before agreeing."""

print("T&C Summarizer ready! Paste your terms and conditions text below.")

user_input = input("Paste text: ")

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_input}
]

response = co.chat(
    model="command-r-plus-08-2024",
    messages=messages
)

bot_reply = response.message.content[0].text
print()
print(bot_reply)