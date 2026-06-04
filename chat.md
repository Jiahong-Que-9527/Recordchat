给我和我的agent写一下recordchat项目的详细实现步骤

我会把它写成两层：先给你一个“项目实现路线图”，再给你一段可以直接交给 coding agent 执行的任务说明。重点不是做一个普通 chat app，而是做成你未来 ALH / ONE Record 叙事里的第一个可展示入口。

Thought for a few seconds

Bill，这个项目非常值得做，而且对你 2026 找 100k+ 数据/AI平台岗位有帮助。原因很简单：RecordChat 不是普通 chatbot，它可以成为你展示下面三种能力的入口：

Domain-specific AI Agent 能力：不是玩通用 LLM，而是围绕 IATA ONE Record 做专业问答、标准解释、数据建模辅助。
AviationLakehouse / ONE Record 叙事入口：以后 ALH、RecordForge、ONE Record Server 都可以通过 RecordChat 被解释、查询、调试。
平台 owner 思维：你不是做一个 demo，而是在做一个“行业标准知识层 + Agent Interface + 后续平台能力入口”。

更高一层看，RecordChat 应该是你的 Aviation AI Interface Layer，未来可以变成：

ONE Record / Air Cargo domain 的智能解释器、开发助手、数据建模助手、合规/语义查询入口。

1. RecordChat 项目定位
一句话定位

RecordChat 是一个面向 IATA ONE Record 的 domain-specific AI assistant，用于理解 ONE Record 标准、解释数据模型、辅助开发者构建 ONE Record Server / API / JSON-LD payload，并未来连接 AviationLakehouse 和 RecordForge。

不要把它做成“上传 PDF 问答”的小工具。那样太低级。

你要把它设计成：

ONE Record Knowledge Base
        ↓
RAG / Agent Layer
        ↓
RecordChat UI / API
        ↓
Developer / Researcher / Air Cargo Operator

未来演进：

RecordChat
  ├── ONE Record Q&A
  ├── JSON-LD payload assistant
  ├── API endpoint explainer
  ├── ontology / class relationship explorer
  ├── RecordForge test data generator
  └── ALH semantic query assistant
2. MVP 目标

RecordChat v0.1 不要贪多。先完成一个可以展示的 MVP：

v0.1 核心功能

用户可以问：

What is a Piece in ONE Record?
How is Shipment related to Piece?
How do I create a ONE Record LogisticsObject?
What is the difference between Waybill and Shipment?
Generate an example JSON-LD payload for a Piece.
Explain the ONE Record API flow.

系统应该返回：

简洁解释
引用来源
相关 ONE Record 类 / 属性
可选 JSON-LD 示例
开发建议
3. 推荐技术栈

我建议你先用一个非常务实的栈。

Backend
Python
FastAPI
LangChain or LlamaIndex
Qdrant or Chroma
PostgreSQL optional
LLM

第一阶段可以用：

Qwen API
OpenAI API
Claude API

你之前问过能不能用 Qwen API。可以。对于 RecordChat，Qwen 很适合作为低成本主力模型。

建议策略：

Dev / low-cost:
Qwen API

High-quality fallback:
OpenAI / Claude

Local experiment:
Ollama + Qwen2.5 / Qwen3
Frontend

简单一点：

Next.js
Tailwind CSS
shadcn/ui

或者更快：

Streamlit

但如果你想做 portfolio，我更建议：

FastAPI backend + Next.js frontend

这更像一个真实产品，不像研究 demo。

Vector DB

MVP 用：

Chroma

稍微正式一点用：

Qdrant

我建议你用 Qdrant，因为更像生产系统，也更适合 portfolio 叙事。

4. 项目结构建议
recordchat/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── ingest.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── llm.py
│   │   │   ├── embeddings.py
│   │   │   └── logging.py
│   │   ├── rag/
│   │   │   ├── loader.py
│   │   │   ├── chunker.py
│   │   │   ├── retriever.py
│   │   │   ├── reranker.py
│   │   │   ├── prompt.py
│   │   │   └── pipeline.py
│   │   ├── domain/
│   │   │   ├── one_record_schema.py
│   │   │   ├── jsonld_generator.py
│   │   │   └── glossary.py
│   │   └── models/
│   │       ├── chat.py
│   │       └── source.py
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── data/
│   ├── raw/
│   ├── processed/
│   └── index/
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── adr/
│   └── demo_script.md
└── scripts/
    ├── ingest_docs.py
    ├── evaluate_rag.py
    └── reset_index.py
