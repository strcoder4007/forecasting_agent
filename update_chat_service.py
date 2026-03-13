with open("backend/chat_service.py", "r") as f:
    content = f.read()

content = content.replace(
    'contents=[types.Content(role="user", parts=[types.Part.from_text(intent_prompt)])]',
    'contents=intent_prompt'
)
content = content.replace(
    'contents=[types.Content(role="user", parts=[types.Part.from_text(general_prompt)])]',
    'contents=general_prompt'
)
content = content.replace(
    'contents=[\n                    types.Content(role="user", parts=[types.Part.from_text(f"{schema_context}\\n\\nUser Question: {user_query}")])\n                ]',
    'contents=f"{schema_context}\\n\\nUser Question: {user_query}"'
)
content = content.replace(
    'contents=[types.Content(role="user", parts=[types.Part.from_text(synthesis_prompt)])]',
    'contents=synthesis_prompt'
)

with open("backend/chat_service.py", "w") as f:
    f.write(content)
