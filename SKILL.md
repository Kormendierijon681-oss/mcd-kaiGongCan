---
name: mcd-kaiGongCan
description: 麦麦开工餐——麦当劳多人拼单优化器。输入人数、人均预算、口味禁忌（不吃辣/不吃牛）与就餐方式，自动走麦当劳 MCP 完整链路（搜门店→拉菜单→过滤禁忌→多样性配餐→算价），输出每人一份的不重复组合、预计总支出、剩余空间与加购建议。当用户说"我们 N 个人想吃麦当劳""帮我配一单麦当劳""工地/加班拼单""人均预算 X 元点麦当劳""多人拼单分摊"时使用。需要 MCD_MCP_TOKEN 环境变量；无 Token 时可用 demo 模式离线演示。
---

# 麦麦开工餐 · 多人拼单优化

## 何时使用
- 多人（2-20 人）拼单点麦当劳，需要控制人均预算
- 有口味禁忌（不吃辣/不吃牛）需要统一处理
- 工地收工、加班、值班、班级聚餐等"一群人"场景

## 何时不用
- 单人点餐（直接用麦当劳 MCP 的 query-meals 即可）
- 需要营养配餐（用 list-nutrition-foods）

## 使用步骤

### 离线演示（无 Token）
python3 scripts/mcd_mcp.py demo --people 4 --budget 30 --no-spicy

### 真实链路
export MCD_MCP_TOKEN=你的Token
python3 scripts/mcd_mcp.py stores --city 成都 --keyword 麦当劳
python3 scripts/mcd_mcp.py meals  --store 3450336
python3 scripts/mcd_mcp.py plan   --store 3450336 --people 4 --budget 30 --no-spicy --no-beef

### 在 WorkBuddy 对话中
配置 mcp-config.example.json 后直接说：
「我们 6 个人人均 25，两个不吃辣，成都到店自取，帮我配一单麦当劳」
Agent 走 MCP 链路：now-time-info → query-nearby-stores → query-meals → query-meal-detail → plan_combo → query-store-coupons → calculate-price

## 关键规则
1. city 与 keyword 必须同时传给 query-nearby-stores（只传其一报 600058）
2. 菜单名称要逐个 query-meal-detail 取（items 顶层只有 code）
3. 多样性优先：每人不同，价值从高到低轮转；人数超过不重复数才允许重复
4. create-order 属交易动作：必须用户逐项确认后才调用，支付由用户完成
5. 频率限制 600 次/分钟

详见 MCP_INTEGRATION.md 与 references/tools.md。