5. 实现阶段路线图
Phase 0：项目初始化

目标：让项目像一个真实工程，而不是 notebook demo。

任务

创建 repo：

recordchat

初始化：

README.md
.env.example
docker-compose.yml
backend/
frontend/
data/
docs/
scripts/

README 先写清楚：

What is RecordChat?
Why ONE Record?
Architecture
Quickstart
Roadmap

README 的定位可以这样写：

RecordChat is a domain-specific AI assistant for IATA ONE Record. It helps developers and logistics stakeholders understand the ONE Record data model, API concepts, JSON-LD payloads, and semantic relationships.
Phase 1：收集 ONE Record 知识资料

目标：建立 RecordChat 的知识底座。

数据来源

先不要太复杂。你需要收集：

IATA ONE Record documentation
ONE Record data model
ONE Record API specification
ONE Record ontology / vocabulary
JSON-LD examples
GitHub examples if available

数据放在：

data/raw/

建议结构：

data/raw/
├── one_record_docs/
├── api_specs/
├── ontology/
├── examples/
└── notes/

每个文档都要保留 metadata：

{
  "source": "IATA ONE Record API Specification",
  "version": "x.x",
  "url": "...",
  "document_type": "api_spec",
  "domain": "one_record",
  "ingested_at": "..."
}

这一步非常关键。因为 RecordChat 的可信度来自 source grounding，不是来自 LLM 胡说。

Phase 2：文档解析与 chunking

目标：把资料变成可检索知识块。

不要简单按固定长度切

普通 RAG 最大的问题是 chunking 太粗糙。你这里要做 domain-aware chunking。

建议 chunk 类型：

Concept chunk
API endpoint chunk
Class definition chunk
Property definition chunk
Example payload chunk
Glossary chunk

例如：

Chunk type: ClassDefinition
Entity: Piece
Source: ONE Record Data Model
Content: ...
Related entities: Shipment, LogisticsObject, TransportMovement
chunk metadata

每个 chunk 至少包含：

{
  "chunk_id": "...",
  "source_name": "...",
  "source_url": "...",
  "version": "...",
  "section_title": "...",
  "chunk_type": "class_definition",
  "entity": "Piece",
  "related_entities": ["Shipment", "LogisticsObject"],
  "content": "..."
}

这会让你的 RAG 显得很高级。

Phase 3：Embedding 与 Vector Store

目标：把 chunk 写入 Qdrant。

推荐 collection
recordchat_one_record_docs
embedding model

可以先用：

text-embedding-3-small

或者 Qwen embedding：

text-embedding-v4 / qwen embedding model

如果你想保持中国模型生态，也可以走：

Qwen embedding + Qwen chat
Qdrant payload

Qdrant payload 里要放：

{
  "source_name": "...",
  "source_url": "...",
  "version": "...",
  "chunk_type": "...",
  "entity": "...",
  "section_title": "..."
}

这样回答时可以展示 citations。

Phase 4：基础 RAG Pipeline

目标：用户提问后，可以检索相关文档并回答。

流程
User Query
   ↓
Query classification
   ↓
Retrieve top-k chunks from Qdrant
   ↓
Optional reranking
   ↓
Prompt assembly
   ↓
LLM response
   ↓
Return answer + citations
Query classification

先做简单分类：

concept_explanation
api_question
jsonld_generation
relationship_question
debugging_question
general_question

例如：

if "generate" in query and "JSON-LD" in query:
    query_type = "jsonld_generation"

后面可以换成 LLM classifier。

Phase 5：Prompt 设计

这是 RecordChat 的灵魂。

System Prompt 核心原则
You are RecordChat, a domain-specific AI assistant for IATA ONE Record.

You help users understand:
- ONE Record concepts
- ONE Record data model
- JSON-LD structures
- API flows
- logistics object relationships
- implementation patterns

