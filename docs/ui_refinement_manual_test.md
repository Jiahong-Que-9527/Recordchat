# RecordChat UI Refinement Manual Test Guide

这份文档用于你手动验证当前前端 UI refinement / interaction polish 的真实效果。

目标不是只看“能不能用”，而是确认：

- 页面是否稳定加载
- streaming 是否顺畅
- 回答结构是否清晰
- Inspector 是否好用
- JSON-LD / sources / related concepts 的展示是否有高级感
- 输入、滚动、折叠、移动端等交互是否自然

---

## 1. 测试前准备

确认你已经有可用的 API 配置：

- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_BASE_URL`

建议先检查根目录 `.env` 是否已经填好。

---

## 2. 启动方式

优先使用 Docker Compose 联调，因为这是最接近完整演示环境的方式。

在仓库根目录运行：

```bash
docker compose up --build -d
```

然后执行 ingest：

```bash
curl -X POST http://127.0.0.1:8000/ingest
```

你应该看到类似结果：

```json
{"status":"ok","documents_loaded":714,"chunks_created":10502,"chunks_indexed":10502}
```

如果想确认服务状态：

```bash
curl -s http://127.0.0.1:8000/health
```

---

## 3. 需要打开的页面

### 前端主页面

浏览器打开：

`http://localhost:3000`

### 后端文档页面

浏览器打开：

`http://localhost:8000/docs`

后端文档不是本轮重点，但当你怀疑接口异常时可以快速看。

---

## 4. 首屏应该观察什么

进入 `http://localhost:3000` 后，先不要急着提问，先检查这几个点：

### 页面结构

你应该看到：

- 左侧 `Sidebar`
- 中间主聊天区
- 右侧 `Conversation Inspector`
- 底部输入区

### 首屏内容

你应该看到：

- 顶部标题
- 空状态卡片
- suggested prompts
- 左侧 example questions
- 左侧 ONE Record concepts

### 视觉和交互感

重点观察：

- 是否有明显“拼装感”或“廉价感”
- 留白是否舒服
- 边框/阴影是否太重或太乱
- Inspector 是否像一个独立分析面板，而不是杂乱的信息块

如果首屏就让你感觉“挤、乱、平”，记下来。

---

## 5. 核心联调问题清单

按下面顺序测试，不要一上来乱跳。

### Case 1: 概念问答

输入：

`What is ONE Record?`

你要观察：

- 点击发送后，是否迅速进入 streaming 状态
- 是否出现 `Live Response` 样式的提示
- assistant 消息是否一段段流出来，而不是卡很久后一次性出现
- 回答结束后，Inspector 是否更新
- `Query Type` 是否显示为概念类
- `Sources` 是否显示正常

重点主观判断：

- streaming 是否“顺”
- 回答面是否好读
- source cards 是否像“证据卡片”而不是列表

### Case 2: 数据模型概念

输入：

`What is a LogisticsObject in ONE Record?`

你要观察：

- assistant 卡片头部层次是否清楚
- `Related Concepts` 是否出现
- related concept chips 是否容易扫读
- Inspector 里的 `Related Concepts` 区是否有价值

重点主观判断：

- 信息层次是否清楚
- 你是不是一眼能看懂“主回答”和“结构化辅助信息”的关系

### Case 3: Ontology / relationship

输入：

`What properties connect Shipment to Piece in the ONE Record ontology?`

你要观察：

- `Query Type` 是否是 ontology 类
- 是否能稳定给出 ontology 风格的回答
- Sources 是否偏 ontology
- Inspector 的存在是否真的帮助理解

重点主观判断：

- 这类偏复杂问题时，右侧 panel 是否提升理解效率
- 页面有没有显得太重、太花或者太散

### Case 4: JSON-LD

输入：

`Generate a JSON-LD example for a Piece.`

你要观察：

- 回答区是否正常出现说明文本
- Inspector 是否出现 `Structured Output`
- JSON-LD viewer 是否默认可读
- `Structured` / `Raw` 切换是否自然
- `Copy` 是否可用

重点主观判断：

- JSON-LD viewer 是否像开发者工具面板
- 结构视图是否真的有帮助
- 原始视图是否适合复制和检查

### Case 5: NE:ONE implementation

输入：

`How do I start NE:ONE locally with docker compose?`

你要观察：

- implementation 类问题的回答是不是明显更像开发者支持
- Sources 是否命中 NE:ONE 文档
- Query type badge 是否正确

重点主观判断：

