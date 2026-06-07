Bill，RecordChat 第一阶段不要贪多。目标是先做成一个**ONE Record 标准知识 + 示例数据 + API 问答助手**。下载清单我建议这样分层：

## 0. 总原则

RecordChat 需要的数据分三类：

1. **标准文档**：让它懂 ONE Record 是什么、API 怎么设计、数据模型怎么组织。
2. **结构化规范文件**：让它能回答类、属性、关系、JSON-LD、ontology、OpenAPI 这类技术问题。
3. **示例数据与代码**：让它能解释真实 payload、NE:ONE server、请求流程、错误排查。

这对你的 100k+ 求职是有帮助的，因为它不是普通 RAG demo，而是一个**行业标准 × 数据平台 × AI interface** 的作品。更高一层看，RecordChat 应该成为你 ALH/RecordMind 体系的第一个入口产品。

---

# RecordChat 数据下载清单

## A. 必须下载：ONE Record 官方标准资料

### 1. IATA-Cargo/ONE-Record GitHub 仓库

这是最核心的数据源。官方仓库包含 ONE Record 的 **data model、ontology、API、security specifications**，并且 README 说明 `working_draft` 是最新工作版本。([GitHub][1])

需要下载：

```text
IATA-Cargo/ONE-Record
├── working_draft/
├── 2025-07/
├── 2023-12/
├── ontology files
├── API specification
├── Security specification
├── changelog / release notes
└── examples if available
```

用途：

```text
RecordChat 回答：
- ONE Record 是什么？
- data model 有哪些核心类？
- API endpoint 怎么设计？
- security 机制是什么？
- 版本之间有什么变化？
- JSON-LD payload 应该怎么理解？
```

优先级：**P0，必须下载**

---

### 2. ONE Record 官方在线 specification 文档

ONE Record API specification 定义了一个语言无关的标准接口，用于 ONE Record Web API 与 Data Model 的交互。([iata-cargo.github.io][2])

建议下载这几个版本：

```text
https://iata-cargo.github.io/ONE-Record/development/
https://iata-cargo.github.io/ONE-Record/2025-07/
https://iata-cargo.github.io/ONE-Record/2023-12/
```

用途：

```text
- 做 RAG 的主要知识库
- 让 RecordChat 能回答 implementation-level 问题
- 对比 stable version 和 development version
```

优先级：**P0，必须下载**

---

### 3. IATA ONE Record 官方介绍页

IATA 官方介绍页说明 ONE Record 标准包括 data model specification、API specification，并强调 JSON-LD 用于数据交换。([IATA][3])

需要下载：

```text
IATA ONE Record overview page
IATA ONE Record presentation PDF
ONE Record technical insight PDFs
```

用途：

```text
- 用于回答非技术用户的问题
- 用于生成 executive summary
- 用于你以后写 blog / portfolio / ALH narrative
```

优先级：**P0，必须下载**

---

## B. 必须下载：Ontology / JSON-LD / API 结构文件

### 4. ONE Record Data Model Ontology

ONE Record API ontology 是 ONE Record API 标准背后的数据模型。([onerecord.iata.org][4])

需要下载：

```text
ontology.ttl
ontology.rdf
ontology.jsonld
class diagrams
data model diagrams
vocabulary definitions
```

用途：

```text
RecordChat 回答：
- Shipment / Waybill / LogisticsObject / Company / Piece 是什么关系？
- 某个 class 有哪些 property？
- 某个 property 的 domain/range 是什么？
- JSON-LD 中 @context / @type / @id 如何理解？
```

优先级：**P0，必须下载**

---

### 5. ONE Record API Ontology / API Class Diagram

2025-07 API Security 文档中提到，ONE Record API ontology 提供 API 数据模型使用的数据类和词汇，class diagram 展示 API ontology 的类、属性和关系。([iata-cargo.github.io][5])

需要下载：

```text
API ontology
API class diagram
Notification model
Subscription model
Logistics Object API model
Access delegation / security model
```

用途：

```text
- 支持 API 问答
- 支持 endpoint + object relationship 解释
- 支持以后 RecordMind 的 workflow 设计
```

优先级：**P0，必须下载**

---

### 6. OpenAPI Specification

IATA Developer Portal 有 ONE Record Standard API Documentation，说明它描述了 ONE Record API implementation 的 endpoint structure。([api.developer.iata.org][6])

需要下载：

```text
openapi.yaml
openapi.json
endpoint docs
request / response schema
auth / security schema
```

用途：

```text
RecordChat 回答：
- 怎么 create logistics object？
- 怎么 retrieve object？
- 怎么做 notification？
- 怎么订阅 event？
- endpoint 参数有哪些？
```

优先级：**P0，必须下载**

---

## C. 必须下载：NE:ONE 相关资料

### 7. NE:ONE GitLab 仓库

NE:ONE 是 Open Logistics Foundation 的 ONE Record server 实现，项目页说明它兼容 IATA ONE Record API description v2.2 和 data model v3.2.0。([GitLab][7])

需要下载：

