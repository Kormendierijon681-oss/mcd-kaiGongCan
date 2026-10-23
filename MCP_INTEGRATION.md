# MCP_INTEGRATION · 麦当劳 MCP 集成说明

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| 服务地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 认证方式 | `Authorization: Bearer <MCP Token>` |
| 服务版本 | mcd-mcp 1.0.0（initialize 实测返回） |
| 会话模型 | 无状态（响应无 `mcp-session-id`，每次调用独立） |

## 2. 实际使用的 Tool（按调用链顺序）

| # | Tool | 用途 | 输入要点 |
|---|---|---|---|
| 1 | `now-time-info` | 取服务器时间（判断早餐/正餐时段） | 无参 |
| 2 | `query-nearby-stores` | 搜门店 | `beType=1`（到店）+ `searchType=2`（按位置）+ **city 与 keyword 必须同时传** |
| 3 | `query-meals` | 拉门店菜单 | `storeCode` + `orderType=1` + `beType=1` |
| 4 | `query-meal-detail` | 逐个取餐品名称/价格/可特调 | `storeCode` + `orderType` + `beType` + `mealCode` |
| 5 | `query-store-coupons` | 查该门店可用券 | `storeCode` + `orderType` + `beType` |
| 6 | `calculate-price` | 算优惠后总价 | `items[]` + 门店参数（支持逐项挂 `couponId`） |
| 7 | `create-order`（可选） | 生成订单与支付链接 | 用户在对话中逐项确认后才调用 |

## 3. 调用流程

```
用户输入（人数/人均预算/禁忌/到店或外送）
   │
   ├─① now-time-info            → 判断时段，过滤未营业门店
   ├─② query-nearby-stores      → 选门店（city+keyword 同传，见踩坑1）
   ├─③ query-meals              → 拉全量菜单（code 列表）
   ├─④ query-meal-detail        → 逐个补名称/价格（items 顶层只有 code，见踩坑2）
   ├─⑤ 本地优化引擎 plan_combo  → 多样性配餐 + 预算约束 + 禁忌过滤
   ├─⑥ query-store-coupons      → 查可用券
   ├─⑦ calculate-price          → 真实算价（含优惠）
   └─⑧ create-order（可选）     → 用户确认后下单
```

前三步与优化引擎已实跑（见 [evidence-real.md](evidence-real.md)，含服务端 traceId）；
⑦⑧ 属交易动作，设计上**必须由用户在对话中逐项确认后**才会执行——与官方"Agent 建单、支付在人手"的责任切分一致。

## 4. 业务价值

**目标用户**：工地班组、加班项目组、值班团队、班级/社团聚餐——一切"多人 + 预算 + 口味不一"的麦当劳拼单场景。

**解决的真实痛点**：

| 痛点 | 传统做法 | 本项目 |
|---|---|---|
| 意见收集 | 逐个问"你吃什么"，微信刷屏 | 输入人数+预算+禁忌，一次出全单 |
| 预算失控 | 点完才发现超支 | 人均预算硬约束，输出预计总支出与剩余空间 |
| 口味遗漏 | 退单重下 | 禁忌过滤（辣/牛等）在配餐前完成 |
| 单调重复 | 图省事全员同款 | 多样性引擎保证每人不同（价值从高到低轮转） |
| 优惠遗漏 | 不看券直接下单 | 链路内建 `query-store-coupons` → `calculate-price` |

**与榜单头部项目的差异**：现有高分项目（省钱/比价/营养）全部解决"一个人"的问题；本项目解决"一群人"的问题——多人拼单 + 分摊方向在 104 个进榜项目中尚无头部作品。

## 5. 实测踩坑（官方文档未写，本项目补充）

1. `query-nearby-stores` 的 `city` 与 `keyword` **必须同时传**，缺一即报 `600058 城市名或者关键词不能为空`；
2. 响应 `content[0].text` 为「字段说明 + JSON 数据」混合文本，且 JSON 不一定在规范代码块内，解析需容错回退；
3. `query-meals` 的商品分散在 `data.meals` 与 `data.categories[].meals` 两处，且混有非 dict 的占位字符串项，需过滤；
4. 菜单 items 顶层仅 `code`+`tags`，名称/价格需逐个 `query-meal-detail`；
5. `query-meal-detail` 响应中服务端附带「输出格式要求」（supportModify 标注、isDefault 搭配、特调交互），**官方在用服务端提示词约束 LLM 行为**——集成时应遵循，否则输出与 App 体验不一致。