Rules:
1. Use the retrieved context as the primary source of truth.
2. If the answer is not supported by the retrieved context, say so clearly.
3. Always distinguish between official ONE Record concepts and your own implementation suggestions.
4. When generating JSON-LD examples, mark them as illustrative unless directly copied from official documentation.
5. Prefer concise, developer-friendly answers.
6. Always include relevant sources when available.
回答格式
Answer
Sources
Related ONE Record concepts
Example / Implementation note

例如：

Answer:
A Piece represents ...

Sources:
- ONE Record Data Model, section ...

Related concepts:
- Shipment
- LogisticsObject
- Waybill

Implementation note:
In a ONE Record Server, Piece would usually be represented as a LogisticsObject with ...
Phase 6：JSON-LD Generator

这是你区别于普通 RAG Chatbot 的第一个亮点。

用户问：

Generate a JSON-LD example for a Piece.

系统返回：

{
  "@context": "...",
  "@type": "Piece",
  "@id": "...",
  ...
}

但是要注意：不能让模型乱造。你应该做成半模板化。

实现方式

建立：

backend/app/domain/jsonld_generator.py

支持：

generate_piece_example()
generate_shipment_example()
generate_waybill_example()
generate_transport_movement_example()

每个函数返回一个基础 JSON-LD skeleton。

然后 LLM 负责解释，不负责裸生成全部结构。

这样更稳定。

Phase 7：Relationship Explorer

这是第二个亮点。

用户问：

How is Shipment related to Piece?

系统应该能够返回：

Shipment
  └── contains / refers to Piece
Piece
  └── belongs to Shipment

你可以先用静态关系表：

ONE_RECORD_RELATIONSHIPS = {
    "Shipment": ["Piece", "Waybill", "LogisticsEvent"],
    "Piece": ["Shipment", "LogisticsObject", "TransportMovement"],
}

后面再从 ontology 自动解析。

v0.1 不要追求完美 ontology parser，先手写核心关系。

Phase 8：API Explainer

用户问：

How does ONE Record API work?
How do I create a LogisticsObject?
How does subscription work?

系统应该返回：

Conceptual explanation
Endpoint flow
Pseudo request
Implementation note

例如：

1. Create a LogisticsObject
2. Assign URI / ID
3. Expose it through the ONE Record Server
4. Allow other parties to access it through standard API
5. Use linked data references to connect it with related logistics objects

后续可以支持 OpenAPI spec-based retrieval。

Phase 9：Frontend UI

MVP UI 不要复杂。

页面布局
Left sidebar:
- New Chat
- Example Questions
- ONE Record Concepts
- JSON-LD Generator
- Sources

Main area:
- Chat messages
- Source citations
- JSON viewer for structured output
推荐 example questions
What is ONE Record?
What is a LogisticsObject?
Explain the relationship between Shipment and Piece.
Generate a JSON-LD example for a Piece.
How does ONE Record support data sharing?
What is the role of JSON-LD in ONE Record?

这个对 portfolio 很重要。别人打开项目，不需要猜怎么用。

Phase 10：Evaluation

你必须做一个小型 eval。否则它只是玩具。

建立：

data/eval/questions.yaml

示例：

- id: q001
  question: "What is a LogisticsObject in ONE Record?"
  expected_keywords:
    - LogisticsObject
    - data sharing
    - linked data
  category: concept

- id: q002
  question: "Generate a JSON-LD example for a Piece."
  expected_keywords:
    - "@context"
    - "@type"
    - Piece
  category: jsonld

写脚本：

scripts/evaluate_rag.py

评估：

retrieval hit rate
source coverage
answer groundedness
JSON validity

这个会让 RecordChat 从 demo 变成“工程项目”。

6. v0.1 验收标准

你的 agent 应该以这个作为完成标准。

