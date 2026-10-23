# workbuddy.md · WorkBuddy 开发对话上下文

> 本项目使用腾讯 WorkBuddy 智能体开发。以下为 2026-10-23 开发会话的结构化记录，
> 用于 WorkBuddy 专项奖励核验。对话发生于 WorkBuddy 桌面端（GLM 模型），工作目录
> `/Users/lee/WorkBuddy/2026-09-28-03-15-58/`。

---

## Round 1 — 赛事调研

**Lxb**：给了 WorkBuddy 资料库里保存的一个页面链接，要求"看看这个活动，结合我的情况，授权你去帮我发布作品"。

**WorkBuddy**：
- 读取链接后发现是竞品调研快照（闲鱼搜索页），进一步检索确认真正活动为「麦当劳程序员创意开发大赛」
- 检索官方 GitHub 仓库与规则原文，输出完整规则表：截止 2026-10-25 23:59、按 Star 排名、进榜奖 3000 WorkBuddy 积分
- 分析榜单现状：104 个项目进榜，头部 611★ 全部是"单人省钱"方向
- 给出参赛判断：值得参加，目标 3000 积分档（前 3 名需 600★，2 天内不现实）

## Round 2 — 方向决策

**WorkBuddy**（主动提供差异化分析）：
- 榜单 104 个项目里「多人拼单 + 分摊」方向没有头部作品
- 结合 Lxb 的工程行业背景（工地班组订餐是真实高频场景），提出「麦麦开工餐」：
  输入人数/人均预算/口味禁忌 → 输出不重复组合 + 总支出 + 剩余空间 + 加购建议
- Lxb 采纳

## Round 3 — MCP 真实联调

**Lxb**：提供 MCP Token（open.mcd.cn/mcp 激活）。

**WorkBuddy**（逐项实测并留痕）：
1. `initialize` 握手 ✅ → serverInfo: mcd-mcp 1.0.0，确认无状态实现
2. `tools/list` ✅ → 35 个工具
3. `now-time-info` ✅ → 真实服务器时间
4. `query-nearby-stores` ❌→✅ → **发现官方文档未写的坑：city 与 keyword 必须同时传**，只传其一报 600058
5. `query-meals` ✅ → 15 分类、127 个有效餐品编码；发现商品分散在 `data.meals` 与 `data.categories[].meals` 两处且混有字符串占位项
6. `query-meal-detail` ✅ → 发现服务端在响应内嵌「输出格式要求」约束 LLM 行为

以上全部记录进 `evidence-real.md`（含 traceId）与 `references/tools.md`。

## Round 4 — 编码

**WorkBuddy** 编写 `scripts/mcd_mcp.py`（零依赖，仅 Python 标准库）：
- `McdMcp` 类：Streamable HTTP JSON-RPC 客户端，兼容纯 JSON 与 SSE 两种响应
- `extract_json()`：两级回退的响应解析（先 ```json 块，再按 "data" 键定位）
- `plan_combo()`：多样性拼单引擎——禁忌过滤 → 按价值排序 → 每人不重复轮转 → 剩余空间加购建议

**Lxb** 复测时发现首版缺陷：4 人全点巨无霸（贪心选最贵导致零多样性）。
**WorkBuddy** 修复为多样性轮转策略，并修复禁忌文案的运算符优先级 bug。

## Round 5 — 文档与合规

**WorkBuddy** 编写全部参赛材料：README、CONTEST_DECLARATION（原创/合规/敏感信息三段声明）、
MCP_INTEGRATION、mcp-config.example.json（仅环境变量占位符）、references/tools.md、demo/index.html。

合规要点（WorkBuddy 主动提示并执行）：
- 仓库不落 Token（配置仅 `${MCD_MCP_TOKEN}` 占位）
- 证据文件脱敏：不含个人地址、积分、券、历史订单
- 演示页零网络请求
- 遵守官方"不将麦当劳品牌与其他品牌对比"条款，与竞品对比仅限赛事内部数据

## 遗留事项

- GitHub 仓库创建与报名 Issue：待 Lxb 完成 GitHub 登录后由 WorkBuddy 执行
- Lxb 的 GitHub 账号未设密码（Google OAuth 注册），密码登录被平台拒绝，已改走 Token 方案