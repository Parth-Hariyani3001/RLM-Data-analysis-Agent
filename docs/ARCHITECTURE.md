# Architecture

This document describes the system design of **RLM Data Agent** — how components connect, where boundaries are drawn, and how data flows from upload to answer.

## Design principles

1. **The LLM never touches raw data.** All file access goes through `DataRuntime` → `AnalysisTools` → sandboxed REPL. The agent can only call approved async functions.
2. **Separation of transport, compute, and storage.** FastAPI handles HTTP/SSE; Celery handles ingestion; DuckDB handles analytical queries; PostgreSQL handles metadata and chat history.
3. **Streaming-first UX.** Agent steps are pushed over SSE so users see progress instead of waiting for a blocking response.
4. **User isolation.** Every query is scoped by `user_id` — datasets, jobs, sessions, and chat messages belong to one user.

---

## System overview

```mermaid
flowchart TB
    user(["Analyst"])
    rlm["RLM Data Agent<br/>Web app + API + agent"]
    llm["LLM Provider<br/>OpenAI-compatible API"]
    postgres["PostgreSQL<br/>Metadata and chat history"]
    redis["Redis<br/>Celery broker"]

    user -->|HTTPS| rlm
    rlm -->|Chat completions| llm
    rlm -->|CRUD via asyncpg| postgres
    rlm -->|Task queue| redis
```

---

## Layered architecture

```mermaid
flowchart LR
    subgraph Presentation
        direction TB
        P1[React SPA]
        P2[TanStack Query]
        P3[SSE Client]
    end

    subgraph Application
        direction TB
        A1[FastAPI Routers]
        A2[Services Layer]
        A3[Celery Workers]
    end

    subgraph Domain
        direction TB
        D1[RLM Engine]
        D2[Analysis Layer]
        D3[Data Runtime]
    end

    subgraph Infrastructure
        direction TB
        I1[PostgreSQL]
        I2[Redis]
        I3[File Storage]
        I4[DuckDB]
    end

    P1 --> A1
    A2 --> D1
    D3 --> I1
```

| Layer | Responsibility | Key modules |
|-------|---------------|-------------|
| **Presentation** | UI, routing, auth state, streaming consumption | `frontend/src/pages`, `hooks/useAgentStream.ts` |
| **Application** | HTTP contracts, orchestration, background jobs | `backend/api`, `backend/services`, `backend/workers` |
| **Domain** | Agent loop, analytics, query execution | `backend/rlm`, `backend/analysis`, `backend/data_runtime` |
| **Infrastructure** | Persistence, queues, files | PostgreSQL, Redis, `storage/datasets/` |

---

## Backend modules

```mermaid
flowchart TB
    subgraph api["api/v1"]
        health[health]
        auth[auth]
        datasets[datasets]
        chats[chats]
        agent[agent]
        jobs[jobs]
    end

    subgraph services["services"]
        auth_svc[auth]
        datasets_svc[datasets]
        chats_svc[chats]
        agent_svc[agent]
        ingestion[injestion]
    end

    subgraph rlm_pkg["rlm"]
        engine[RLMEngine]
        repl[RLMRepl]
        tools[ToolRegistry]
        provider[LLMProvider]
        prompts[prompts]
    end

    subgraph analysis_pkg["analysis"]
        analyzer[Analyzer]
        stats[StatisticsEngine]
        agg[AggregationEngine]
        anomaly[AnomalyDetector]
        quality[DataQualityAnalyzer]
        ts[TimeSeriesAnalyzer]
    end

    subgraph runtime_pkg["data_runtime"]
        dr[DataRuntime]
        duck[DuckDBEngine]
        csv[CSVSource]
        excel[ExcelSource]
        profiler[DatasetProfiler]
    end

    agent --> agent_svc
    datasets --> datasets_svc
    datasets --> ingestion
    agent_svc --> engine
    engine --> provider
    engine --> repl
    engine --> tools
    tools --> analyzer
    analyzer --> dr
    dr --> duck
    duck --> csv
    duck --> excel
    ingestion --> csv
    ingestion --> excel
```

### `api/v1` — HTTP surface

Thin routers that validate input, enforce auth, and delegate to services. The agent router is special: it returns a `StreamingResponse` with `text/event-stream` media type.

### `services` — orchestration

Business logic that composes domain objects. `run_agent()` is the key entry point:

1. Build a `DataRuntime` from the dataset file path
2. Wrap it in `AnalysisTools` + `ToolRegistry`
3. Create an `OpenAICompatibleProvider` from settings
4. Run `RLMEngine.run()` and always close the runtime in `finally`

### `rlm` — Recursive Language Model

The core agent loop:

