# Architecture

GraphMind is a document question-answering product. The MVP uses normal retrieval-augmented generation (RAG); keyword and knowledge-graph retrieval are later enhancements.

## Service boundaries

The API follows `router -> service -> adapter -> database`. Routers validate HTTP input and delegate to services. Services own product workflows. Adapters isolate external providers and persistence. Database access belongs behind adapters.

All language-model requests go through `apps/api/app/adapters/llm.py`; all embedding requests go through `apps/api/app/adapters/embeddings.py`. Model identifiers are configuration, not source-code constants. Validate user input and model output before use.

## Data isolation and document trust

Every persisted user-owned row includes `user_id`; database queries enforce ownership and Supabase Row Level Security protects tables. Graph queries must also include `user_id`, because Neo4j does not provide Postgres-style row-level security.

Retrieved document text is untrusted data. It is context for answering, never instructions to follow. Do not log full documents or full prompts. Deleting a document must remove its stored content and derived vectors and graph data.

## Runtime behavior

FastAPI exposes public `/health` and `/ready` endpoints. Each API request receives a server-generated trace ID returned in `X-Trace-ID` and included in structured JSON logs. CORS origins are configured explicitly. AI-backed routes must return `503` without invoking a model when `AI_ENABLED=false`.

The web application is a Next.js App Router application. It must not contain service-role keys or other server secrets.

## Roadmap

1. Foundation: monorepo, configuration, health endpoints, logs, and CI.
2. Ingestion and vector retrieval: parse, chunk, embed, persist, and delete documents.
3. Chat and citations: retrieve evidence, stream validated cited answers, and provide the user interface.
4. Authentication and evaluation baseline: wire Supabase Auth, prove isolation, and measure vector-only quality.
5. Knowledge graph and hybrid retrieval: extract entities, combine retrieval modes, and compare results.
6. Hardening and launch: rate limits, security verification, observability, deployment, and operator documentation.
