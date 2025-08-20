# SOPHIA Action Schemas

This document defines the standardized action schemas for each of SOPHIA's capabilities. These schemas will be used by the `ActionEngine` to execute actions based on user intent.

## 1. Research Actions

### `research.get_weather`

*   **Description:** Get the current weather for a specific location.
*   **Parameters:**
    *   `location` (string, required): The city and state or zip code for which to get the weather.
*   **Handler:** `research-mcp/weather`

### `research.web_search`

*   **Description:** Perform a web search for a given query.
*   **Parameters:**
    *   `query` (string, required): The search query.
*   **Handler:** `research-mcp/search`

## 2. Code Actions

### `code.create_file`

*   **Description:** Create a new file with the given content.
*   **Parameters:**
    *   `file_path` (string, required): The absolute path of the file to create.
    *   `content` (string, optional): The content to write to the file.
*   **Handler:** `code-mcp/create_file`

### `code.read_file`

*   **Description:** Read the content of a file.
*   **Parameters:**
    *   `file_path` (string, required): The absolute path of the file to read.
*   **Handler:** `code-mcp/read_file`

### `code.update_file`

*   **Description:** Update the content of a file.
*   **Parameters:**
    *   `file_path` (string, required): The absolute path of the file to update.
    *   `content` (string, required): The new content to write to the file.
*   **Handler:** `code-mcp/update_file`

### `code.commit_and_push`

*   **Description:** Commit and push changes to the GitHub repository.
*   **Parameters:**
    *   `commit_message` (string, required): The commit message.
    *   `branch` (string, optional): The branch to push to. Defaults to `main`.
*   **Handler:** `code-mcp/commit_and_push`

## 3. Business Actions

### `business.summarize_gong_calls`

*   **Description:** Summarize recent Gong calls.
*   **Parameters:**
    *   `time_period` (string, optional): The time period to summarize (e.g., "last 24 hours," "last week"). Defaults to "last 24 hours."
*   **Handler:** `business-mcp/summarize_gong_calls`

### `business.create_asana_task`

*   **Description:** Create a new task in Asana.
*   **Parameters:**
    *   `project_id` (string, required): The ID of the Asana project.
    *   `task_name` (string, required): The name of the task.
    *   `assignee` (string, optional): The email address of the assignee.
*   **Handler:** `business-mcp/create_asana_task`

## 4. Deployment Actions

### `deployment.deploy_service`

*   **Description:** Deploy a service to a specified environment.
*   **Parameters:**
    *   `service_name` (string, required): The name of the service to deploy.
    *   `environment` (string, required): The environment to deploy to (e.g., "staging," "production").
*   **Handler:** `deployment-mcp/deploy_service`

### `deployment.rollback_service`

*   **Description:** Roll back a service to the previous version.
*   **Parameters:**
    *   `service_name` (string, required): The name of the service to roll back.
    *   `environment` (string, required): The environment to roll back in.
*   **Handler:** `deployment-mcp/rollback_service`


