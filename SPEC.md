# RecordChat 项目规格说明书（SPEC v0.1）

> 面向 IATA ONE Record 的 domain-specific AI 助手。
> 本文档是给人和 coding agent 共同阅读的**单一事实来源（Single Source of Truth）**。
> 任何实现都应以本文档的契约（API 契约、数据模型、目录结构、验收标准）为准。

---

## 0. 怎么用这份文档

- 第 1–4 章：**为什么 / 做什么**（定位、范围、架构、技术栈）——人读。
- 第 5–11 章：**怎么做**（数据、契约、模块实现、目录、环境变量）——agent 主要参照。
- 第 12 章：**执行步骤**——按 Step 顺序执行，每个 Step 有「产出」和「验收」。
- 第 13 章：**验收清单**——v0.1 是否完成的唯一判据。
- 第 14 章：**工程边界**——禁止事项，防止做成一坨 LangChain demo。

Agent 执行原则：
1. **先能跑，再完善。** 每个 Phase 结束时项目必须能启动并通过该 Phase 的验收。
2. **契约优先。** 第 6 章定义的 API 请求/响应结构是硬约束，前后端都依赖它，不得擅自更改字段名。
3. **抽象不可省。** LLM provider、Embedding provider、Retriever 必须是可替换的接口（见第 14 章），即便 v0.1 只实现一个实现类。
4. **有疑问时，选择「能独立运行 + 有降级方案」的方案**，不要引入需要外部凭据才能启动的硬依赖。

---

## 1. 项目定位

**一句话：** RecordChat 是一个面向 IATA ONE Record 标准的 domain-specific AI 助手，帮助开发者和航空货运从业者理解 ONE Record 的数据模型、API 概念、JSON-LD 结构和语义关系，并通过 source-grounded 的 RAG 给出带引用的回答。

**它不是什么：**
- 不是「上传 PDF 问答」的通用工具。
- 不是裸调 LLM 的 chatbot。

**它在更大叙事中的位置（未来演进，不在 v0.1 范围）：**

```
RecordChat        = ONE Record 知识的 AI 接口层（本项目）
RecordForge       = 合成 ONE Record 数据生成器
ONE Record Server = 标准化数据交换层
AviationLakehouse = 分析后端（Bronze/Silver/Gold）
```

RecordChat 是这套生态的**第一个可展示入口**。设计时为后续接入 RecordForge / ALH 预留接口，但 v0.1 不实现它们。

---

## 2. v0.1 范围（Scope）

### In Scope（必须做）
- 后端 FastAPI 服务，3 个端点：`/health`、`/chat`、`/ingest`。
- 一个 RAG pipeline：query 分类 → 检索 → 组装 prompt → LLM → 带引用的回答。
- 向量库 Qdrant（通过 docker-compose 启动）。
- 知识底座：ONE Record 本体（ontology）+ 文档 + 手工 glossary 的混合摄取。
- JSON-LD 生成器（模板化，覆盖至少 Piece 和 Shipment）。
- 关系图谱（手工维护的核心关系映射）。
- 最小但干净的 Next.js 前端：聊天 + 引用展示 + JSON-LD 代码块。
- LLM / Embedding provider 抽象，支持环境变量切换（Qwen / OpenAI / Claude）。
- 评估脚本 + ≥10 条评估问题。
- 文档：README、architecture、roadmap、demo_script。

### Out of Scope（v0.1 明确不做，放 v0.2/v0.3）
- 用户认证 / 多用户 / 会话持久化到数据库。
- 完整的 ontology parser（v0.1 用启发式 + 手工关系表）。
- RecordForge / ALH / ONE Record Server 真正集成。
- 复杂 agent workflow、reranker（接口预留，实现可选）。
- OpenTelemetry、admin UI、评估 dashboard。

---

## 3. 架构