```text
WG-DigitalAirCargo / NE-ONE GitLab repository
├── README
├── docs
├── API docs
├── configuration files
├── example payloads
├── Docker / deployment files
├── source code
└── tests
```

用途：

```text
RecordChat 回答：
- NE:ONE 怎么启动？
- 配置项是什么意思？
- 如何创建 ONE Record object？
- 如何和 server API 交互？
- 报错怎么排查？
```

优先级：**P0，必须下载**

这是你现在最应该绑定的资料，因为你马上要参与 NE:ONE public review。RecordChat 如果能围绕 NE:ONE 做出问答能力，你就不只是“学习 ONE Record”，而是在准备进入社区讨论。

---

## D. 强烈建议下载：示例 JSON-LD / Payload / Test Data

### 8. ONE Record JSON-LD 示例文件

IATA 的技术资料提到，ONE Record 使用 Linked Data 和 JSON-LD，最新 ontology 可在 GitHub 找到，也有 ONE Record compliant JSON-LD files。([IATA][8])

需要下载：

```text
shipment example JSON-LD
waybill example JSON-LD
piece example JSON-LD
logistics object example JSON-LD
company / location / event examples
notification examples
subscription examples
error response examples
```

用途：

```text
RecordChat 回答：
- 这个 JSON-LD payload 表示什么？
- 这个 object 合不合规？
- 哪些字段缺失？
- 如何把普通 shipment 数据转成 ONE Record JSON-LD？
```

优先级：**P0/P1，强烈建议第一阶段就下载**

---

### 9. Hackathon / Pilot / Demo 示例

ONE Record 2025-07 release notes 提到，hackathons、pilots 和 live implementations 的反馈是标准改进的重要来源。([GitHub][9])

需要下载：

```text
ONE Record hackathon materials
pilot examples
demo payloads
community sample projects
tutorial notebooks
```

用途：

```text
- 增加真实场景语料
- 让 RecordChat 不只会背标准，也能解释实际使用方式
- 后续支持 RecordForge 生成 synthetic examples
```

优先级：**P1，很有价值**

---

## E. 建议下载：背景知识与行业资料

### 10. IATA ONE Record Presentation PDF

IATA presentation PDF 中说明 ONE Record 的 data model specification 提供 air cargo 行业标准数据结构，并使用 JSON-LD 促进数据集成。([IATA][10])

需要下载：

```text
IATA ONE Record presentation PDF
technical insight PDFs
business overview PDFs
```

用途：

```text
- 给非技术用户解释 ONE Record
- 写 blog / portfolio
- 准备和行业人士交流
```

优先级：**P1**

---

### 11. ONE Record community / awesome-one-record

`awesome-one-record` 是一个社区整理的 ONE Record 资源清单，适合作为扩展入口。([GitHub][11])

需要下载或记录：

```text
awesome-one-record README
linked repositories
tutorial links
community tools
demo projects
```

用途：

```text
- 找更多开源项目
- 找 examples
- 发现生态里的玩家和工具
```

优先级：**P1**

---

## F. 后续扩展：RecordChat 进阶数据源

这些不是第一天必须做，但很适合后面做成高级版本。

### 12. IATA Cargo XML / Cargo-IMP 对比资料

用途：

```text
RecordChat 回答：
- ONE Record 和 Cargo-XML 有什么区别？
- 为什么 JSON-LD / Linked Data 更适合现代数据共享？
- 传统 message-based exchange 和 ONE Record object-based exchange 的差别是什么？
```

优先级：**P2**

---

### 13. Air cargo domain glossary

需要收集：

```text
AWB / eAWB
HAWB / MAWB
ULD
shipment
piece
booking
consignment
freight forwarder
ground handler
carrier
customs
warehouse process
```

用途：

```text
- 让 RecordChat 能解释业务术语
- 降低非专业用户理解门槛
- 支撑 ALH 的行业叙事
```

优先级：**P1**

---

### 14. Lufthansa / Fraport / DHL / CHAMP / DAKOSY 公开资料

用途：

```text
- 建立德国 air cargo digitalization 背景知识
- 支撑你未来面试时谈行业趋势
- 让 RecordChat 以后能回答“ONE Record 在德国航空货运生态里有什么意义”
```

优先级：**P2**

---

# 第一阶段最小下载包

如果你现在只想马上开始，不要下载太多。先抓这 6 类：

```text
1. IATA-Cargo/ONE-Record GitHub repo
2. ONE Record 2025-07 specification docs
3. ONE Record development specification docs
4. ONE Record ontology files: ttl / rdf / jsonld
5. OpenAPI spec: yaml / json
6. NE:ONE GitLab repo + docs + examples
```

这 6 个足够做出 RecordChat v0.1。

---

# 推荐本地目录结构

你可以这样组织：

