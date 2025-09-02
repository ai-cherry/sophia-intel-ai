with open('app/server_shim.py') as f:
    content = f.read()

# Fix the f-string backslash issue
content = content.replace(
    "yield f\"data: {json.dumps({'token': '\\n\\nTask: '})}\\n\\n\"",
    "task_newline = '\\n\\nTask: '; yield f\"data: {json.dumps({'token': task_newline})}\\n\\n\""
)

with open('app/server_shim.py', 'w') as f:
    f.write(content)
print('Fixed f-string issue')