Backend
[ ] FastAPI service can start
[ ] /health endpoint works
[ ] /chat endpoint works
[ ] /ingest endpoint or script works
[ ] Qdrant can store and retrieve chunks
[ ] LLM response includes citations
[ ] JSON-LD generation works for at least Piece and Shipment
Frontend
[ ] User can ask questions
[ ] Answers are displayed clearly
[ ] Sources are shown
[ ] JSON-LD output is formatted
[ ] Example questions are clickable
Documentation
[ ] README has quickstart
[ ] Architecture doc exists
[ ] Demo script exists
[ ] Roadmap exists
Demo

用户打开后能演示这 5 个问题：

1. What is ONE Record?
2. What is a LogisticsObject?
3. Explain Shipment vs Piece.
4. Generate a JSON-LD example for a Piece.
5. How could ONE Record data be connected to an AviationLakehouse?
7. v0.2 路线

v0.1 做完后，不要马上重构。v0.2 加三个东西：

v0.2.1 Ontology-aware Retrieval

从 ontology 里提取：

classes
properties
relationships
definitions

让 retrieval 支持：

entity-first search

例如用户问 Piece，系统先知道 Piece 是一个 ONE Record entity，然后优先检索 Piece 相关 chunk。

v0.2.2 RecordForge Integration

RecordForge 是生成 synthetic ONE Record data 的工具。

RecordChat 可以调用它：

User: Generate 5 synthetic shipments with pieces and transport events.
RecordChat → RecordForge → JSON-LD output

这时你就形成了：

RecordChat = interface
RecordForge = synthetic data engine
ONE Record Server = standard exchange layer
ALH = analytical backend

这是完整平台叙事。

v0.2.3 ALH Integration

让用户问：

How would this ONE Record object land in AviationLakehouse?

系统回答：

ONE Record Server object
  ↓
Bronze: raw JSON-LD landing
  ↓
Silver: normalized logistics entities
  ↓
Gold: analytics-ready shipment movement facts

这会直接服务你的 ALH 战略。

8. v0.3 路线

v0.3 开始做成真正有架构感的项目：

Authentication
User sessions
Conversation memory
Source versioning
OpenTelemetry
Evaluation dashboard
Admin ingestion UI
ONE Record Server connector
RecordForge connector
ALH connector

这时你可以在 LinkedIn 上写：

I started RecordChat as a small ONE Record RAG assistant, but I am evolving it into an intelligent interface layer for federated aviation data platforms.

这句话比“我做了一个 chatbot”强太多。

9. 给 coding agent 的完整任务说明

下面这段你可以直接复制给 Codex / Claude Code。

Agent Task: Build RecordChat v0.1

You are building RecordChat, a domain-specific AI assistant for IATA ONE Record.

The goal is to create a production-minded MVP, not a toy chatbot. RecordChat should help users understand ONE Record concepts, data model relationships, API concepts, and JSON-LD examples. It should use retrieval-augmented generation with source citations.

Product Positioning

RecordChat is the first interface layer for a future aviation data platform ecosystem:

RecordChat = AI interface for ONE Record knowledge
RecordForge = synthetic ONE Record data generator
ONE Record Server = standardized data exchange layer
AviationLakehouse = analytical backend

The v0.1 goal is to build a working RAG-based ONE Record assistant with a clean backend, minimal frontend, source-grounded answers, and JSON-LD example generation.

Required Tech Stack

Use:

Backend: Python + FastAPI
Vector DB: Qdrant
LLM provider: configurable through environment variables
Frontend: Next.js + Tailwind + shadcn/ui
Containerization: Docker Compose

The LLM provider should be abstracted so that I can switch between:

Qwen API
OpenAI API
Claude API
Local Ollama later

Do not hardcode one provider deeply into the application.

Repository Structure

Create this structure:

recordchat/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── ingest.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── llm.py
│   │   │   ├── embeddings.py
│   │   │   └── logging.py
│   │   ├── rag/
│   │   │   ├── loader.py
│   │   │   ├── chunker.py
│   │   │   ├── retriever.py
│   │   │   ├── prompt.py
│   │   │   └── pipeline.py
│   │   ├── domain/
│   │   │   ├── one_record_schema.py
│   │   │   ├── jsonld_generator.py
│   │   │   └── glossary.py
│   │   └── models/
│   │       ├── chat.py
│   │       └── source.py
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── data/
│   ├── raw/
│   ├── processed/
│   └── index/
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── demo_script.md
│   └── adr/
└── scripts/
    ├── ingest_docs.py
    ├── evaluate_rag.py
    └── reset_index.py
