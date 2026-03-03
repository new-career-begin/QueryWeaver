<div align="center">  
  <h1>QueryWeaver (Text2SQL)</h1>

**REST API · MCP · Graph-powered** 

QueryWeaver is an **open-source Text2SQL** tool that converts plain-English questions into SQL using **graph-powered schema understanding**. It helps you ask databases natural-language questions and returns SQL and results.

Connect and ask questions: [![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?&logo=discord&logoColor=white)](https://discord.gg/b32KEzMzce)

[![Try Free](https://img.shields.io/badge/Try%20Free-FalkorDB%20Cloud-FF8101?labelColor=FDE900&link=https://app.falkordb.cloud)](https://app.falkordb.cloud)
[![Dockerhub](https://img.shields.io/docker/pulls/falkordb/queryweaver?label=Docker)](https://hub.docker.com/r/falkordb/queryweaver/)
[![Tests](https://github.com/FalkorDB/QueryWeaver/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/FalkorDB/QueryWeaver/actions/workflows/tests.yml)
[![Swagger UI](https://img.shields.io/badge/API-Swagger-11B48A?logo=swagger&logoColor=white)](https://app.queryweaver.ai/docs)
</div>

![new-qw-ui-gif](https://github.com/user-attachments/assets/34663279-0273-4c21-88a8-d20700020a07)


## Supported Databases

QueryWeaver supports the following database systems:

- **PostgreSQL** - Full support for PostgreSQL databases
- **MySQL** - Full support for MySQL databases  
- **达梦数据库 (DM Database)** - 支持达梦数据库 8.0+
- **人大金仓数据库 (KingbaseES)** - 支持人大金仓数据库 V8+

For detailed connection guides, see the [Database Support Documentation](docs/database-support-quickstart.md).

## Get Started

### Docker

> 💡 Recommended for evaluation purposes (Local Python or Node are not required)
```bash
docker run -p 5000:5000 -it falkordb/queryweaver
```


Launch: http://localhost:5000

---

### Use an .env file (Recommended)

Create a local `.env` by copying `.env.example` and passing it to Docker. This is the simplest way to provide all required configuration:

```bash
cp .env.example .env
# edit .env to set your values, then:
docker run -p 5000:5000 --env-file .env falkordb/queryweaver
```

### Alternative: Pass individual environment variables

If you prefer to pass variables on the command line, use `-e` flags (less convenient for many variables):

```bash
docker run -p 5000:5000 -it \
  -e APP_ENV=production \
  -e FASTAPI_SECRET_KEY=your_super_secret_key_here \
  -e GOOGLE_CLIENT_ID=your_google_client_id \
  -e GOOGLE_CLIENT_SECRET=your_google_client_secret \
  -e GITHUB_CLIENT_ID=your_github_client_id \
  -e GITHUB_CLIENT_SECRET=your_github_client_secret \
  -e WECHAT_APP_ID=your_wechat_app_id \
  -e WECHAT_APP_SECRET=your_wechat_app_secret \
  -e WECOM_CORP_ID=your_wecom_corp_id \
  -e WECOM_AGENT_ID=your_wecom_agent_id \
  -e WECOM_CORP_SECRET=your_wecom_corp_secret \
  -e AZURE_API_KEY=your_azure_api_key \
  falkordb/queryweaver
```

> Note: To use OpenAI directly instead of Azure OpenAI, replace `AZURE_API_KEY` with `OPENAI_API_KEY` in the above command.

> WeChat and WeCom OAuth are optional. Only include their environment variables if you want to enable these login methods.

> For a full list of configuration options, consult `.env.example`.

## Memory TTL (optional)

QueryWeaver stores per-user conversation memory in FalkorDB. By default these graphs persist indefinitely. Set `MEMORY_TTL_SECONDS` to apply a Redis TTL (in seconds) so idle memory graphs are automatically cleaned up.

```bash
# Expire memory graphs after 1 week of inactivity
MEMORY_TTL_SECONDS=604800
```

The TTL is refreshed on every user interaction, so active users keep their memory.

## MCP server: host or connect (optional)

QueryWeaver includes optional support for the Model Context Protocol (MCP). You can either have QueryWeaver expose an MCP-compatible HTTP surface (so other services can call QueryWeaver as an MCP server), or configure QueryWeaver to call an external MCP server for model/context services.

What QueryWeaver provides
- The app registers MCP operations focused on Text2SQL flows:
   - `list_databases`
   - `connect_database`
   - `database_schema`
   - `query_database`

- To disable the built-in MCP endpoints set `DISABLE_MCP=true` in your `.env` or environment (default: MCP enabled).
- Configuration

- `DISABLE_MCP` — disable QueryWeaver's built-in MCP HTTP surface. Set to `true` to disable. Default: `false` (MCP enabled).

Examples

Disable the built-in MCP when running with Docker:

```bash
docker run -p 5000:5000 -it --env DISABLE_MCP=true falkordb/queryweaver
```

Calling the built-in MCP endpoints (example)
- The MCP surface is exposed as HTTP endpoints. 


### Server Configuration

Below is a minimal example `mcp.json` client configuration that targets a local QueryWeaver instance exposing the MCP HTTP surface at `/mcp`.

```json
{
   "servers": {
      "queryweaver": {
         "type": "http",
         "url": "http://127.0.0.1:5000/mcp",
         "headers": {
            "Authorization": "Bearer your_token_here"
         }
      }
   },
   "inputs": []
}
```

## REST API 

### API Documentation

Swagger UI: https://app.queryweaver.ai/docs

OpenAPI JSON: https://app.queryweaver.ai/openapi.json

### Overview

QueryWeaver exposes a small REST API for managing graphs (database schemas) and running Text2SQL queries. All endpoints that modify or access user-scoped data require authentication via a bearer token. In the browser the app uses session cookies and OAuth flows; for CLI and scripts you can use an API token (see `tokens` routes or the web UI to create one).

Core endpoints
- GET /graphs — list available graphs for the authenticated user
- GET /graphs/{graph_id}/data — return nodes/links (tables, columns, foreign keys) for the graph
- POST /graphs — upload or create a graph (JSON payload or file upload)
- POST /graphs/{graph_id} — run a Text2SQL chat query against the named graph (streaming response)

Authentication
- Add an Authorization header: `Authorization: Bearer <API_TOKEN>`

Examples

1) List graphs (GET)

curl example:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
   https://app.queryweaver.ai/graphs
```

Python example:

```python
import requests
resp = requests.get('https://app.queryweaver.ai/graphs', headers={'Authorization': f'Bearer {TOKEN}'})
print(resp.json())
```

2) Get graph schema (GET)

curl example:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
   https://app.queryweaver.ai/graphs/my_database/data
```

Python example:

```python
resp = requests.get('https://app.queryweaver.ai/graphs/my_database/data', headers={'Authorization': f'Bearer {TOKEN}'})
print(resp.json())
```

3) Load a graph (POST) — JSON payload

```bash
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
   -d '{"database": "my_database", "tables": [...]}' \
   https://app.queryweaver.ai/graphs
```

Or upload a file (multipart/form-data):

```bash
curl -H "Authorization: Bearer $TOKEN" -F "file=@schema.json" \
   https://app.queryweaver.ai/graphs
```

4) Query a graph (POST) — run a chat-based Text2SQL request

The `POST /graphs/{graph_id}` endpoint accepts a JSON body with at least a `chat` field (an array of messages). The endpoint streams processing steps and the final SQL back as server-sent-message chunks delimited by a special boundary used by the frontend. For simple scripting you can call it and read the final JSON object from the streamed messages.

Example payload:

```json
{
   "chat": ["How many users signed up last month?"],
   "result": [],
   "instructions": "Prefer PostgreSQL compatible SQL"
}
```

curl example (simple, collects whole response):

```bash
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
   -d '{"chat": ["Count orders last week"]}' \
   https://app.queryweaver.ai/graphs/my_database
```

Python example (stream-aware):

```python
import requests
import json

url = 'https://app.queryweaver.ai/graphs/my_database'
headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
with requests.post(url, headers=headers, json={"chat": ["Count orders last week"]}, stream=True) as r:
      # The server yields JSON objects delimited by a message boundary string
      boundary = '|||FALKORDB_MESSAGE_BOUNDARY|||'
      buffer = ''
      for chunk in r.iter_content(decode_unicode=True, chunk_size=1024):
            buffer += chunk
            while boundary in buffer:
                  part, buffer = buffer.split(boundary, 1)
                  if not part.strip():
                        continue
                  obj = json.loads(part)
                  print('STREAM:', obj)

Notes & tips
- Graph IDs are namespaced per-user. When calling the API directly use the plain graph id (the server will namespace by the authenticated user). For uploaded files the `database` field determines the saved graph id.
- The streaming response includes intermediate reasoning steps, follow-up questions (if the query is ambiguous or off-topic), and the final SQL. The frontend expects the boundary string `|||FALKORDB_MESSAGE_BOUNDARY|||` between messages.
- For destructive SQL (INSERT/UPDATE/DELETE etc) the service will include a confirmation step in the stream; the frontend handles this flow. If you automate destructive operations, ensure you handle confirmation properly (see the `ConfirmRequest` model in the code).


## Development

Follow these steps to run and develop QueryWeaver from source.

### Prerequisites

- Python 3.12+
- pipenv
- A FalkorDB instance (local or remote)
- Node.js and npm (for the React frontend)

### Install and configure

Quickstart (recommended for development):

```bash
# Clone the repo
git clone https://github.com/FalkorDB/QueryWeaver.git
cd QueryWeaver

# Install dependencies (backend + frontend) and start the dev server
make install
make run-dev
```

If you prefer to set up manually or need a custom environment, use Pipenv:

```bash
# Install Python (backend) and frontend dependencies
pipenv sync --dev

# Create a local environment file
cp .env.example .env
# Edit .env with your values (set APP_ENV=development for local development)
```

### Run the app locally

```bash
pipenv run uvicorn api.index:app --host 0.0.0.0 --port 5000 --reload
```

The server will be available at http://localhost:5000

Alternatively, the repository provides Make targets for running the app:

```bash
make run-dev   # development server (reload, debug-friendly)
make run-prod  # production mode (ensure frontend build if needed)
```

### Frontend build (when needed)

The frontend is a modern React + Vite app in `app/`. Build before production runs or after frontend changes:

```bash
make install       # installs backend and frontend deps
make build-prod    # builds the frontend into app/dist/

# or manually
cd app
npm ci
npm run build
```

### OAuth configuration

QueryWeaver supports multiple OAuth providers: Google, GitHub, WeChat (微信), and WeCom (企业微信). Create OAuth credentials for each provider you want to enable and paste the client IDs/secrets into your `.env` file.

#### Google OAuth
- Set authorized origin and callback `http://localhost:5000/login/google/authorized`

#### GitHub OAuth
- Set homepage and callback `http://localhost:5000/login/github/authorized`

#### WeChat OAuth (微信登录)
WeChat OAuth enables Chinese users to log in using their WeChat accounts.

**Prerequisites:**
- Register at [WeChat Open Platform](https://open.weixin.qq.com/)
- Create a Website Application
- Configure authorized callback domain
- Obtain AppID and AppSecret
- Domain must be ICP-registered (for China deployments)

**Configuration:**
```bash
# WeChat OAuth credentials
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_wechat_app_secret

# Optional: custom callback URL (defaults to auto-generated)
WECHAT_REDIRECT_URI=http://localhost:5000/login/wechat/authorized
```

**Callback URL:** `http://localhost:5000/login/wechat/authorized`

**Notes:**
- WeChat OAuth requires HTTPS in production
- Users without email will get a virtual email: `{openid}@wechat.queryweaver.local`
- Supports both PC QR code scanning and mobile in-app authorization

#### WeCom OAuth (企业微信登录)
WeCom (WeChat Work) OAuth is designed for enterprise users within organizations.

**Prerequisites:**
- Register at [WeCom Admin Console](https://work.weixin.qq.com/)
- Create a self-built application or third-party application
- Configure trusted domain
- Obtain CorpID, AgentID, and CorpSecret
- Configure application permissions

**Configuration:**
```bash
# WeCom OAuth credentials
WECOM_CORP_ID=ww1234567890abcdef
WECOM_AGENT_ID=1000001
WECOM_CORP_SECRET=your_wecom_corp_secret

# Optional: custom callback URL (defaults to auto-generated)
WECOM_REDIRECT_URI=http://localhost:5000/login/wecom/authorized
```

**Callback URL:** `http://localhost:5000/login/wecom/authorized`

**Notes:**
- WeCom OAuth requires HTTPS in production
- Users can authenticate with their enterprise WeChat account
- Retrieves user information including department and employee ID
- Supports both PC QR code scanning and mobile in-app authorization

#### Environment-specific OAuth settings

For production/staging deployments, set `APP_ENV=production` or `APP_ENV=staging` in your environment to enable secure session cookies (HTTPS-only). This prevents OAuth CSRF state mismatch errors.

```bash
# For production/staging (enables HTTPS-only session cookies)
APP_ENV=production

# For development (allows HTTP session cookies)
APP_ENV=development
```

**Important**: If you're getting "mismatching_state: CSRF Warning!" errors on staging/production, ensure `APP_ENV` is set to `production` or `staging` to enable secure session handling.

### AI/LLM configuration

QueryWeaver uses AI models for Text2SQL conversion and supports both Azure OpenAI and OpenAI directly.

#### Default: Azure OpenAI

By default, QueryWeaver is configured to use Azure OpenAI. You need to set all three Azure credentials:

```bash
AZURE_API_KEY=your_azure_api_key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-12-01-preview
```

#### Alternative: OpenAI directly

To use OpenAI directly instead of Azure, simply set the `OPENAI_API_KEY` environment variable:

```bash
OPENAI_API_KEY=your_openai_api_key
```

When `OPENAI_API_KEY` is provided, QueryWeaver automatically switches to use OpenAI's models:
- Embedding model: `openai/text-embedding-ada-002`
- Completion model: `openai/gpt-4.1`

This configuration is handled automatically in `api/config.py` - you only need to provide the appropriate API key.

#### Docker examples with AI configuration

Using Azure OpenAI:
```bash
docker run -p 5000:5000 -it \
  -e FASTAPI_SECRET_KEY=your_secret_key \
  -e AZURE_API_KEY=your_azure_api_key \
  -e AZURE_API_BASE=https://your-resource.openai.azure.com/ \
  -e AZURE_API_VERSION=2024-12-01-preview \
  falkordb/queryweaver
```

Using OpenAI directly:
```bash
docker run -p 5000:5000 -it \
  -e FASTAPI_SECRET_KEY=your_secret_key \
  -e OPENAI_API_KEY=your_openai_api_key \
  falkordb/queryweaver
```

## Testing

> Quick note: many tests require FalkorDB to be available. Use the included helper to run a test DB in Docker if needed.

### Prerequisites

- Install dev dependencies: `pipenv sync --dev`
- Start FalkorDB (see `make docker-falkordb`)
- Install Playwright browsers: `pipenv run playwright install`

### Quick commands

Recommended: prepare the development/test environment using the Make helper (installs dependencies and Playwright browsers):

```bash
# Prepare development/test environment (installs deps and Playwright browsers)
make setup-dev
```

Alternatively, you can run the E2E-specific setup script and then run tests manually:

```bash
# Prepare E2E test environment (installs browsers and other setup)
./setup_e2e_tests.sh

# Run all tests
make test

# Run unit tests only (faster)
make test-unit

# Run E2E tests (headless)
make test-e2e

# Run E2E tests with a visible browser for debugging
make test-e2e-headed
```

### Test types

- Unit tests: focus on individual modules and utilities. Run with `make test-unit` or `pipenv run pytest tests/ -k "not e2e"`.
- End-to-end (E2E) tests: run via Playwright and exercise UI flows, OAuth, file uploads, schema processing, chat queries, and API endpoints. Use `make test-e2e`.

See `tests/e2e/README.md` for full E2E test instructions.

### CI/CD

GitHub Actions run unit and E2E tests on pushes and pull requests. Failures capture screenshots and artifacts for debugging.

## Troubleshooting

- FalkorDB connection issues: start the DB helper `make docker-falkordb` or check network/host settings.
- Playwright/browser failures: install browsers with `pipenv run playwright install` and ensure system deps are present.
- Missing environment variables: copy `.env.example` and fill required values.
- **OAuth "mismatching_state: CSRF Warning!" errors**: Set `APP_ENV=production` (or `staging`) in your environment for HTTPS deployments, or `APP_ENV=development` for HTTP development environments. This ensures session cookies are configured correctly for your deployment type.
- **WeChat/WeCom OAuth not working**: 
  - Verify your AppID/CorpID and Secret are correct
  - Ensure callback URL is configured in WeChat/WeCom admin console
  - Check that your domain is properly registered (ICP filing required for China)
  - Use HTTPS in production (WeChat/WeCom require secure connections)
  - Check logs for specific error codes (see troubleshooting guide below)

## Project layout (high level)

- `api/` – FastAPI backend
- `app/` – React + Vite frontend
- `tests/` – unit and E2E tests


## License

Licensed under the GNU Affero General Public License (AGPL). See [LICENSE](LICENSE.txt).

Copyright FalkorDB Ltd. 2025

