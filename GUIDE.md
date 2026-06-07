# RecordChat 项目制作指南（中文详解）

> 本文档是 RecordChat 的**完整制作指南**：从零到可运行 v0.1，逐步讲清每一步要做什么、
> 每个文件的职责、关键代码逻辑、为什么这样设计、怎么运行和验证。
>
> 配套文档：
> - [SPEC.md](SPEC.md) — 规格与契约（单一事实来源）
> - [README.md](README.md) — 面向用户的快速上手
> - [docs/architecture.md](docs/architecture.md) — 架构图与设计决策
> - 本文（GUIDE.md）— 面向**开发者/制作者**的逐步实现细节
>
> **状态说明（2026-06）**：本文主体仍以 `v0.1` 的构建过程为主，但项目接下来的
> 优先级已经调整为：**先补知识底座，再继续堆功能。** 具体见
> [docs/data_source_plan.md](docs/data_source_plan.md) 与
> [docs/v0.2_development_plan.md](docs/v0.2_development_plan.md)。
>
> 阅读建议：第 1–2 章建立整体认知；第 3 章是目录地图；第 4 章是**按序制作步骤**（核心）；
> 第 5–9 章是各模块的代码级细节；第 10 章起是运行、测试、Docker、扩展与排错。

---

## 目录