```
                ┌─────────────────────────────────────────┐
                │            Frontend (Next.js)            │
                │  Chat UI · Sources · JSON-LD viewer      │
                └───────────────────┬─────────────────────┘
                                    │ HTTP (JSON, 见第 6 章契约)
                ┌───────────────────▼─────────────────────┐
                │            Backend (FastAPI)             │
                │  api/  chat · ingest · health            │
                │   │                                       │
                │   ▼                                       │
                │  rag/pipeline.py  ── 编排器               │
                │     ├── query classifier                  │
                │     ├── retriever.py  ─┐                  │
                │     ├── prompt.py       │                  │
                │     └── llm.py          │                  │
                │   domain/               │                  │
                │     ├── jsonld_generator.py（模板）       │
                │     ├── one_record_schema.py（关系表）    │
                │     └── glossary.py（种子知识）           │
                │   core/  config · llm · embeddings        │
                └──────────┬────────────┬───────────────────┘
                          │            │
              ┌───────────▼──┐   ┌─────▼──────────────┐
              │   Qdrant     │   │  LLM / Embedding   │
              │ (vector DB)  │   │  Provider (API)    │
              └──────────────┘   └────────────────────┘

Ingestion path:  data/raw/ → loader → chunker → embeddings → Qdrant
```

**数据流（/chat）：**
```
User query
  → classify(query) → query_type
  → retriever.search(query, top_k) → chunks[] (含 metadata)
  → [可选] rerank
  → prompt.build(query, chunks, query_type)
  → llm.complete(prompt) → answer
  → [若 query_type == jsonld_generation] domain.jsonld_generator → structured_output
  → [若 query_type == relationship_question] domain.one_record_schema → related_concepts
  → 组装 ChatResponse（answer + sources + related_concepts + structured_output）
```

---

## 4. 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 后端 | Python 3.11+ / FastAPI | 用 `uv` 管理依赖，`pyproject.toml` |
| 向量库 | Qdrant | docker-compose 启动，collection: `recordchat_one_record` |
| LLM | 抽象接口 + 多实现 | 默认 provider 由 `LLM_PROVIDER` 环境变量决定，支持 `qwen`/`openai`/`claude` |
| Embedding | 抽象接口 + 多实现 | `EMBEDDING_PROVIDER`，支持 `qwen`/`openai` |
| 前端 | Next.js (App Router) + Tailwind + shadcn/ui | 单页聊天界面 |
| 容器 | Docker Compose | 服务：backend、frontend、qdrant |
| 测试 | pytest（后端） | RAG 关键路径 + domain 逻辑单测 |

> **判断说明（不要盲从）：** 若时间极紧，前端允许先用一个极简静态页面或 Streamlit 验证后端，但**最终 v0.1 交付以 Next.js 为准**，因为这是 portfolio 信号的一部分。后端契约必须先稳定，前端后做。

---

## 5. 知识底座与数据（最关键、最易被低估的部分）

RAG 的可信度来自 **source grounding**，不来自 LLM 编造。数据质量决定项目质量。

### 5.1 数据来源（真实来源，agent 需据此采集）

ONE Record 是有公开本体和规范的真实标准，**不要凭空编造内容**：

| 来源 | 内容 | 形态 |
|---|---|---|
| IATA-Cargo/ONE-Record（GitHub） | 官方本体（ontology）、API 规范、示例 | RDF/Turtle (`.ttl`)、Markdown、JSON |
| ONE Record API Specification | 端点、订阅/通知机制 | OpenAPI / Markdown |
| ONE Record Data Model / Ontology | 类（Class）、属性（Property）、关系 | TTL / OWL |
| JSON-LD 示例 payload | LogisticsObject 实例样例 | JSON-LD |

**采集落地结构：**
```
data/raw/
├── ontology/      # .ttl / .owl 本体文件
├── one_record_docs/  # markdown / html 文档
├── api_specs/     # openapi.yaml / api markdown
├── examples/      # 示例 JSON-LD payload
└── notes/         # 自己整理的补充笔记
```