```text
┌──────────────────────────────────────────────────────────┐
│                      RLMEngine.run()                     │
│                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────────────────┐ │
│  │ System  │    │  User   │    │ Assistant turns     │ │
│  │ prompt  │ +  │ question│ +  │ (code results, etc.)│ │
│  └─────────┘    └─────────┘    └─────────────────────┘ │
│                          │                               │
│                          ▼                               │
│                   LLMProvider.chat()                     │
│                          │                               │
│              ┌───────────┴───────────┐                   │
│              ▼                       ▼                   │
│         <code>...</code>      <final>...</final>       │
│              │                       │                   │
│              ▼                       └──► RLMResult     │
│         RLMRepl.exec()                                   │
│              │                                           │
│              ▼                                           │
│    ToolRegistry namespace                                │
│    (await profile_dataset(), etc.)                       │
└──────────────────────────────────────────────────────────┘
```

**`RLMRepl`** — Executes Python in a restricted namespace. Only registered tool callables and safe builtins are available. Output is truncated to prevent context explosion.

**`ToolRegistry`** — Binds `AnalysisTools` methods into the REPL namespace and records each tool invocation in a `RunCollector` for the run log.

**`RunCollector`** — Captures steps (LLM turns, code execution, tool calls, errors) for streaming and persistence.

### `analysis` — analytical domain

`Analyzer` is the high-level analysis facade over `DataRuntime`. It provides:

- Column-level statistics and full dataset analysis
- Filtering, aggregation, correlation
- Time series decomposition
- Anomaly detection (z-score, IQR)
- Data quality scoring

`AnalysisTools` exposes a curated subset of these capabilities to the RLM — the agent cannot run arbitrary SQL or access the filesystem.

### `data_runtime` — data access

Abstraction over data sources with a uniform interface:

```text
DataSource (ABC)
    ├── CSVSource      ──► DuckDB read_csv with encoding detection
    ├── ExcelSource    ──► DuckDB / pandas bridge
    └── DatabaseSource ──► (future) direct DB connections

DataRuntime
    ├── schema()       ──► column names, dtypes, row count
    ├── sample(n)      ──► preview rows
    ├── query(sql)     ──► read-only SQL with forbidden-keyword guard
    └── to_dataframe() ──► Pandas DataFrame for analysis layer
```

**DuckDB** is the execution engine — it handles large CSVs efficiently in-process without loading everything into memory upfront.

**Safety:** `DataRuntime.query()` rejects SQL containing `DROP`, `DELETE`, `INSERT`, `UPDATE`, and other mutating keywords.

---

## Frontend architecture

```mermaid
flowchart TB
    subgraph routes["React Router"]
        loginRoute["Login route"]
        dashRoute["Dashboard route"]
        datasetRoute["Dataset detail route"]
    end

    subgraph layout["Layout"]
        shell[AppShell]
        protected[ProtectedRoute]
    end

    subgraph pages["Pages"]
        dashboardPage[DashboardPage]
        datasetPage[DatasetPage]
        loginPage[LoginPage]
    end

    subgraph agent_ui["Agent UI"]
        chatPanel[ChatPanel]
        stepTimeline[StepTimeline]
        runLogsPanel[RunLogsPanel]
        codeBlock[CodeBlock]
    end

    subgraph data_hooks["Data Hooks"]
        hookAuth[useAuth]
        hookDatasets[useDatasets]
        hookJobs[useJobs]
        hookChatSessions[useChatSessions]
        hookAgentStream[useAgentStream]
    end

    subgraph api_client["API Client"]
        authApi[auth client]
        datasetsApi[datasets client]
        chatsApi[chats client]
        apiClient[client.ts]
    end

    askApi["POST /ask SSE"]

    dashRoute --> protected
    protected --> shell
    shell --> dashboardPage
    datasetPage --> chatPanel
    dashboardPage --> hookDatasets
    datasetPage --> hookAgentStream
    hookAgentStream -->|SSE| askApi
    hookDatasets --> datasetsApi
    hookAuth --> authApi
    datasetsApi --> apiClient
    authApi --> apiClient
```

### Streaming agent responses

`useAgentStream` consumes the SSE endpoint:

```text
POST /api/v1/datasets/{id}/ask
Content-Type: application/json
Authorization: Bearer <token>

{"question": "...", "session_id": "..."}

─── response (text/event-stream) ───

data: {"event":"step","type":"code","content":"...","iteration":1}
data: {"event":"step","type":"repl_output","content":"...","iteration":1}
data: {"event":"final","answer":"...","iterations":3,"usage":{...}}
```

The hook parses each `data:` line, updates local step state for the timeline, and commits the final answer to the chat panel.

### State management

- **TanStack Query** — server state (datasets, jobs, chat sessions) with caching and refetch
- **Local React state** — streaming steps, upload progress, UI toggles
- **localStorage** — JWT token via `lib/auth.ts`

