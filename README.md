# 麦麦开工餐 mcd-kaiGongCan

**给工地班组、加班团队、值班人员的麦当劳多人拼单优化器。**
输入：人数、人均预算、口味禁忌。输出：每人一份的不重复组合、预计总支出、剩余空间、加购建议。

## 🎮 在线体验（打开即用，无需 Token / 无需注册）

**https://kormendierijon681-oss.github.io/mcd-kaiGongCan/**

页面内置 2026-10-23 成都门店真实菜单快照（主食 / 小食 / 饮品共 59 项），
纯前端单文件，**不发起任何网络请求**，断网也能算。点开就能配单，一键复制结果发群里。

> 参赛项目：麦当劳中国 1024 程序员节创意开发大赛
> 官方赛事仓库：[M-China/mcd-developer-innovation-challenge](https://github.com/M-China/mcd-developer-innovation-challenge)
> MCP 文档：[M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server)
>
> 同时参评：WorkBuddy「1024 造物挑战」程序员节应用创作大赛（投稿期 2026-10-21 — 11-01）

| 更新日期 | 版本 | 说明 |
|---|---|---|
| 2026-10-24 | v1.1.0 | 在线版升级：59 项真实菜单、场景预设、预算预留式配餐（保证配齐）、换一组搭配、一键复制 |
| 2026-10-23 | v1.0.0 | 首版：零依赖 MCP 客户端 + 多样性拼单引擎 + 离线演示 |

---

## 为什么做这个

看一眼赛事排行榜就知道：头部项目（mcd-saver-strategist 611★、mcd-budget-meal 512★、mcd-coupon-strategist 491★）清一色在解决**一个人的省钱问题**。

但麦当劳真正的日常大单不是一个人——是**工地上收工的一班组人、加班到九点的一个项目组、凌晨值班的一班岗**。这群人点单的真实痛点是：

1. 逐个问"你吃什么"再汇总，沟通成本高
2. 总价失控：没人知道这一单到底花了多少
3. 有人不吃辣、有人不吃牛，漏问一个就退单重下

**麦麦开工餐把"问一圈 + 凑单 + 控预算"压缩成一次输入。**

## 三秒看懂效果

```bash
python3 scripts/mcd_mcp.py demo --people 4 --budget 30 --no-spicy --no-beef
```

```
每人一份（4 人不重复）：
  巨无霸 ¥25.0 ｜ 板烧鸡腿堡 ¥24.0 ｜ 双层吉士汉堡 ¥17.5 ｜ 麦香鱼 ¥15.0
预计总支出 ¥81.5 / 预算 ¥120
剩余空间 ¥38.5 → 加购建议：麦乐鸡、中薯条、可口可乐
禁忌已过滤：辣类、牛类
```

再换 6 人 × ¥25 试试，组合完全不同——**预算和人一变，方案就变**。

## 快速开始

### 离线演示（不需要 Token，30 秒）

```bash
git clone https://github.com/<YOUR>/mcd-kaiGongCan.git
cd mcd-kaiGongCan
python3 scripts/mcd_mcp.py demo --people 4 --budget 30
```

### 真实下单链路（需要麦当劳 MCP Token）

1. 到 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 手机号登录 → 控制台 → 激活，领取 Token
2. `export MCD_MCP_TOKEN=你的Token`
3. 走完整链路：

```bash
python3 scripts/mcd_mcp.py stores --city 成都 --keyword 麦当劳   # 搜门店
python3 scripts/mcd_mcp.py meals  --store 3450336                # 拉菜单
python3 scripts/mcd_mcp.py plan   --store 3450336 --people 4 --budget 30 --no-spicy
```

## 接入 WorkBuddy / 任意 MCP Client

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer 你的Token" }
    }
  }
}
```

然后在对话里说：
> 「我们工地下班了 6 个人，人均 25，有两个不吃辣，帮我配一单麦当劳，到店自取」

Agent 会自动走：搜门店 → 拉菜单 → 过滤禁忌 → 多样性配餐 → 算价 → 给出分摊表。

## 实测踩坑（官方文档没写，全部实测得出）

| # | 坑 | 结论 |
|---|---|---|
| 1 | `query-nearby-stores` 只传 `city` 或只传 `keyword` 都报 `600058 城市名或者关键词不能为空` | **city 与 keyword 必须同时传** |
| 2 | MCP 响应 `content[0].text` 是「说明文字 + ```json 代码块」混合体 | 解析需定位代码块；`data` 分散在 `data.meals` 与 `data.categories[].meals` 两处 |
| 3 | 菜单 items 顶层只有 `code` + `tags` | 名称要靠 `query-meal-detail` 逐个取 |
| 4 | 服务端响应头无 `mcp-session-id` | 无状态实现，无需维护会话，直接并发调用即可 |

完整工具清单与更多细节见 [references/tools.md](references/tools.md)。

## 项目结构

```
├── index.html              # 在线版（GitHub Pages 入口，含 59 项真实菜单，打开即用）
├── _template.html          # 页面模板（菜单数据由 scripts/build_site.py 注入生成 index.html）
├── scripts/build_site.py   # 从 references/02-meals-raw.json 抽取真实菜单 → 生成 index.html
├── scripts/mcd_mcp.py      # 零依赖 MCP 客户端 + 拼单优化引擎（仅标准库）
├── demo/index.html         # 早期简化版演示（保留）
├── references/tools.md     # 35 个 MCP 工具清单 + 实测坑
├── references/*-raw.json   # 真实 MCP 原始响应
├── evidence-real.md        # 真实调用证据（时间戳 + traceId）
├── workbuddy.md            # WorkBuddy 开发对话记录
└── CONTEST_DECLARATION.md  # 参赛声明
```

## 配餐算法（一句话）

**预留式贪心 + 升级回炉**：先按价格从高到低、轮换起点给每人发不同款（保证尽量不重样）；
每发一份都给还没轮到的人预留「最便宜一份」的钱，所以**只要预算够就一定配齐 N 份，且绝不超支**；
发完再在剩余预算内把便宜的逐轮换更贵的，把预算用足；最后用余量补饮品、给加购建议。

15 组参数回归（1—20 人 × ¥10—80 × 辣/牛禁忌组合）实测：无超支、无禁忌漏网，预算利用率 84%—100%。

## 声明

本项目为麦当劳中国 1024 程序员节创意开发大赛参赛作品，基于麦当劳中国官方 MCP 能力开发，非麦当劳官方产品。餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准。