每个文档需配套一个 sidecar metadata（`<filename>.meta.json`）：
```json
{
  "source_name": "IATA ONE Record Ontology",
  "version": "x.x",
  "url": "https://...",
  "document_type": "ontology | api_spec | docs | example | notes",
  "domain": "one_record",
  "ingested_at": "ISO-8601"
}
```

### 5.2 降级方案（必须有，保证项目「即使没联网也能跑」）

`backend/app/domain/glossary.py` 内置一份**手工整理的种子知识**（≥15 个核心概念），即使 `data/raw/` 为空，`/ingest` 也能把 glossary 写入 Qdrant，使 `/chat` 可用。核心概念至少包括：

```
LogisticsObject, Shipment, Piece, Waybill (Air Waybill),
TransportMovement, LogisticsEvent, Booking, Product,
Company, Location, Item, ULD (Unit Load Device),
Sensor, Subscription, Notification
```

每个种子条目结构：
```python
{
  "entity": "Piece",
  "definition": "A Piece represents the smallest physical unit ...",
  "related_entities": ["Shipment", "LogisticsObject"],
  "source_name": "RecordChat curated glossary",
}
```

> **判断说明：** 这一步是 ChatGPT 原始计划里被忽略的最大风险。先实现 glossary 降级，再做真实文档摄取——保证 walking skeleton 始终可运行。

### 5.3 Domain-aware Chunking（差异化亮点）

不要只做固定长度切分。按来源类型分别切：

| 来源类型 | 切分策略 | chunk_type |
|---|---|---|
| ontology (.ttl) | 按 Class / Property 切，每个类一个 chunk | `class_definition` / `property_definition` |
| markdown 文档 | 按标题层级（H1/H2/H3）切 | `concept` / `general` |
| OpenAPI / API 文档 | 按 endpoint 切 | `api` |
| 示例 payload | 整个 payload 一个 chunk | `example` |
| glossary | 每个条目一个 chunk | `concept` |

**每个 chunk 的统一结构：**
```json
{
  "chunk_id": "stable-hash-or-uuid",
  "content": "...",
  "metadata": {
    "source_name": "...",
    "source_url": "...",
    "version": "...",
    "section_title": "...",
    "chunk_type": "concept | api | class_definition | property_definition | example | general",
    "entity": "可选，如 Piece",
    "related_entities": []
  }
}
```

---

## 6. API 契约（硬约束 — 前后端共同依赖，禁止擅改字段名）

### `GET /health`
```json
{ "status": "ok", "service": "recordchat-backend" }
```

### `POST /chat`
**Request:**
```json
{
  "message": "What is a Piece in ONE Record?",
  "conversation_id": "optional-string"
}
```
**Response:**
```json
{
  "answer": "string (markdown)",
  "query_type": "concept_explanation | relationship_question | api_question | jsonld_generation | general_question",
  "sources": [
    {
      "source_name": "string",
      "section_title": "string",
      "source_url": "string|null",
      "chunk_id": "string"
    }
  ],
  "related_concepts": ["Piece", "Shipment", "LogisticsObject"],
  "structured_output": null
}
```
当 `query_type == "jsonld_generation"` 时，`structured_output` 为合法 JSON-LD：
```json
{
  "structured_output": {
    "@context": "https://onerecord.iata.org/ns/cargo",
    "@type": "Piece",
    "@id": "https://example.com/pieces/...",
    "...": "..."
  }
}
```

### `POST /ingest`
**Request（v0.1 可为空 body 或）：**
```json
{ "reset": false, "source_dir": "data/raw" }
```
**Response:**
```json
{
  "status": "ok",
  "documents_loaded": 0,
  "chunks_created": 0,
  "chunks_indexed": 0
}
```
行为：load → chunk → embed → 写入 Qdrant，保留 metadata。`reset=true` 时先清空 collection。

---

## 7. 后端模块职责（每个文件该干什么）