---

## Data flow

### Upload & ingestion

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Storage
    participant DB as PostgreSQL
    participant Celery
    participant Ingestion

    User->>Frontend: Drop CSV/XLSX
    Frontend->>API: POST /datasets (multipart)
    API->>Storage: Write file to storage/datasets/
    API->>DB: Create Dataset pending and Job
    API->>Celery: inspect_dataset_task.delay()
    API-->>Frontend: Return dataset and job

    Celery->>Ingestion: inspect_dataset(type, path)
    Ingestion->>Ingestion: Detect encoding, infer schema
    Ingestion->>DB: Update row_count, column_count, schema, status=ready
    Ingestion->>DB: Job status=completed

    Frontend->>API: GET /jobs/id poll
    Frontend-->>User: Show schema + enable chat
```

### Ask question

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Engine as RLMEngine
    participant DB

    User->>Frontend: Type question
    Frontend->>API: POST /datasets/id/ask SSE
    API->>DB: Get/create chat session

    loop Agent iterations
        API->>Engine: run(question, on_step)
        Engine-->>API: step callback
        API-->>Frontend: SSE step event
    end

    Engine-->>API: RLMResult
    API->>DB: persist_turn(session, question, result)
    API-->>Frontend: SSE final event
```

---

## Database schema

```mermaid
erDiagram
    users ||--o{ datasets : owns
    users ||--o{ jobs : owns
    datasets ||--o{ chat_sessions : has
    chat_sessions ||--o{ chat_messages : contains
    chat_sessions ||--o{ chat_run_logs : stores

    users {
        uuid id PK
        string username
        string password_hash
        string full_name
        timestamp created_at
    }

    datasets {
        uuid id PK
        uuid user_id FK
        string name
        enum source_type
        enum status
        text file_path
        bigint row_count
        int column_count
        jsonb dataset_schema
        text error_message
    }

    jobs {
        uuid id PK
        uuid user_id FK
        enum type
        enum status
        string celery_task_id
        float progress
    }

    chat_sessions {
        uuid id PK
        uuid dataset_id FK
        uuid user_id FK
        string title
        timestamp created_at
    }

    chat_messages {
        uuid id PK
        uuid session_id FK
        enum role
        text content
    }

    chat_run_logs {
        uuid id PK
        uuid session_id FK
        jsonb steps
        jsonb usage
        int iterations
    }
```

---

## Security model

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT bearer tokens, bcrypt password hashing |
| Authorization | All dataset/chat endpoints filter by `current_user.id` |
| Agent sandbox | REPL namespace limited to registered tools; no file I/O |
| SQL safety | Read-only queries; forbidden keyword blocklist |
| Upload limits | Configurable max file size (default 500 MB); extension allowlist |
| CORS | Configurable origins (default `http://localhost:5173`) |

Secrets (`JWT_SECRET_KEY`, `LLM_API_KEY`, `DATABASE_URL`) are loaded from `backend/.env` via Pydantic Settings and never committed to the repository.

---

## Analytical tools available to the agent

The LLM can call these functions inside the REPL (all async):

| Tool | Purpose |
|------|---------|
| `profile_dataset()` | High-level column profiles |
| `get_columns()` | Column names and dtypes |
| `count()` | Total row count |
| `sample(n)` | Random sample rows |
| `value_counts(column)` | Top value frequencies |
| `describe()` | Statistical summary of all columns |
| `describe_column(column)` | Detailed stats for one column |
| `filter_rows(expression)` | Filter with pandas-style expressions |
| `analyze()` | Full column-by-column analysis |
| `quality_report()` | Data quality assessment |
| `correlation(method)` | Correlation matrix |
| `percentiles(column, values)` | Percentile calculations |
| `aggregate(group_by, aggregations)` | Group-by aggregations |
| `timeseries(date_col, value_col)` | Time series analysis |
| `detect_anomalies(column)` | Z-score or IQR anomaly detection |

---

## Extension points

| Area | How to extend |
|------|--------------|
| New file formats | Implement `DataSource` + register in `factory.py` |
| New analysis | Add method to `Analyzer`, expose via `AnalysisTools`, document in `prompts.py` |
| New LLM provider | Implement `LLMProvider` protocol |
| Database sources | Extend `DatabaseSource` in `data_runtime/sources/` |
| Background jobs | Add Celery task in `workers/tasks/` |

---

## Observability

- **structlog** — structured JSON logging across API and workers
- **RunCollector** — per-agent-run step log persisted to `chat_run_logs`
- **OpenTelemetry** — API dependencies included; instrumentation can be wired in `main.py`

---

## Related docs

- [Getting Started](GETTING_STARTED.md) — run the full stack locally
- [README](../README.md) — project overview and quick reference
