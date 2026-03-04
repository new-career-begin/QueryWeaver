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

## Internationalization (i18n)

QueryWeaver supports multiple languages to provide a localized experience for users worldwide.

### Supported Languages

- **简体中文 (Simplified Chinese)** - Default language
- **English** - Full English translation

### Language Switching

Users can easily switch between languages using the language switcher in the application header:

1. Click the **globe icon** (🌐) in the top-right corner of the application
2. Select your preferred language from the dropdown menu
3. The interface will immediately update to display content in the selected language
4. Your language preference is automatically saved and will be remembered on your next visit

### Features

- **Complete UI Translation**: All user-facing text, buttons, labels, and messages are translated
- **Localized Formatting**: Dates, times, and numbers are formatted according to language conventions
  - Chinese: Uses "年月日" format and 24-hour time
  - English: Uses standard date formats and 12/24-hour time based on locale
- **Error Messages**: All error messages and notifications are displayed in the selected language
- **Accessibility**: ARIA labels and screen reader text are fully localized
- **Browser Language Detection**: Automatically detects and uses your browser's language preference on first visit
- **Persistent Preference**: Your language choice is saved locally and persists across sessions

### For Developers

If you're contributing translations or adding new languages, please refer to:
- [Localization Development Guide](docs/i18n-development-guide.md) - How to add and maintain translations
- [Translation Contribution Guide](docs/i18n-contribution-guide.md) - Translation quality standards and review process

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

LLM Configuration endpoints (🆕)
- GET /api/config/llm — get user's LLM configuration
- POST /api/config/llm — save user's LLM configuration
- DELETE /api/config/llm — delete user's LLM configuration
- POST /api/config/llm/test — test LLM provider connection

Authentication
- Add an Authorization header: `Authorization: Bearer <API_TOKEN>`

### Using DeepSeek via API

You can configure DeepSeek as your LLM provider through the API:

#### 1. Save DeepSeek Configuration

```bash
curl -X POST https://app.queryweaver.ai/api/config/llm \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "completion_model": "deepseek-chat",
    "embedding_model": "text-embedding-ada-002",
    "api_key": "sk-xxxxxxxxxxxxx",
    "base_url": "https://api.deepseek.com",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }'
```

#### 2. Test DeepSeek Connection

```bash
curl -X POST https://app.queryweaver.ai/api/config/llm/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "deepseek",
    "api_key": "sk-xxxxxxxxxxxxx",
    "base_url": "https://api.deepseek.com"
  }'
```

#### 3. Get Current Configuration

```bash
curl -X GET https://app.queryweaver.ai/api/config/llm \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. Query with DeepSeek

Once configured, all Text2SQL queries will automatically use DeepSeek:

```bash
curl -X POST https://app.queryweaver.ai/graphs/my_database \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat": ["查询用户表的前10条记录"]
  }'
```

The system will use your DeepSeek configuration for SQL generation.

### Examples

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

QueryWeaver uses AI models for Text2SQL conversion and supports multiple LLM providers: Azure OpenAI, OpenAI, and DeepSeek.

#### Supported LLM Providers

QueryWeaver supports three LLM providers with automatic configuration:

1. **Azure OpenAI** (Default)
2. **OpenAI** (Direct API)
3. **DeepSeek** (Cost-effective Chinese LLM) - 🆕

#### Option 1: Azure OpenAI (Default)

By default, QueryWeaver is configured to use Azure OpenAI. You need to set all three Azure credentials:

```bash
AZURE_API_KEY=your_azure_api_key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-12-01-preview
```

#### Option 2: OpenAI directly

To use OpenAI directly instead of Azure, simply set the `OPENAI_API_KEY` environment variable:

```bash
OPENAI_API_KEY=your_openai_api_key
```

When `OPENAI_API_KEY` is provided, QueryWeaver automatically switches to use OpenAI's models:
- Embedding model: `openai/text-embedding-ada-002`
- Completion model: `openai/gpt-4.1`

#### Option 3: DeepSeek (Recommended for cost-effectiveness) 🆕

DeepSeek is a high-performance, cost-effective Chinese LLM provider with OpenAI-compatible APIs. It offers:
- **90% lower cost** compared to OpenAI
- **High performance** for Chinese and English queries
- **OpenAI-compatible API** for easy integration
- **国产化支持** - 支持国产化部署需求

##### Getting DeepSeek API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com/)
2. Register an account (支持中国手机号注册)
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

##### Configuration via Environment Variables

```bash
# DeepSeek API credentials
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com  # Optional, uses default if not set

# Optional: specify models (uses defaults if not set)
DEEPSEEK_COMPLETION_MODEL=deepseek-chat
DEEPSEEK_EMBEDDING_MODEL=text-embedding-ada-002
```

##### Configuration via Web UI (Recommended)

After logging in, you can configure DeepSeek through the web interface:

1. Navigate to **Settings** → **AI Model Configuration**
2. Select **DeepSeek** as the provider
3. Enter your API Key
4. Choose your preferred models:
   - **Completion Model**: `deepseek-chat` (general) or `deepseek-coder` (code-focused)
   - **Embedding Model**: `text-embedding-ada-002`
5. Click **Test Connection** to verify
6. Click **Save** to apply the configuration

The configuration is stored securely (encrypted) in FalkorDB and takes precedence over environment variables.

##### Available DeepSeek Models

**Completion Models:**
- `deepseek-chat` - General-purpose conversational model (recommended)
- `deepseek-coder` - Optimized for code generation and technical queries

**Embedding Models:**
- Currently uses OpenAI's `text-embedding-ada-002` (DeepSeek's embedding model coming soon)

##### Configuration Priority

QueryWeaver loads LLM configuration in the following priority order:

1. **User Configuration** (highest) - Set via web UI, stored in FalkorDB
2. **Environment Variables** - Set in `.env` or system environment
3. **System Defaults** (lowest) - Fallback to Azure OpenAI

This allows per-user model selection while maintaining system-wide defaults.

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

Using DeepSeek:
```bash
docker run -p 5000:5000 -it \
  -e FASTAPI_SECRET_KEY=your_secret_key \
  -e DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx \
  -e DEEPSEEK_BASE_URL=https://api.deepseek.com \
  falkordb/queryweaver
```

#### Encryption Key for Secure Storage

When using the web UI to configure LLM providers, API keys are encrypted before storage. Set an encryption key:

```bash
# Generate a secure encryption key (32 bytes, base64 encoded)
LLM_CONFIG_ENCRYPTION_KEY=your-32-byte-base64-encoded-key
```

If not set, a default key will be generated (not recommended for production).

#### Switching Between Providers

You can switch between providers at any time:

- **System-wide**: Change environment variables and restart the application
- **Per-user**: Use the web UI to configure your preferred provider (no restart needed)

For detailed configuration guides and troubleshooting, see [docs/deepseek-setup.md](docs/deepseek-setup.md).

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