Backend Requirements

Implement FastAPI backend with these endpoints:

GET /health
POST /chat
POST /ingest
/health

Return:

{
  "status": "ok",
  "service": "recordchat-backend"
}
/chat

Request:

{
  "message": "What is a Piece in ONE Record?",
  "conversation_id": "optional-id"
}

Response:

{
  "answer": "...",
  "sources": [
    {
      "source_name": "...",
      "section_title": "...",
      "source_url": "...",
      "chunk_id": "..."
    }
  ],
  "related_concepts": ["Piece", "Shipment", "LogisticsObject"],
  "structured_output": null
}

For JSON-LD generation questions, response should include:

{
  "structured_output": {
    "@context": "...",
    "@type": "Piece",
    "@id": "..."
  }
}
/ingest

For v0.1, this can trigger ingestion from:

data/raw/

It should:

load documents
chunk documents
create embeddings
store chunks in Qdrant
preserve metadata
RAG Requirements

Implement a basic RAG pipeline:

User Query
  → classify query type
  → retrieve top-k chunks from Qdrant
  → build prompt
  → call LLM
  → return answer with citations

Query types:

concept_explanation
relationship_question
api_question
jsonld_generation
general_question

The retrieval result must include metadata:

{
  "chunk_id": "...",
  "source_name": "...",
  "source_url": "...",
  "section_title": "...",
  "chunk_type": "...",
  "entity": "...",
  "content": "..."
}
Chunking Requirements

Do not only use naive fixed-size chunking.

Implement a chunking strategy that tries to preserve semantic sections.

Each chunk should have:

{
  "chunk_id": "...",
  "content": "...",
  "metadata": {
    "source_name": "...",
    "source_url": "...",
    "version": "...",
    "section_title": "...",
    "chunk_type": "concept | api | class_definition | property_definition | example | general",
    "entity": "optional entity name",
    "related_entities": []
  }
}

For v0.1, heuristic chunking is acceptable.

Prompt Requirements

Use this system prompt:

You are RecordChat, a domain-specific AI assistant for IATA ONE Record.

You help users understand:
- ONE Record concepts
- ONE Record data model
- JSON-LD structures
- API flows
- logistics object relationships
- implementation patterns

Rules:
1. Use the retrieved context as the primary source of truth.
2. If the answer is not supported by the retrieved context, say so clearly.
3. Distinguish official ONE Record concepts from implementation suggestions.
4. When generating JSON-LD examples, mark them as illustrative unless directly copied from official documentation.
5. Prefer concise, developer-friendly answers.
6. Always include relevant sources when available.

The answer should follow this structure:

Answer:
...

Related concepts:
...

Implementation note:
...

Sources:
...
Domain Layer Requirements

Create:

backend/app/domain/jsonld_generator.py

Implement at least:

generate_piece_example()
generate_shipment_example()

These functions should return valid JSON dictionaries.

Also create:

backend/app/domain/one_record_schema.py

Add a small manually curated relationship map:

ONE_RECORD_RELATIONSHIPS = {
    "Shipment": ["Piece", "Waybill", "LogisticsObject"],
    "Piece": ["Shipment", "LogisticsObject", "LogisticsEvent"],
    "Waybill": ["Shipment"],
    "LogisticsObject": ["Piece", "Shipment", "Waybill"]
}

Use this map to enrich answers for relationship questions.

Frontend Requirements

Build a minimal but clean Next.js frontend.

Page layout:

Left sidebar:
- New Chat
- Example Questions
- ONE Record Concepts
- JSON-LD Generator

Main:
- Chat messages
- Source citations
- JSON-LD viewer if structured output exists

Example questions:

What is ONE Record?
What is a LogisticsObject?
Explain the relationship between Shipment and Piece.
Generate a JSON-LD example for a Piece.
How does ONE Record support data sharing?
What is the role of JSON-LD in ONE Record?

Requirements:

