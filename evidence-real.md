# 真实调用证据 evidence-real

> 所有调用均通过 Streamable HTTP 直连 `https://mcp.mcd.cn`，
> 认证头 `Authorization: Bearer <MCP Token>`。
> 以下为 2026-10-23 联调实录，traceId 均为服务端原样返回。

| 更新日期 | 记录条数 | 结论 |
|---|---|---|
| 2026-10-23 | 6 次 | 官方 MCP 真实连通，35 个工具可用，完整点餐链路走通 |

---

## 1. initialize 握手

**请求**
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"mcd-kaiGongCan","version":"1.0.0"}}}
```

**响应（原文）**
```json
{"jsonrpc": "2.0","id":1,"result":{"capabilities":{"tools":{}},"protocolVersion":"2025-03-26","serverInfo":{"name":"mcd-mcp","version":"1.0.0"}}}
```

## 2. tools/list —— 35 个工具全部返回

工具清单（名称）：cancel-order, query-party-store, auto-bind-coupons, delivery-create-address, create-order, query-meals, query-meal-detail, calculate-price, query-survey-coupon, query-lottery-info, query-my-prizes, mall-create-order, mall-points-products, query-party-store-date, query-party-store-session, campaign-calendar, query-store-coupons, query-order, query-promotions, mall-order-list, query-nearby-stores, order-list, list-nutrition-foods, delivery-query-addresses, delivery-query-stores, query-my-account, query-party-city, party-order-create, query-my-coupons, mall-order-detail, available-coupons, now-time-info, query-meal-assistance, draw-lottery, mall-product-detail

## 3. now-time-info 真实调用

**响应片段（原文）**
```
# API Response Information
...
- **data**: 服务器时间信息 (Type: object)
```
✅ 200，真实服务器时间返回。

## 4. query-nearby-stores（成都 · 到店自取）

**请求**
```json
{"name":"query-nearby-stores","arguments":{"beType":1,"searchType":2,"city":"成都","keyword":"麦当劳"}}
```

**响应（原文节选，traceId: 99e831bffd433ef410d23bb6cf42da7e）**
```json
{"success":true,"code":200,"message":"请求成功","datetime":"2026-10-23 22:50:57",
 "data":[{"storeCode":"3450336","storeName":"麦当劳成都成华区鹏瑞利东站广场餐厅",
          "address":"丹景山路28号鹏瑞利国际医疗健康中心A2-01-01a商铺","distance":21,
          "businessStatus":true,"businessStartTime":"07:00","businessEndTime":"00:00",...}]}
```

返回成都 5 家真实门店（成华区鹏瑞利东站广场 / 成都东站出发层 / 迎晖路 / 凯德魅力城 / 大凉山路）。

## 5. query-meals（门店 3450336 菜单）

**响应要点（原文数据）**
- 15 个分类，有效餐品编码 127 个（另含 116 个字符串占位项）
- items 顶层字段仅 `code` + `tags`，餐品名称需逐个调 `query-meal-detail`

原始响应全文见 [02-meals-raw.json](02-meals-raw.json)（29,922 字符）。

## 6. query-meal-detail（code 521956）

响应包含官方输出格式要求（supportModify 标注规则、isDefault 默认搭配、特调选项交互规范），
说明**服务端在引导 LLM 的输出行为**——这是本 MCP 一个值得注意的设计。

---

## 实测踩坑记录（官方文档未写）

| # | 现象 | 根因与结论 |
|---|---|---|
| 1 | `query-nearby-stores` 只传 `city` 报 `600058 城市名或者关键词不能为空`；只传 `keyword` 同样报错 | **city 与 keyword 必须同时传**。仅 `city`（无 keyword）也报错，属服务端校验与文档不符 |
| 2 | `searchType=1`（收藏餐厅）返回 `600050 收藏餐厅列表为空` | 新账号无收藏，正常；生产中应先引导用户使用 searchType=2 |
| 3 | 响应 JSON 前有说明文字、代码块包裹不规范 | 解析必须容错：先找 ```json 块，失败再按 `"data"` 键定位 |
| 4 | `query-meals` 的 `data.meals` 与 `data.categories[].meals` 两处都有商品 | 取并集，且要过滤掉非 dict 的占位字符串项 |
| 5 | 无 `mcp-session-id` 响应头 | 无状态实现，每次调用独立，无需握手维持 |

---

## 复现方式

```bash
export MCD_MCP_TOKEN=你的Token
python3 scripts/mcd_mcp.py stores --city 成都 --keyword 麦当劳
```

原始响应文件（01-stores-raw.json / 02-meals-raw.json / 03-meal-detail-raw.json）随仓库附带，
其中已做脱敏：不含 Token、不含个人收货地址。