```text
recordchat-data/
├── raw/
│   ├── iata-one-record/
│   │   ├── github-repo/
│   │   ├── spec-2025-07/
│   │   ├── spec-development/
│   │   ├── ontology/
│   │   ├── openapi/
│   │   └── pdfs/
│   │
│   ├── ne-one/
│   │   ├── repo/
│   │   ├── docs/
│   │   ├── examples/
│   │   └── configs/
│   │
│   ├── examples/
│   │   ├── jsonld/
│   │   ├── shipment/
│   │   ├── waybill/
│   │   ├── piece/
│   │   └── notification/
│   │
│   └── domain-background/
│       ├── glossary/
│       ├── iata-presentations/
│       ├── cargo-xml/
│       └── industry-reports/
│
├── processed/
│   ├── markdown/
│   ├── chunks/
│   ├── metadata/
│   └── qa_pairs/
│
└── indexes/
    ├── vector_index/
    ├── keyword_index/
    └── graph_index/
```

---

# 每类数据的处理方式

| 数据类型                    | 处理方式                               | 是否进入 embedding |
| ----------------------- | ---------------------------------- | -------------- |
| HTML docs               | 转 Markdown                         | 是              |
| PDF                     | 转 Markdown / text                  | 是              |
| ontology ttl/rdf/jsonld | 保留原文件 + 提取 class/property 表        | 部分进入           |
| OpenAPI yaml/json       | 解析 endpoint/schema                 | 是，但要结构化        |
| JSON-LD examples        | 保留原始 + 生成解释文本                      | 是              |
| source code             | 只 index README/docs/tests/examples | 不建议全量代码        |
| changelog               | 保留版本信息                             | 是              |
| diagrams                | 截图 + 人工描述                          | 可选             |

---

# v0.1 下载优先级表

| 优先级 | 数据                         | 用途                   |
| --- | -------------------------- | -------------------- |
| P0  | ONE Record official repo   | 核心标准知识               |
| P0  | 2025-07 spec               | 当前稳定版本知识             |
| P0  | development spec           | 最新变化                 |
| P0  | ontology files             | 类/属性/关系问答            |
| P0  | OpenAPI spec               | API endpoint 问答      |
| P0  | NE:ONE repo/docs           | 实现层问答                |
| P1  | JSON-LD examples           | payload 解释           |
| P1  | IATA presentation PDFs     | business explanation |
| P1  | glossary                   | 业务术语解释               |
| P1  | hackathon/demo examples    | 实战场景                 |
| P2  | Cargo-XML / Cargo-IMP      | 标准对比                 |
| P2  | company/industry materials | 德国航空货运叙事             |

---

# 我的建议：你真正要做的不是“下载资料”，而是建立 4 个知识层

RecordChat 应该按这 4 层组织：

```text
Layer 1: Standard Knowledge
ONE Record 是什么，为什么存在，解决什么问题。

Layer 2: Technical Specification
Data Model / Ontology / API / Security / JSON-LD。

Layer 3: Implementation Knowledge
NE:ONE 怎么运行，怎么配置，怎么调用，怎么排错。

Layer 4: Use Case Knowledge
air cargo shipment、waybill、piece、ULD、event、notification 在真实业务里怎么用。
```

这个结构比单纯向量库更高级。你以后面试时可以说：

> I built RecordChat as a domain-specific RAG assistant for the ONE Record ecosystem. It combines official IATA standards, ontology files, OpenAPI specifications, JSON-LD examples, and NE:ONE implementation materials to support both conceptual understanding and implementation-level Q&A.

这句话非常有用。它传达的是：你不只是会 RAG，你能把 AI interface 接到一个真实行业标准和数据平台生态里。

[1]: https://github.com/IATA-Cargo/ONE-Record?utm_source=chatgpt.com "IATA-Cargo/ONE-Record: This repository contains the ..."
[2]: https://iata-cargo.github.io/ONE-Record/2023-12/?utm_source=chatgpt.com "Introduction - ONE Record Specification"
[3]: https://www.iata.org/one-record/?utm_source=chatgpt.com "ONE Record"
[4]: https://onerecord.iata.org/ns/api?utm_source=chatgpt.com "ONE Record API Ontology"
[5]: https://iata-cargo.github.io/ONE-Record/2025-07/API-Security/?utm_source=chatgpt.com "Introduction - ONE Record Specification"
[6]: https://api.developer.iata.org/iata-iata-cargo/api/one-record-standard1?utm_source=chatgpt.com "ONE Record Standard API Documentation (iata-iata-cargo)"
[7]: https://git.openlogisticsfoundation.org/wg-digitalaircargo/ne-one?utm_source=chatgpt.com "WG-DigitalAirCargo / NE-ONE · GitLab"
[8]: https://www.iata.org/contentassets/a1b5532e38bf4d6284c4bf4760646d4e/one_record_tech_insight_decentralized_architecture_with_linked_data.pdf?utm_source=chatgpt.com "Decentralized architecture with Linked Data and JSON-LD"
[9]: https://github.com/IATA-Cargo/ONE-Record/releases?utm_source=chatgpt.com "Releases · IATA-Cargo/ONE-Record"
[10]: https://www.iata.org/contentassets/a1b5532e38bf4d6284c4bf4760646d4e/iata_one_record_presentation_en.pdf?utm_source=chatgpt.com "ONE Record"
[11]: https://github.com/ddoeppner/awesome-one-record?utm_source=chatgpt.com "ddoeppner/awesome-one-record: A curated list of ..."