[ ] User can send a message
[ ] Answer is displayed
[ ] Sources are displayed
[ ] JSON-LD is formatted as code block
[ ] Example questions are clickable
Docker Compose Requirements

Create a docker-compose.yml with:

backend
frontend
qdrant

Optional:

postgres

MVP can avoid Postgres unless needed.

Evaluation Requirements

Create:

data/eval/questions.yaml
scripts/evaluate_rag.py

The evaluation file should include at least 10 questions:

concept questions
relationship questions
api questions
jsonld generation questions

The evaluation script should check:

retrieval results exist
sources are returned
answer is not empty
JSON-LD output is valid JSON when expected
expected keywords appear in the answer
Documentation Requirements

Create:

docs/architecture.md
docs/roadmap.md
docs/demo_script.md
architecture.md

Must explain:

RecordChat architecture
RAG pipeline
Vector store
LLM abstraction
Domain layer
Future integration with RecordForge and AviationLakehouse
roadmap.md

Include:

v0.1: ONE Record RAG assistant
v0.2: ontology-aware retrieval + RecordForge integration
v0.3: ALH integration + ONE Record Server connector
demo_script.md

Include 5 demo questions:

1. What is ONE Record?
2. What is a LogisticsObject?
3. Explain Shipment vs Piece.
4. Generate a JSON-LD example for a Piece.
5. How could ONE Record data be connected to an AviationLakehouse?
Acceptance Criteria

The project is complete when:

[ ] docker compose up starts backend, frontend, and Qdrant
[ ] /health works
[ ] documents from data/raw can be ingested
[ ] /chat returns grounded answers
[ ] answers include source citations
[ ] JSON-LD generation works for Piece and Shipment
[ ] frontend can send messages and display answers
[ ] source citations are visible in UI
[ ] README includes quickstart
[ ] architecture.md, roadmap.md, and demo_script.md exist
[ ] at least 10 evaluation questions exist
[ ] evaluation script runs
10. 推荐开发顺序

你的 agent 应该按这个顺序做，不要乱跳：

Step 1: Create repo structure
Step 2: Implement FastAPI skeleton
Step 3: Add Qdrant docker-compose
Step 4: Implement config and environment variables
Step 5: Implement document loader
Step 6: Implement chunker
Step 7: Implement embedding abstraction
Step 8: Implement Qdrant retriever
Step 9: Implement LLM abstraction
Step 10: Implement RAG pipeline
Step 11: Implement /chat endpoint
Step 12: Implement JSON-LD generator
Step 13: Implement relationship map
Step 14: Implement frontend chat UI
Step 15: Add example questions
Step 16: Add source display
Step 17: Add evaluation script
Step 18: Add docs
Step 19: Test full docker compose flow
Step 20: Polish README and demo script
11. 最重要的架构边界

你要提醒 agent：不要把 RecordChat 做成一坨 LangChain demo。

必须保持这些边界：

LLM provider abstraction
Embedding provider abstraction
Retriever abstraction
Domain logic separate from RAG
JSON-LD generator separate from free-form LLM
Frontend separate from backend
Docs and evaluation included from day one

也就是说：

错误做法：
chat.py 里面直接写 prompt + call model + parse result + generate JSON

正确做法：
chat.py → pipeline.py → retriever.py / prompt.py / llm.py / domain tools

这就是 platform engineer 和 demo builder 的区别。

12. 你的战略执行建议

RecordChat 的第一版不要超过 1–2 周。你现在最重要的不是做一个巨大系统，而是快速形成一个可以展示的 aviation AI interface。

你的优先级应该是：

第一优先：能跑
第二优先：有 ONE Record 专业感
第三优先：有 citations
第四优先：有 JSON-LD 生成
第五优先：能接到 RecordForge / ALH 的路线

不要一开始就做：

复杂权限系统
复杂 ontology parser
多用户管理
完整 ONE Record Server 集成
复杂 agent workflow

那些是 v0.2 / v0.3 的事情。

你现在的目标是做出一个让别人一看就明白的 demo：

This person is not just learning AI. He understands how domain standards, data platforms, semantic models, and AI interfaces connect.

这才是对你 100k+ 岗位最有价值的信号。