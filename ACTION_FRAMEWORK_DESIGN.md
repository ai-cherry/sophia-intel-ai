# SOPHIA Action Framework Design

## 1. Introduction

This document outlines the design of the SOPHIA Action Framework, a new architecture that enables SOPHIA to execute real-world tasks based on user intent. This framework will replace the current "chat-only" model and provide a robust and scalable solution for action execution.

## 2. Core Components

The Action Framework consists of three core components:

*   **`ActionEngine`:** The central orchestrator that manages the action execution lifecycle.
*   **Action Schemas:** Standardized definitions for each supported action.
*   **MCP Services:** The backend services that perform the actual work (research, code, business, etc.).

## 3. `ActionEngine` Design

The `ActionEngine` will be implemented as a Python class with the following responsibilities:

*   **Intent Recognition:** Use a natural language understanding (NLU) model to identify the user's intent from their chat message.
*   **Action Dispatching:** Dispatch the recognized intent to the appropriate MCP service based on the action schema.
*   **Parameter Mapping:** Extract and map the required parameters from the user's message to the action schema.
*   **Error Handling:** Handle any errors or exceptions that occur during action execution and provide a clear error message to the user.

```python
class ActionEngine:
    def __init__(self):
        # Initialize NLU model and MCP clients
        pass

    def execute_action(self, user_message):
        intent = self.recognize_intent(user_message)
        action_schema = self.get_action_schema(intent)
        parameters = self.extract_parameters(user_message, action_schema)
        
        try:
            result = self.dispatch_action(action_schema, parameters)
            return self.format_result(result)
        except Exception as e:
            return self.handle_error(e)
```

## 4. Action Schema Design

Action schemas will be defined in JSON format and will include the following fields:

*   `name`: A unique name for the action (e.g., `research.get_weather`).
*   `description`: A brief description of what the action does.
*   `parameters`: A list of input parameters, including their name, type, and whether they are required.
*   `handler`: The MCP service and endpoint that will handle the action.

### Example Action Schema:

```json
{
  "name": "research.get_weather",
  "description": "Get the current weather for a specific location.",
  "parameters": [
    {
      "name": "location",
      "type": "string",
      "required": true
    }
  ],
  "handler": {
    "service": "research-mcp",
    "endpoint": "/weather"
  }
}
```

## 5. Implementation Plan

The implementation of the Action Framework will be divided into the following steps:

1.  **Develop the `ActionEngine` class:** Implement the core logic for intent recognition, action dispatching, and error handling.
2.  **Define action schemas:** Create a comprehensive set of action schemas for all supported capabilities.
3.  **Update MCP services:** Modify the MCP services to expose the new action endpoints and handle the incoming requests.
4.  **Integrate with the dashboard:** Replace the current chat logic with the new `ActionEngine` to enable real action execution.

By following this design, we can create a powerful and flexible Action Framework that will enable SOPHIA to perform a wide range of real-world tasks and provide a truly interactive and intelligent user experience.


