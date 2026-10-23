# 麦当劳 MCP 工具清单（35 个，2026-10-23 实测）

> 来源：`tools/list` 实测返回。标注 ★ 的是本项目调用链使用的工具。

## 点餐链路
| 工具 | 用途 | 备注 |
|---|---|---|
| ★ query-nearby-stores | 到店搜门店 | ⚠️ city+keyword 必须同传 |
| ★ query-meals | 门店菜单 | code+tags，名称需逐个查详情 |
| ★ query-meal-detail | 餐品详情 | 响应含官方输出格式要求 |
| query-nearby-stores(beType=5) | 得来速 | |
| delivery-query-addresses | 外送地址列表 | 无参 |
| delivery-create-address | 新增地址 | |
| delivery-query-stores | 外送门店 | |
| ★ calculate-price | 算价（含券） | items[].couponId 逐项挂券 |
| ★ create-order | 创建订单 | 建单在人、支付在人手 |
| cancel-order | 取消订单 | |
| query-order / order-list | 订单查询 | |

## 优惠与账户
| 工具 | 用途 |
|---|---|
| query-store-coupons ★ | 门店可用券 |
| query-my-coupons | 卡包券 |
| available-coupons | 麦麦省可领券 |
| auto-bind-coupons | 一键领券 |
| query-my-account | 积分账户 |
| query-promotions | 企业团餐促销 |
| query-meal-assistance | 团餐助餐服务 |

## 商城与活动
| 工具 | 用途 |
|---|---|
| mall-points-products / mall-product-detail | 积分商城 |
| mall-create-order / mall-order-list / mall-order-detail | 商城订单 |
| campaign-calendar | 营销日历 |
| query-party-city / query-party-store / query-party-store-date / query-party-store-session / party-order-create | 主题派对 |
| query-lottery-info / draw-lottery / query-my-prizes | 积分抽奖 |

## 辅助
| 工具 | 用途 |
|---|---|
| ★ now-time-info | 服务器时间 |
| list-nutrition-foods | 营养成分 |
| query-survey-coupon | 问卷券 |

---

## 实测坑（官方文档未写）

1. **query-nearby-stores 必须 city+keyword 同传**，只传其一报 `600058`（含只传 city 的情况）
2. 响应文本 = 说明 + 数据混合，JSON 可能不在代码块里，解析要两级回退
3. query-meals 商品分散两处 + 混有字符串占位项
4. 无状态服务：无 mcp-session-id
5. query-meal-detail 的响应内嵌「输出格式要求」——服务端在约束 LLM 的展示行为（supportModify/isDefault 规则），集成时应遵循
6. 频率限制 600 次/分钟，超限 429