1. [项目是什么 / 设计哲学](#1-项目是什么--设计哲学)
2. [技术栈与选型理由](#2-技术栈与选型理由)
3. [目录结构地图（每个文件干什么）](#3-目录结构地图每个文件干什么)
4. [按序制作步骤（Phase 0–10）](#4-按序制作步骤phase-010)
5. [后端核心：配置与 Provider 抽象](#5-后端核心配置与-provider-抽象)
6. [后端核心：RAG 管线](#6-后端核心rag-管线)
7. [后端核心：Domain 领域层](#7-后端核心domain-领域层)
8. [数据与摄取（Ingestion）](#8-数据与摄取ingestion)
9. [前端实现](#9-前端实现)
10. [运行、测试与验证](#10-运行测试与验证)
11. [Docker 与部署](#11-docker-与部署)
12. [评估（Evaluation）](#12-评估evaluation)
13. [扩展方向（v0.2 / v0.3）](#13-扩展方向v02--v03)
14. [常见问题与排错](#14-常见问题与排错)

---

## 1. 项目是什么 / 设计哲学

**RecordChat** 是一个面向 IATA ONE Record 标准的 domain-specific AI 助手。用户用自然语言提问
（概念、数据模型、JSON-LD、API、实体关系），系统用 RAG（检索增强生成）从 ONE Record 知识库
检索证据，再让 LLM 基于证据回答，并**附带来源引用**。

当前阶段最重要的工程判断是：**先扩充真实知识源，再继续下游功能。** `v0.1`
已经证明了端到端链路可运行；下一步不该优先追求更花哨的功能，而是把官方 ONE
Record 与 NE:ONE 资料真正导入进来，让后续问答建立在更扎实的语料上。

它不是普通 chatbot，制作时贯穿四条设计哲学（违反它们就是做错了）：

| 原则 | 含义 | 在代码里如何体现 |
|---|---|---|
| **离线优先 / 优雅降级** | 没有任何 API key、没有 Docker，也能完整跑起来 | `local` LLM + `local` embedding + 内存 Qdrant；缺 key 只告警不崩溃 |
| **Provider 抽象** | 换 LLM/embedding 厂商是改配置不是改代码 | `LLMProvider` / `EmbeddingProvider` / `Retriever` 抽象基类 + 工厂 |
| **关注点分离** | API 薄、编排集中、领域逻辑独立 | `api/*` 只解析请求 → `rag/pipeline.py` 编排 → 调 retriever/prompt/llm/domain |
| **结构稳定不靠 LLM 裸生成** | JSON-LD 结构由模板保证合法，LLM 只解释 | `domain/jsonld_generator.py` 出结构，prompt 让 LLM 解释 |

> 记住这张表。后面所有实现细节都是为了落地这四条。

---

## 2. 技术栈与选型理由

| 层 | 选型 | 为什么 |
|---|---|---|
| 后端语言 | Python 3.11+ | AI/RAG 生态最成熟 |
| Web 框架 | FastAPI | 异步、自带 pydantic 校验与 OpenAPI 文档 |
| 依赖管理 | `uv` | 比 pip/poetry 快一个数量级，`uv.lock` 可复现 |
| 数据校验/模型 | pydantic v2 + pydantic-settings | 请求/响应契约即代码；环境变量强类型 |
| 向量库 | Qdrant | 生产级；`qdrant-client` 同时支持 `:memory:` 内嵌与远程服务，完美契合"离线优先" |
| 本体解析 | rdflib | 解析 `.ttl`/`.owl` 本体，按类/属性切块 |
| LLM/Embedding | HTTP 抽象 | OpenAI 与 Qwen(DashScope) 都是 OpenAI 兼容协议，一套 client 复用；Claude 单独实现 |
| 前端 | Next.js 14 (App Router) + Tailwind + TypeScript | 真实产品观感，利于 portfolio |
| 测试 | pytest | 标准 |
| 容器编排 | Docker Compose | backend + frontend + qdrant 一键起 |

**关键判断：** 为什么不一上来就强依赖云端 LLM/Qdrant？因为那样项目"启动"就需要密钥和网络，
demo 和 CI 都脆弱。我们让 `local` 实现成为默认，保证"克隆即可跑"，真实模型只是一个环境变量的事。

---

## 3. 目录结构地图（每个文件干什么）

```
Recordchat/
├── SPEC.md                      # 规格与契约（单一事实来源）
├── GUIDE.md                     # 本文：制作指南
├── README.md                    # 用户快速上手
├── .env.example                 # 所有环境变量样例
├── .gitignore
├── docker-compose.yml           # backend + frontend + qdrant
│
├── backend/
│   ├── pyproject.toml           # 依赖 + pytest 配置（pythonpath/asyncio）
│   ├── README.md                # 后端快速上手（打包需要它存在）
│   ├── Dockerfile               # python:3.11-slim + uv
│   └── app/
│       ├── main.py              # FastAPI 实例工厂 create_app() + CORS + 路由注册
│       ├── api/
│       │   ├── health.py        # GET /health
│       │   ├── chat.py          # POST /chat（薄 handler → pipeline.answer）
│       │   └── ingest.py        # POST /ingest（薄 handler → run_ingest）
│       ├── core/
│       │   ├── config.py        # Settings（pydantic-settings），所有运行时旋钮
│       │   ├── logging.py       # 统一日志
│       │   ├── llm.py           # LLMProvider 抽象 + local/openai兼容/claude + 工厂
│       │   └── embeddings.py    # EmbeddingProvider 抽象 + local哈希/openai兼容 + 工厂
│       ├── rag/
│       │   ├── loader.py        # 读 data/raw + sidecar meta → RawDocument[]
│       │   ├── chunker.py       # domain-aware 切块（本体/openapi/markdown/jsonld）
│       │   ├── retriever.py     # Retriever 抽象 + QdrantRetriever（建库/重置/写入/检索）
│       │   ├── reranker.py      # 占位 no-op（v0.2 接 rerank 的缝）
│       │   ├── prompt.py        # 系统提示词 + 上下文组装
│       │   ├── pipeline.py      # 编排器：classify→retrieve→prompt→llm→enrich
│       │   └── ingest.py        # 摄取服务：load→chunk→embed→store（含 glossary）
│       ├── domain/
│       │   ├── glossary.py      # 17 条手工种子知识（离线降级知识库）
│       │   ├── one_record_schema.py  # 关系表 + 实体识别
│       │   └── jsonld_generator.py   # 模板化 JSON-LD 生成
│       ├── models/
│       │   ├── chat.py          # API 契约模型（ChatRequest/Response/Source 等）
│       │   └── source.py        # 内部模型（Chunk/RawDocument/ChunkMetadata）
│       └── tests/
│           ├── conftest.py      # 固定离线 provider + 内存 Qdrant 的 fixtures
│           ├── test_health.py
│           ├── test_providers.py
│           └── test_pipeline.py
│
├── frontend/                    # Next.js
│   ├── package.json / tsconfig.json / next.config.mjs
│   ├── tailwind.config.ts / postcss.config.mjs
│   ├── Dockerfile               # 多阶段 standalone 构建
│   ├── app/{layout.tsx, page.tsx, globals.css}
│   ├── components/{Sidebar, Message, Sources, JsonLdViewer}.tsx
│   └── lib/{api.ts, constants.ts}
│
├── data/
│   ├── raw/                     # 知识源（按类型分子目录）
│   │   ├── ontology/one_record_core.ttl(+.meta.json)
│   │   ├── one_record_docs/data_sharing.md
│   │   ├── api_specs/one_record_api.yaml
│   │   └── examples/piece_example.jsonld
│   ├── eval/questions.yaml      # 12 条评估问题
│   ├── processed/ index/        # 预留产物目录
│
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── demo_script.md
│   └── adr/0001-provider-abstraction.md
│
└── scripts/
    ├── ingest_docs.py           # CLI 摄取
    ├── reset_index.py           # CLI 清库
    └── evaluate_rag.py          # CLI 评估
```

---

## 4. 按序制作步骤（Phase 0–10）

> 制作铁律：**每个 Phase 结束，项目必须能启动并通过该 Phase 验收，不跳步。**
> 下面每个 Phase 给出「做什么 / 产出文件 / 怎么验收」。命令默认在 `backend/` 下用 `uv` 执行。

### Phase 0 — 项目骨架
- **做什么**：建目录树；写 `backend/pyproject.toml`（声明依赖与 pytest 配置）；写 `backend/README.md`
  （hatchling 打包要求 readme 存在，否则 `uv pip install -e` 会报错）。
- **命令**：
  ```bash
  mkdir -p backend/app/{api,core,rag,domain,models} backend/tests \
           data/{raw/{ontology,one_record_docs,api_specs,examples,notes},processed,index,eval} \
           docs/adr scripts
  ```
- **验收**：目录齐全；`uv run python -c "import app"` 不报错。

### Phase 1 — FastAPI 骨架 + 配置
- **做什么**：`models/chat.py`（契约模型）、`core/config.py`、`core/logging.py`、`api/health.py`、`main.py`。
- **验收**：`uv run uvicorn app.main:app --port 8000` 启动，`curl localhost:8000/health` 返回
  `{"status":"ok","service":"recordchat-backend"}`。

### Phase 2 — docker-compose + Qdrant
- **做什么**：写 `docker-compose.yml`（qdrant + backend + frontend），`backend/Dockerfile`。
  retriever 默认用 `:memory:`，compose 里通过环境变量 `QDRANT_URL=http://qdrant:6333` 覆盖为真实服务。
- **验收**：`docker compose config --quiet` 通过；`docker compose up -d qdrant` 后 `curl localhost:6333/readyz` 就绪。

### Phase 3 — Provider 抽象（LLM + Embedding）
- **做什么**：`core/embeddings.py` 与 `core/llm.py`：抽象基类 + `local` 实现 + OpenAI兼容/Claude 实现 + 工厂。
  工厂规则：provider=local → 用 local；provider≠local 但 key 为空 → **告警并降级 local**。
- **验收**：`uv run pytest tests/test_providers.py -q` 通过（验证降级、确定性、归一化）。

### Phase 4 — Glossary 降级知识 + 摄取闭环
- **做什么**：`domain/glossary.py`（≥15 条）、`rag/loader.py`、`rag/chunker.py`、`rag/retriever.py`、
  `rag/ingest.py`、`api/ingest.py`。`run_ingest` 永远把 glossary 与 `data/raw` 合并，保证库非空。
- **验收**：`data/raw` 为空时 `POST /ingest` 仍返回 `chunks_indexed>0`（仅 glossary）。

### Phase 5 — RAG 管线 + /chat
- **做什么**：`rag/prompt.py`、`rag/pipeline.py`（含 `classify_query`）、`api/chat.py`。
- **验收**：`POST /chat {"message":"What is a Piece?"}` 返回非空 answer + ≥1 source + 正确 query_type。

### Phase 6 — Domain：关系表 + JSON-LD 生成器
- **做什么**：`domain/one_record_schema.py`、`domain/jsonld_generator.py`，并在 pipeline 接入：
  jsonld 类问题填 `structured_output`；relationship 类问题用关系表富化 `related_concepts`。
- **验收**：问 "Generate a JSON-LD example for a Piece" → `structured_output["@type"]=="Piece"` 且合法 JSON。

### Phase 7 — 真实文档摄取（domain-aware chunking）
- **做什么**：往 `data/raw` 放种子文件（`.ttl` 本体 + `.meta.json` sidecar、`.md`、openapi `.yaml`、`.jsonld`）；
  chunker 对不同类型用不同策略。
- **验收**：摄取后 `chunks_created` 含多种 `chunk_type`（class_definition/property_definition/api/concept/example）。

### Phase 8 — 前端
- **做什么**：Next.js App Router + Tailwind；`lib/api.ts` 镜像后端契约；Sidebar/Message/Sources/JsonLdViewer 组件。
- **验收**：`npm run build` 编译 + 类型检查通过；UI 能发消息、显示回答/来源/JSON-LD、示例问题可点。

### Phase 9 — 评估
- **做什么**：`data/eval/questions.yaml`（≥10 条）、`scripts/evaluate_rag.py`。
- **验收**：脚本离线可跑，硬门槛（检索命中/来源覆盖/答案非空/JSON-LD 合法）全 100%。

### Phase 10 — 文档 + 全链路冒烟
- **做什么**：`docs/{architecture,roadmap,demo_script}.md`、ADR、`scripts/{ingest_docs,reset_index}.py`、完善 README。
- **验收**：全新环境 `docker compose up` → ingest → 跑通 demo_script 的 5 个问题。

---

## 5. 后端核心：配置与 Provider 抽象

### 5.1 配置 `core/config.py`
用 `pydantic-settings` 读环境变量与 `.env`，全部带默认值（默认离线）：

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    llm_provider: str = "local"        # local | qwen | openai | claude
    llm_api_key: str = ""
    embedding_provider: str = "local"  # local | qwen | openai
    embedding_dim: int = 1024
    qdrant_url: str = ":memory:"       # 内存库；docker 里覆盖为 http://qdrant:6333
    qdrant_collection: str = "recordchat_one_record"
    rag_top_k: int = 5
    cors_origins: str = "http://localhost:3000"
```
- `get_settings()` 用 `@lru_cache` 保证单例。
- **要点**：`embedding_dim` 必须与所选 embedding 模型维度一致；建 Qdrant collection 用它。
  测试里用 256 降低开销（见 `conftest.py`）。

### 5.2 Embedding 抽象 `core/embeddings.py`
- 抽象基类 `EmbeddingProvider`：`embed(texts)->list[vec]`，`embed_one(text)`。
- `LocalHashEmbeddingProvider`：把分词哈希到 `dim` 维桶里（带符号），再 L2 归一化。
  确定性、零依赖、可离线。语义弱但够 demo/测试的词面检索。
- `OpenAICompatEmbeddingProvider`：POST `/embeddings`，OpenAI 与 Qwen(DashScope) 通用。
- **工厂 `build_embedding_provider`**：provider=local 直接用 local；否则 key 为空 → 告警降级；
  base_url 取 `LLM_BASE_URL` 或内置默认（openai/qwen）。

### 5.3 LLM 抽象 `core/llm.py`
- 抽象基类 `LLMProvider.complete(system, user)->str`。
- `LocalLLMProvider`：**抽取式**回答——从 prompt 里解析出 `CONTEXT:` 与 `QUESTION:` 块，
  取前 2 段上下文拼成答案。保证离线时回答仍 grounded（不编造），也让 RAG 管线无需花 token 即可测。
  辅助函数 `_extract_block` 负责按 `LABEL:` 切块。
- `OpenAICompatLLMProvider`：POST `/chat/completions`（openai/qwen）。
- `ClaudeLLMProvider`：POST `/v1/messages`（Anthropic 协议，带 `anthropic-version` 头）。
- 工厂规则同 embedding：缺 key 降级 local，未知 provider 降级 local。

> 这一层是"换厂商=改配置"的关键。业务代码只 `get_llm_provider()` / `get_embedding_provider()`，
> 永远不 import 具体实现类。

---

## 6. 后端核心：RAG 管线

数据流（`rag/pipeline.py` 的 `answer()`）：
```
query → classify_query → retriever.search(top_k) → rerank(no-op)
      → prompt.build_user_prompt → llm.complete
      → [jsonld 类] jsonld_generator 填 structured_output
      → [关系类] one_record_schema 富化 related_concepts
      → 组装 ChatResponse
```

### 6.1 查询分类 `classify_query`
v0.1 用**规则**（按关键词），接口保留以后换 LLM 分类器：
- 含 jsonld/payload + generate/example/create → `jsonld_generation`
- 含 relationship/related/difference between/vs → `relationship_question`
- 含 api/endpoint/subscription/server/how do i create → `api_question`
- 含 what is/explain/define/what are → `concept_explanation`
- 兜底 → `general_question`

### 6.2 提示词 `rag/prompt.py`
- `SYSTEM_PROMPT`：定义 RecordChat 身份与 6 条规则（以检索上下文为准、不支持就直说、
  区分官方概念与实现建议、JSON-LD 标注为示例、简洁、给来源），并要求答案结构化
  （Answer / Related concepts / Implementation note / Sources）。
- `build_user_prompt`：拼 `GUIDANCE`（按 query_type 的额外引导）+ `CONTEXT:`（用 `\n---\n`
  分隔的检索块，每块带 `[来源 — 小节]` 头）+ `QUESTION:`。
  **注意**：`CONTEXT:`/`QUESTION:` 这两个标签是 `LocalLLMProvider` 解析的契约，别改名。

### 6.3 检索 `rag/retriever.py`
- 抽象 `Retriever`：`ensure_collection/reset/upsert/search`。
- `QdrantRetriever`：`qdrant_url==":memory:"` 用内嵌库，否则连远程。
  - `upsert`：对每个 chunk 算向量；Qdrant 的 point id 必须是 uint/UUID，所以用
    `uuid5(NAMESPACE, chunk_id)` 生成稳定 id，原始 `chunk_id` 存进 payload。payload 同时存
    `content` 与全部 metadata，检索时还原成 `Chunk`。
  - `search`：用 `query_points`（新 API）取 top_k，从 payload 重建 `Chunk`。
- `get_retriever()` 单例。

### 6.4 编排细节
- `_related_concepts`：把「查询里识别到的实体 + 这些实体的关系表邻居 + 检索块自带的
  entity/related_entities」去重合并，截断到 8 个。
- `_jsonld_entity`：在查询里正则匹配生成器支持的实体名（Piece/Shipment/Waybill/TransportMovement），
  匹配不到默认 Piece。
- `answer()` 的 `retriever`/`llm` 是可注入参数，测试可传内存 retriever 与 `LocalLLMProvider`。

---

## 7. 后端核心：Domain 领域层

领域逻辑**独立于 RAG**，这样换检索/模型不影响领域知识。

### 7.1 `domain/glossary.py`
- 一个 `GLOSSARY` 字典：17 个核心实体（ONE Record、LogisticsObject、Shipment、Piece、Waybill、
  TransportMovement、LogisticsEvent、Booking、Product、Company、Location、Item、ULD、Sensor、
  Subscription、Notification、JSON-LD），每条含 `definition` 与 `related`。
- `glossary_chunks()`：物化成 `Chunk[]`，`source_name="RecordChat curated glossary"`，
  `chunk_type="concept"`，`chunk_id="glossary::<Entity>"`。
- **作用**：离线降级知识库。`data/raw` 为空也能回答核心概念。定义是教学性转述，标注为
  curated source，便于 UI 与官方文档区分。

### 7.2 `domain/one_record_schema.py`
- `ONE_RECORD_RELATIONSHIPS`：手工维护的实体→相关实体映射。
- `KNOWN_ENTITIES`：用于轻量实体识别。
- `get_related(entity)` / `detect_entities(text)`（大小写不敏感地在文本里找已知实体）。
- v0.2 会用本体解析自动生成，v0.1 先手写核心关系（不追求完美 ontology parser）。

### 7.3 `domain/jsonld_generator.py`
- 模板函数：`generate_piece_example/shipment/waybill/transport_movement_example`，
  返回带 `@context`（指向 `https://onerecord.iata.org/ns/cargo`）、`@type`、`@id`（uuid）的合法 dict。
- `GENERATORS` 注册表 + `generate_for_entity(entity)`（缺省 Piece）。
- **设计要点**：结构由模板出，LLM 不裸生成 → 永远合法、可稳定演示。

---

## 8. 数据与摄取（Ingestion）

### 8.1 知识源组织（`data/raw/`）
按类型分子目录，每个文件可配 `<文件名>.meta.json` sidecar 描述来源：
```json
{ "source_name": "...", "version": "...", "url": "...",
  "document_type": "ontology|api_spec|docs|example|notes",
  "domain": "one_record", "ingested_at": "ISO-8601" }
```
> **真实来源**（采集时用，不要编造）：IATA-Cargo/ONE-Record（GitHub）的本体 `.ttl`、API 规范、
> JSON-LD 示例。仓库里现有的种子文件是**示例子集**，已在内容与 meta 中标注 "illustrative"。

### 8.2 加载 `rag/loader.py`
- 遍历 `data/raw`，按扩展名映射 doc 类型（`.ttl/.owl→ontology`、`.md→docs`、`.yaml→api_spec`、
  `.json/.jsonld→example`、`.txt→notes`），跳过 `.meta.json`。
- 读 sidecar 覆盖 `source_name/url/version/document_type`。
- doc 类型 → 初始 `chunk_type`（`_doc_kind_to_chunk_type`）。
- 文件不可读/目录不存在都安全跳过（不崩）。

### 8.3 切块 `rag/chunker.py`（domain-aware，核心差异化）
按 `chunk_type` 选策略，**每个策略都有 size 兜底**，坏输入不会中断摄取：
| chunk_type | 策略 | 实现 |
|---|---|---|
| class_definition（本体） | rdflib 解析，每个 owl:Class/Property 一块 | 取 `rdfs:label`/`rdfs:comment`，local name 作 entity |
| api（openapi） | 每个 (path, method) 一块 | yaml 解析 paths |
| example（jsonld） | 整个 payload 一块 | — |
| concept/general（markdown） | 按标题切，再按字数（1200 上限）切 | 正则切 H1-H6 |
- `_chunk_id`：`sha1(source::key)` 前 16 位，稳定可复算。

### 8.4 摄取服务 `rag/ingest.py`
```python
run_ingest(source_dir, reset, retriever):
    if reset: retriever.reset()
    docs   = load_documents(source_dir)
    chunks = glossary_chunks() + chunk_documents(docs)   # 永远带 glossary
    indexed = retriever.upsert(chunks)
    return IngestResponse(documents_loaded, chunks_created, chunks_indexed)
```
- `POST /ingest` 只是它的薄封装。

### 8.5 实测验收
```
docs loaded: 4 → chunks: 13
by type: {api:3, example:1, concept:4, class_definition:4, property_definition:1}
```
说明四种策略都生效。

---

## 9. 前端实现

### 9.1 契约镜像 `lib/api.ts`
TypeScript 类型严格对应后端 `models/chat.py`（`ChatResponse/Source/QueryType`）。
`sendChat(message)` POST `${NEXT_PUBLIC_API_BASE_URL}/chat`。**字段名是硬契约**，与后端同改同步。

### 9.2 组件
- `Sidebar.tsx`：New Chat、Example Questions（点击直接发送）、ONE Record Concepts（拼成
  "What is X?"）、JSON-LD Generator 入口。常量在 `lib/constants.ts`。
- `Message.tsx`：用户气泡 / 助手气泡；助手气泡含 query_type 标签、related_concepts 标签、
  JsonLdViewer、Sources。
- `JsonLdViewer.tsx`：深色代码块格式化展示 `structured_output`。
- `Sources.tsx`：列出来源（source_name — section_title，可选外链）。
- `app/page.tsx`：客户端组件，管理 `turns` 状态、输入、loading、自动滚动；后端不可达时给出
  友好提示（提醒是否启动后端 / 是否 ingest）。

### 9.3 构建
`output: "standalone"`（next.config.mjs）配合多阶段 Dockerfile 产出最小运行镜像。
`npm run build` 通过即代表 TS 类型与页面预渲染都 OK。

---

## 10. 运行、测试与验证

### 10.1 后端（离线，无密钥）
```bash
cd backend
uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
# 另开终端：
curl -X POST localhost:8000/ingest
curl -s -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What is a Piece in ONE Record?"}'
```

### 10.2 切真实模型（举例 Qwen）
在 `.env`：
```bash
LLM_PROVIDER=qwen
LLM_MODEL=qwen-plus
LLM_API_KEY=sk-xxx
EMBEDDING_PROVIDER=qwen
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_API_KEY=sk-xxx
EMBEDDING_DIM=1024     # 必须与模型实际维度一致！
```
重启后端即可，**业务代码零改动**。

### 10.3 测试
```bash
cd backend
EMBEDDING_DIM=256 uv run pytest -q     # 9 passed
```
`conftest.py` 强制 `LLM_PROVIDER=local / EMBEDDING_PROVIDER=local / QDRANT_URL=:memory: / EMBEDDING_DIM=256`，
并提供 `retriever` / `ingested_retriever` 两个 fixture。

### 10.4 已验证结果（实测）
- 单测 9 passed。
- 全 HTTP 链路（TestClient）：health → ingest(17 glossary chunks) → chat(带来源) → jsonld 合法。
- domain-aware chunking：4 类策略均生效。
- 真实 Qdrant（docker 起容器）：4 docs / 30 chunks 写入，分类与来源正确。
- 前端 `npm run build` 通过。

### 10.5 前端
```bash
cd frontend
npm install && npm run dev     # http://localhost:3000
```

---

## 11. Docker 与部署

`docker-compose.yml` 三服务：
- `qdrant`：暴露 6333，带 healthcheck，数据卷 `qdrant_storage`。
- `backend`：build `./backend`，环境变量把 `QDRANT_URL` 指向 `http://qdrant:6333`，
  挂载 `./data` 只读，`depends_on: qdrant healthy`。
- `frontend`：build `./frontend`，`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`，依赖 backend。

```bash
cp .env.example .env          # 需要真实模型就填 key
docker compose up --build
curl -X POST localhost:8000/ingest
# backend :8000 / frontend :3000 / qdrant :6333
```
注意：`backend` 的 `Dockerfile` 用 `python:3.11-slim` + 复制 `uv` 二进制安装依赖；
`frontend` 用多阶段 `node:20-alpine` 产出 standalone。

---

## 12. 评估（Evaluation）

- `data/eval/questions.yaml`：12 题，覆盖 concept/relationship/api/jsonld，每题带
  `expected_keywords`，jsonld 题带 `expects_jsonld: true`。
- `scripts/evaluate_rag.py`：reset 摄取后逐题跑 `pipeline.answer`，统计：
  检索命中率、来源覆盖、答案非空率、JSON-LD 合法率、关键词命中率。
  **硬门槛**（检索/非空/JSON-LD 合法 = 100%）决定 PASS/FAIL。
```bash
cd backend && uv run python ../scripts/evaluate_rag.py
# RESULT: PASS（检索/来源/非空/JSON-LD 100%，关键词 90%）
```
> 关键词没满分是因为离线 local LLM 只抽取 top-2 上下文；接真实 LLM 会显著提升。这正是 eval 的价值：
> 把"玩具"变成可量化的"工程"。

---

## 13. 扩展方向（v0.2 / v0.3）

代码里已留好"缝"，扩展时不必大改：
- **`reranker.py` 是 no-op**：v0.2 在此接 cross-encoder / LLM rerank，调用点不变。
- **`Retriever` 抽象**：可加 entity-first / 混合检索实现。
- **`classify_query` 规则**：可替换为 LLM 分类器，签名不变。

路线已经调整为“先补知识底座，再扩功能”：
- **前置任务：数据底座扩充**：导入官方 ONE Record repo/spec/ontology/OpenAPI/JSON-LD examples，
  以及 NE:ONE docs/config/examples。见 [docs/data_source_plan.md](docs/data_source_plan.md)。
- **v0.2.1 本体感知检索验证**：在更完整官方资料上验证并收紧 ontology-aware retrieval。
- **v0.2.2 NE:ONE implementation knowledge**：回答 setup、config、payload、排错问题。
- **v0.2.3 ALH 叙事**：回答"对象如何落到 Bronze/Silver/Gold"。
- **v0.2.4 前端升级**：流式对话 UI，但前提仍是知识底座更扎实。
- **v0.2.5 RecordForge 集成**：pipeline 识别"生成 N 条合成数据"→ 调 RecordForge → JSON-LD。
- **v0.3**：认证、会话记忆、source versioning、OpenTelemetry、评估面板、三大 connector。

---

## 14. 常见问题与排错

| 现象 | 原因 / 解决 |
|---|---|
| `uv pip install -e` 报 `Readme file does not exist` | `backend/README.md` 必须存在（pyproject 引用它） |
| `/chat` 答案像"复述上下文" | 当前是 `local` LLM（抽取式）。设 `LLM_PROVIDER` + `LLM_API_KEY` 切真实模型 |
| Qdrant 维度报错 / 检索异常 | `EMBEDDING_DIM` 与 embedding 模型实际维度不一致；换模型要同步改 |
| `reset_index.py` 用内存库"没效果" | `:memory:` 每个进程独立，重置不跨进程持久；连真实 `QDRANT_URL` 才有意义 |
| 前端报"Could not reach backend" | 后端没起 / CORS / `NEXT_PUBLIC_API_BASE_URL` 不对；并确认已 `POST /ingest` |
| 切了 provider 但没生效 | 确认改的是后端进程的环境变量并重启；`get_*_provider()` 是进程内单例 |
| 本体 `.ttl` 没切出 class | 文件非合法 turtle 或无 owl:Class；chunker 会 size 兜底，检查 rdflib 解析日志 |
| 摄取 chunks 偏少 | markdown 无标题会整篇按字数切；想要更细就加标题层级 |

---

### 一句话总结
按 Phase 0→10 顺序做，守住"离线优先 / Provider 抽象 / 关注点分离 / JSON-LD 模板化"四条原则，
每步用对应验收命令确认，就能稳定复刻出这套 production-minded 的 RecordChat v0.1。
