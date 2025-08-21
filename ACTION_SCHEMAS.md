# SOPHIA Action Schemas v4.2

This document defines the standardized action schemas for each of SOPHIA's capabilities. These schemas are used by the `ActionEngine` to execute actions based on user intent with unified normalization.

**Schema Version:** v2  
**Last Updated:** August 21, 2025  
**Normalization Spec:** All responses follow unified result format with proper error handling

## Unified Response Format

All actions return results in the following normalized format:

```json
{
  "status": "success|failure|partial|timeout",
  "query": "original user query",
  "results": [...],
  "summary": {
    "text": "summary text",
    "confidence": 0.8,
    "model": "gpt-4",
    "sources": [{"title": "...", "url": "..."}]
  },
  "timestamp": "2025-08-21T04:00:00Z",
  "execution_time_ms": 1500,
  "errors": []
}
```

## Research Result Schema

```json
{
  "title": "Result title",
  "url": "https://example.com",
  "snippet": "Brief description",
  "extracted_text": "Full extracted content",
  "source": "serper|tavily|zenrows|apify",
  "fetched_at": "2025-08-21T04:00:00Z",
  "score": 0.85
}
```

## 1. Research Actions

### `research.search`

*   **Description:** Perform comprehensive multi-source research with robust parsing
*   **Parameters:**
    *   `query` (string, required): The research query
    *   `sources` (array, optional): Sources to use ["serper", "tavily", "zenrows", "apify"]
    *   `max_results_per_source` (integer, optional): Maximum results per source (default: 3)
    *   `include_content` (boolean, optional): Extract full content (default: true)
    *   `summarize` (boolean, optional): Generate summary (default: true)
*   **Handler:** `sophia-research/search`
*   **Timeout:** 30s
*   **Fallbacks:** Graceful degradation if providers fail

### `research.fetch`

*   **Description:** Fetch and extract content from specific URLs with robust parsing
*   **Parameters:**
    *   `urls` (array, required): List of URLs to fetch
    *   `extract_text` (boolean, optional): Extract readable text (default: true)
    *   `use_js_render` (boolean, optional): Use JavaScript rendering (default: false)
*   **Handler:** `sophia-research/fetch`
*   **Timeout:** 15s
*   **Fallbacks:** HTML→text extraction if JS rendering fails

### `research.summarize`

*   **Description:** Generate summary from research results with LLM + extractive fallbacks
*   **Parameters:**
    *   `results` (array, required): Research results to summarize
    *   `query` (string, required): Original query for context
    *   `model` (string, optional): LLM model to use (default: "gpt-4")
*   **Handler:** `sophia-research/summarize`
*   **Timeout:** 15s
*   **Fallbacks:** Extractive summary → top snippets if LLM fails

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



## 2. Business Actions

### `business.create_task`

*   **Description:** Create task in business management system (Asana/Linear/Notion)
*   **Parameters:**
    *   `title` (string, required): Task title
    *   `description` (string, optional): Task description
    *   `assignee` (string, optional): Assignee email or ID
    *   `project` (string, optional): Project ID or name
    *   `priority` (string, optional): Task priority (low/medium/high)
*   **Handler:** `sophia-business/create_task`
*   **Timeout:** 10s
*   **Fallbacks:** Try alternative platforms if primary fails

### `business.create_issue`

*   **Description:** Create issue in project management system
*   **Parameters:**
    *   `title` (string, required): Issue title
    *   `body` (string, optional): Issue description
    *   `labels` (array, optional): Issue labels
    *   `assignee` (string, optional): Assignee username
*   **Handler:** `sophia-business/create_issue`
*   **Timeout:** 10s

### `business.create_page`

*   **Description:** Create page in knowledge management system (Notion)
*   **Parameters:**
    *   `title` (string, required): Page title
    *   `content` (string, required): Page content
    *   `parent` (string, optional): Parent page ID
*   **Handler:** `sophia-business/create_page`
*   **Timeout:** 15s

## 3. Code Actions

### `code.pr_open`

*   **Description:** Open pull request in GitHub repository
*   **Parameters:**
    *   `title` (string, required): PR title
    *   `body` (string, optional): PR description
    *   `branch` (string, required): Source branch
    *   `base` (string, optional): Target branch (default: "main")
    *   `draft` (boolean, optional): Create as draft (default: false)
*   **Handler:** `sophia-code/pr_open`
*   **Timeout:** 10s

### `code.create_file`

*   **Description:** Create new file in repository
*   **Parameters:**
    *   `path` (string, required): File path
    *   `content` (string, required): File content
    *   `commit_message` (string, optional): Commit message
*   **Handler:** `sophia-code/create_file`
*   **Timeout:** 10s

### `code.update_file`

*   **Description:** Update existing file in repository
*   **Parameters:**
    *   `path` (string, required): File path
    *   `content` (string, required): New content
    *   `commit_message` (string, optional): Commit message
*   **Handler:** `sophia-code/update_file`
*   **Timeout:** 10s

## 4. Deploy Actions

### `deploy.release`

*   **Description:** Deploy service to production
*   **Parameters:**
    *   `service` (string, required): Service name
    *   `version` (string, optional): Version to deploy
    *   `environment` (string, optional): Target environment (default: "production")
*   **Handler:** `sophia-deploy/release`
*   **Timeout:** 60s

### `deploy.rollback`

*   **Description:** Rollback service to previous version
*   **Parameters:**
    *   `service` (string, required): Service name
    *   `version` (string, optional): Version to rollback to
*   **Handler:** `sophia-deploy/rollback`
*   **Timeout:** 30s

## 5. Context Actions

### `context.store`

*   **Description:** Store context information for future reference
*   **Parameters:**
    *   `key` (string, required): Context key
    *   `value` (any, required): Context value
    *   `ttl` (integer, optional): Time to live in seconds
*   **Handler:** `sophia-context/store`
*   **Timeout:** 5s

### `context.retrieve`

*   **Description:** Retrieve stored context information
*   **Parameters:**
    *   `key` (string, required): Context key
*   **Handler:** `sophia-context/retrieve`
*   **Timeout:** 5s

## 6. Memory Actions

### `memory.add`

*   **Description:** Add information to long-term memory
*   **Parameters:**
    *   `content` (string, required): Content to remember
    *   `category` (string, optional): Memory category
    *   `metadata` (object, optional): Additional metadata
*   **Handler:** `sophia-memory/add`
*   **Timeout:** 10s

### `memory.search`

*   **Description:** Search long-term memory
*   **Parameters:**
    *   `query` (string, required): Search query
    *   `limit` (integer, optional): Maximum results (default: 10)
*   **Handler:** `sophia-memory/search`
*   **Timeout:** 10s

---

## Error Handling

All actions implement the following error handling strategy:

1. **Timeout Handling:** Actions timeout according to their specified limits
2. **Graceful Degradation:** Fallback to alternative methods when possible
3. **Error Normalization:** All errors returned in consistent format
4. **Partial Results:** Return partial results when some operations succeed

## Budget Controls

Daily budget limits are enforced per provider:
- `RESEARCH_BUDGET_DAILY_REQUESTS=1500`
- Budget exceeded returns graceful explanation with partial results

## Observability

All actions include:
- Request ID in logs
- Latency measurements per provider
- Prometheus metrics: `provider_requests_total{provider,result}`
- Sentry breadcrumbs with provider and outcome