- 这种“实操型回答”在当前 UI 里是否足够专业
- 你会不会愿意真的拿这个页面当开发助手来用

### Case 6: Workflow intent

输入：

`Generate 5 synthetic shipments with pieces`

你要观察：

- 是否识别为 `synthetic_data_generation`
- 是否明确提示 RecordForge 还未接入
- 是否是“优雅降级”，而不是答非所问

重点主观判断：

- 系统是否在“能力边界”上表现得专业
- 这种未完成功能的呈现是否让人信任，而不是让人失望

---

## 6. 输入区专项测试

单独测试输入区，不看答案内容，只看手感。

### Enter 发送

输入一行问题，直接按 `Enter`。

预期：

- 立即发送
- 不会换行

### Shift+Enter 换行

输入多行内容时按 `Shift+Enter`。

预期：

- 正常换行
- 不会发送

### 禁用状态

在 streaming 过程中观察发送按钮。

预期：

- 按钮应禁用
- 不应允许重复乱发

### Placeholder / toolbar

观察底部输入区：

- 是否像成熟产品的 composer
- 提示文案是否清楚但不吵
- 输入框高度、留白、按钮位置是否舒服

---

## 7. Inspector 专项测试

这轮 refinement 的重点之一就是 Inspector，所以要单独测。

### 折叠 / 展开

点击这些 section：

- `Query Type`
- `Related Concepts`
- `Sources`
- `Structured Output`

预期：

- 动画自然
- 不突兀
- 展开后内容稳定
- 收起后布局不乱跳

### 信息密度

重点感受：

- section 分层是否合理
- summary stats 是否有帮助
- 是不是看着“像工具”，而不是“像原型”

---

## 8. Streaming 体感专项测试

这个测试非常重要。

重复问 2 到 3 个普通问题，专门盯住 streaming 过程看。

重点观察：

- token 是否连续输出
- 有无明显卡顿后突然一大段跳出
- assistant card 是否在 streaming 中保持稳定
- streaming 提示是否增强了“正在工作”的感知

如果你发现以下情况，记录下来：

- 首 token 很慢
- 中间经常停顿很久
- 文本区域在 streaming 中闪烁
- Inspector 更新时视觉跳变太大

---

## 9. 移动端测试

打开浏览器开发者工具，切换到手机尺寸。

推荐尺寸：

- iPhone 13 / 14
- 390 x 844 左右

你要测试：

- 左侧内容是否压得太厉害
- 输入区是否还能舒服使用
- Inspector 在移动端的内嵌呈现是否合理
- message 卡片宽度是否舒服
- JSON-LD / code block 是否还能横向查看

重点主观判断：

- 移动端是“能用”
  还是
- 移动端是“真的像产品”

---

## 10. 你应该怎么记录反馈

建议按下面格式记：

```md
## 问题标题

页面：
- 首页 / 消息区 / Inspector / JSON-LD / 输入区 / 移动端

复现步骤：
1. 打开什么页面
2. 输入什么问题
3. 做了什么动作

实际现象：
- ...

预期感受：
- ...

优先级：
- 高 / 中 / 低
```

例如：

```md
## Inspector 折叠时节奏还是偏硬

页面：
- Inspector

复现步骤：
1. 打开 localhost:3000
2. 提问 What is ONE Record?
3. 反复展开/收起 Sources

实际现象：
- 收起时有点太快
- 缺少更柔和的过渡

预期感受：
- 更像高级 analysis panel 的折叠动效

优先级：
- 中
```

---

## 11. 联调结束后的结论怎么判断

如果下面这些大部分都成立，就说明这轮 refinement 是成功的：

- 你愿意把这个页面给别人看，不会觉得“只是工程页面”
- 回答、sources、JSON-LD、Inspector 的关系你一眼能懂
- streaming 有“产品感”，不只是“技术上在流”
- JSON-LD viewer 像开发者工具而不是普通代码框
- 移动端不只是勉强可用
- 整体视觉给人的感觉是“专业、克制、值钱”

如果还达不到，那下一轮就应该继续打磨：

- streaming 节奏
- answer surface
- Inspector 细节
- JSON-LD / code 面板
- workflow result 的未来展示方式

---

## 12. 联调完成后告诉我什么

你联调完后，最好直接把反馈按这三类告诉我：

1. **最喜欢的 3 个点**
2. **最不满意的 3 个点**
3. **最像“高级产品”的地方 / 最像“原型”的地方**

这样我下一轮就能非常精准地继续收。 