```
backend/app/
├── main.py                 # FastAPI app 实例 + 路由注册 + CORS
├── api/
│   ├── health.py           # GET /health
│   ├── chat.py             # POST /chat — 只做请求解析 + 调 pipeline + 返回，不写业务逻辑
│   └── ingest.py           # POST /ingest — 调 ingestion 流程
├── core/
│   ├── config.py           # pydantic-settings，读所有环境变量（见第 8 章）
│   ├── llm.py              # LLMProvider 抽象 + QwenProvider/OpenAIProvider/ClaudeProvider + factory
│   ├── embeddings.py       # EmbeddingProvider 抽象 + 实现 + factory
│   └── logging.py          # 结构化日志配置
├── rag/
│   ├── loader.py           # 读 data/raw/ + sidecar meta，产出 RawDocument[]
│   ├── chunker.py          # domain-aware chunking（第 5.3 节）→ Chunk[]
│   ├── retriever.py        # Retriever 抽象 + QdrantRetriever（search/upsert/reset）
│   ├── reranker.py         # 可选；v0.1 可为 no-op 直通实现
│   ├── prompt.py           # 系统 prompt（第 9 章）+ 按 query_type 组装上下文
│   └── pipeline.py         # 编排器：classify → retrieve → prompt → llm → 组装 ChatResponse
├── domain/
│   ├── one_record_schema.py  # ONE_RECORD_RELATIONSHIPS 关系表 + 查询函数
│   ├── jsonld_generator.py   # 模板化 JSON-LD 生成（generate_*_example）
│   └── glossary.py           # 种子知识（第 5.2 节）
└── models/
    ├── chat.py             # pydantic: ChatRequest/ChatResponse/Source
    └── source.py           # pydantic: Chunk / RawDocument / ChunkMetadata
```

**query 分类（v0.1 用规则，接口留给后续换 LLM classifier）：**
```
jsonld_generation     : 含 "generate"/"example" + "json-ld"/"payload"/类名
relationship_question : 含 "relationship"/"related"/"difference between"/"vs"
api_question          : 含 "api"/"endpoint"/"create"/"subscription"/"server"
concept_explanation   : 含 "what is"/"explain"/"define"
general_question      : 兜底
```

---

## 8. 环境变量（`.env.example`）

```bash
# LLM
LLM_PROVIDER=qwen            # qwen | openai | claude
LLM_MODEL=qwen-plus
LLM_API_KEY=
LLM_BASE_URL=                # 可选，自定义网关

# Embedding
EMBEDDING_PROVIDER=qwen      # qwen | openai
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_API_KEY=
EMBEDDING_DIM=1024           # 与所选模型一致；建 Qdrant collection 时用

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=recordchat_one_record

# RAG
RAG_TOP_K=5

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> Provider 抽象要求：`core/config.py` 读 `*_PROVIDER`，由 factory 返回对应实现。切换 provider **不需要改业务代码**。

---

## 9. System Prompt（RecordChat 的灵魂）

```
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
3. Distinguish official ONE Record concepts from your own implementation suggestions.
4. When generating JSON-LD examples, mark them as illustrative unless directly copied from official documentation.
5. Prefer concise, developer-friendly answers.
6. Always include relevant sources when available.
```

**回答结构（Answer / Related concepts / Implementation note / Sources）：**
```
Answer:
...

Related concepts:
- ...

Implementation note:
...

Sources:
- <source_name>, <section_title>
```

---

## 10. Domain 层细节

### 10.1 关系表（`one_record_schema.py`）
```python
ONE_RECORD_RELATIONSHIPS = {
    "Shipment": ["Piece", "Waybill", "LogisticsEvent"],
    "Piece": ["Shipment", "LogisticsObject", "TransportMovement"],
    "Waybill": ["Shipment"],
    "LogisticsObject": ["Piece", "Shipment", "Waybill"],
    "TransportMovement": ["Piece", "LogisticsEvent"],
}
# 提供 get_related(entity) -> list[str]，供 relationship_question 富化 related_concepts
```

### 10.2 JSON-LD 生成器（`jsonld_generator.py`）
模板化，**不让 LLM 裸生成整个结构**——LLM 只负责解释，模板负责结构稳定。至少实现：
```python
def generate_piece_example() -> dict: ...
def generate_shipment_example() -> dict: ...
# 返回合法 JSON-LD，含 @context / @type / @id，@context 指向 ONE Record 命名空间
```
pipeline 在 `jsonld_generation` 类型时调用对应函数填充 `structured_output`。

---

## 11. 前端要求（最小但干净）

布局：
```
左侧栏：New Chat · Example Questions · ONE Record Concepts · JSON-LD Generator
主区域：聊天消息 · Source citations · JSON-LD viewer（structured_output 存在时以代码块格式化展示）
```
Example Questions（可点击直接发送）：
```
What is ONE Record?
What is a LogisticsObject?
Explain the relationship between Shipment and Piece.
Generate a JSON-LD example for a Piece.
How does ONE Record support data sharing?
What is the role of JSON-LD in ONE Record?
```
验收：能发消息、显示回答、显示 sources、JSON-LD 格式化为代码块、示例问题可点。

---

## 12. 执行步骤（按序，每步可独立验证）

> 每个 Phase 结束时项目必须能启动并通过该 Phase 验收。不要跳步。

### Phase 0 — 项目骨架
- **产出：** 第 7 章目录结构；README/.env.example/docker-compose.yml 占位；`uv` + pyproject。
- **验收：** 目录齐全；`uv run python -c "import app"` 不报错。

### Phase 1 — FastAPI skeleton + config
- **产出：** `main.py`、`/health`、`core/config.py`（pydantic-settings 读环境变量）。
- **验收：** `uvicorn` 启动，`curl /health` 返回 `{"status":"ok",...}`。

### Phase 2 — docker-compose + Qdrant
- **产出：** docker-compose 含 backend + qdrant；backend 能连上 Qdrant。
- **验收：** `docker compose up` 后 backend 启动且能 ping 通 Qdrant（启动日志或一个内部检查）。

### Phase 3 — Provider 抽象（LLM + Embedding）
- **产出：** `core/llm.py`、`core/embeddings.py` 抽象基类 + 至少一个实现 + factory。
- **验收：** 单测：factory 按环境变量返回正确实现类；mock 下 `complete()` / `embed()` 可调用。

### Phase 4 — Glossary 降级知识 + ingestion 最小闭环
- **产出：** `domain/glossary.py`（≥15 条）、`rag/loader.py`、`rag/chunker.py`、`retriever.py`（Qdrant upsert/search/reset）、`/ingest`。
- **验收：** `data/raw/` 为空时，`POST /ingest` 仍把 glossary 写入 Qdrant；返回 `chunks_indexed > 0`；能 search 召回。

### Phase 5 — RAG pipeline + /chat
- **产出：** query classifier、`prompt.py`、`pipeline.py`、`/chat`。
- **验收：** `POST /chat {"message":"What is a Piece?"}` 返回非空 answer + 至少 1 条 source + query_type 正确。

### Phase 6 — Domain：关系表 + JSON-LD 生成器
- **产出：** `one_record_schema.py`、`jsonld_generator.py`，pipeline 接入。
- **验收：** 问 "Generate a JSON-LD example for a Piece" → `structured_output` 是合法 JSON-LD（含 @context/@type/@id）；问 relationship → `related_concepts` 被关系表富化。

### Phase 7 — 真实文档摄取
- **产出：** 采集 ONE Record ontology/docs/examples 到 `data/raw/` + sidecar meta；domain-aware chunker 处理 .ttl / markdown / openapi。
- **验收：** `/ingest` 处理真实文件，`chunks_created` 反映多种 chunk_type；`/chat` 回答带真实 source 引用。

### Phase 8 — 前端
- **产出：** Next.js + Tailwind + shadcn/ui，按第 11 章布局；接 `/chat`。
- **验收：** 第 11 章全部前端验收项通过。

### Phase 9 — 评估
- **产出：** `data/eval/questions.yaml`（≥10 条，覆盖 concept/relationship/api/jsonld）、`scripts/evaluate_rag.py`。
- **验收：** 脚本可运行，输出 retrieval hit rate / source coverage / answer 非空率 / JSON-LD 合法性 / 关键词命中率。

### Phase 10 — 文档 + 全链路冒烟
- **产出：** `docs/architecture.md`、`roadmap.md`、`demo_script.md`、`scripts/{ingest_docs,reset_index}.py`、完善 README quickstart。
- **验收：** 全新环境 `docker compose up` → ingest → 跑通 demo_script 的 5 个问题。

---

## 13. v0.1 验收清单（完成的唯一判据）

**Backend**
- [ ] `docker compose up` 启动 backend + frontend + qdrant
- [ ] `/health` 正常
- [ ] `data/raw/`（含降级 glossary）可被 `/ingest` 摄取
- [ ] Qdrant 能存储与检索 chunk（含 metadata）
- [ ] `/chat` 返回 grounded answer
- [ ] 回答包含 source citations
- [ ] JSON-LD 生成对 Piece 和 Shipment 可用
- [ ] LLM / Embedding provider 可通过环境变量切换

**Frontend**
- [ ] 用户能发消息并看到回答
- [ ] sources 在 UI 可见
- [ ] JSON-LD 输出格式化为代码块
- [ ] 示例问题可点击

**Docs & Eval**
- [ ] README 有 quickstart
- [ ] architecture.md / roadmap.md / demo_script.md 存在
- [ ] ≥10 条评估问题 + evaluate_rag.py 可运行

**Demo（用户能演示这 5 个问题）**
1. What is ONE Record?
2. What is a LogisticsObject?
3. Explain Shipment vs Piece.
4. Generate a JSON-LD example for a Piece.
5. How could ONE Record data be connected to an AviationLakehouse?

---

## 14. 工程边界（禁止事项 — 这是平台工程师与 demo builder 的区别）

**必须保持：**
- LLM provider 抽象、Embedding provider 抽象、Retriever 抽象（即使各只一个实现）。
- Domain 逻辑（关系表、JSON-LD 模板）与 RAG 解耦。
- JSON-LD 生成器与自由文本 LLM 解耦（结构由模板保证）。
- 前后端解耦，仅通过第 6 章契约通信。
- 文档与评估从第一天就在。

**禁止：**
- ❌ 在 `chat.py` 里直接写 prompt + 调模型 + 解析结果 + 生成 JSON（必须经 `pipeline.py`）。
- ❌ 把某个 LLM provider 硬编码进业务逻辑。
- ❌ 让 LLM 裸生成完整 JSON-LD 结构（必须模板化）。
- ❌ 引入需要外部凭据才能「启动」的硬依赖（凭据缺失应优雅降级，而非崩溃）。
- ❌ v0.1 实现认证、多用户、ontology 全自动解析、RecordForge/ALH 真集成。

**正确分层：**
```
api/chat.py → rag/pipeline.py → {retriever.py | prompt.py | core/llm.py | domain/*}
```

---

## 15. 后续路线（仅记录，不在 v0.1 实现）

- **v0.2.1** Ontology-aware retrieval：entity-first 检索（识别 query 中的 ONE Record 实体后优先检索相关 chunk）。
- **v0.2.2** RecordForge 集成：`User: Generate 5 synthetic shipments` → RecordChat 调 RecordForge 出 JSON-LD。
- **v0.2.3** ALH 集成：解释 ONE Record 对象如何 land 到 Bronze/Silver/Gold。
- **v0.3** 认证 / 会话记忆 / source versioning / OpenTelemetry / 评估 dashboard / 三大 connector。

---

## 16. 时间预算

v0.1 目标 **1–2 周**。优先级：能跑 > ONE Record 专业感 > citations > JSON-LD 生成 > 可接 RecordForge/ALH 的路线。不要在 v0.1 追求完美。
```
