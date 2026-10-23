#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦麦开工餐 · 零依赖麦当劳 MCP 客户端 + 多人拼单优化引擎

参赛项目：麦当劳中国 1024 程序员节创意开发大赛
官方赛事仓库：M-China/mcd-developer-innovation-challenge
MCP 文档：M-China/mcd-mcp-server

零依赖：仅用 Python 3 标准库（urllib / json / argparse）。

用法：
  export MCD_MCP_TOKEN=你的Token
  python3 mcd_mcp.py stores  --city 成都 --keyword 麦当劳     # 搜门店
  python3 mcd_mcp.py meals   --store 3450336                  # 拉菜单
  python3 mcd_mcp.py plan    --people 4 --budget 30 --scene 1 # 拼单优化（真实 MCP）
  python3 mcd_mcp.py demo    --people 4 --budget 30           # 离线演示（不连网、不耗 Token）

真实调用踩坑（官方文档未写，实测得出）：
  1. query-nearby-stores 的 city 与 keyword 必须【同时】传，只传其一报 600058「城市名或者关键词不能为空」
  2. MCP 响应的 content[0].text 是「说明文字 + ```json 代码块」混合体，解析 JSON 时要定位代码块，
     且 data 可能在顶层 {"data": {...}} 里，menu items 分散在 data.meals 和 data.categories[].meals 两处
  3. 菜单 items 顶层只有 code + tags，名称要靠 query-meal-detail 逐个取
  4. 该 MCP 为无状态实现：响应头没有 mcp-session-id，无需维护会话
"""
import argparse
import json
import os
import sys
import urllib.request

MCP_URL = "https://mcp.mcd.cn"


# ---------------------------------------------------------------- MCP 客户端
class McdMcp:
    """Streamable HTTP MCP 客户端（零依赖）。

    用法:
        mcp = McdMcp(token)
        mcp.initialize()
        tools = mcp.list_tools()
        result = mcp.call("query-nearby-stores", {"beType": 1, "searchType": 2,
                                                  "city": "成都", "keyword": "麦当劳"})
    """

    def __init__(self, token: str, url: str = MCP_URL):
        self.token = token
        self.url = url
        self._id = 0

    def _rpc(self, method: str, params: dict | None = None, timeout: int = 30):
        self._id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self._id,
                              "method": method, "params": params or {}}).encode()
        req = urllib.request.Request(
            self.url, data=payload, method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {self.token}",
            })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
        # 兼容纯 JSON 与 SSE 两种响应
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            msg = None
            for line in raw.splitlines():
                if line.startswith("data:"):
                    msg = json.loads(line[5:])
                    break
        if not msg:
            raise RuntimeError(f"MCP 响应无法解析: {raw[:200]}")
        if "error" in msg:
            raise RuntimeError(f"MCP 错误: {msg['error']}")
        return msg["result"]

    def initialize(self):
        return self._rpc("initialize", {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "mcd-kaiGongCan", "version": "1.0.0"}})

    def list_tools(self):
        return self._rpc("tools/list", {}).get("tools", [])

    def call(self, name: str, arguments: dict):
        r = self._rpc("tools/call", {"name": name, "arguments": arguments})
        text = "".join(c.get("text", "") for c in r.get("content", []))
        return extract_json(text)


def extract_json(text: str):
    """从 MCP 的 text 响应里取出 JSON（见模块 docstring 踩坑 2）。

    服务端返回的是「字段说明 + ```json 代码块」，且代码块不一定规范。
    优先取 ```json 块；否则取第一个 "data" 键所在的最外层大括号。
    """
    i = text.find("```json")
    if i >= 0:
        j = text.find("```", i + 7)
        if j > i:
            try:
                return json.loads(text[i + 7:j])
            except json.JSONDecodeError:
                pass
    i = text.find('"data"')
    if i >= 0:
        start = text.rfind("{", 0, i)
        try:
            return json.loads(text[start:text.rfind("}") + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError("响应中未找到 JSON 数据块")


def flatten_meals(data: dict):
    """菜单餐品分散在 data.meals 和 data.categories[].meals 两处（踩坑 2）。"""
    out = list(data.get("meals") or [])
    for cat in data.get("categories") or []:
        out.extend(cat.get("meals") or [])
    return [m for m in out if isinstance(m, dict)]


# ---------------------------------------------------------------- 拼单优化引擎
def plan_combo(meals: list, people: int, budget_pp: float,
               no_spicy: bool = False, no_beef: bool = False):
    """多人拼单优化：每人一份、人均预算内、总支出最优。

    策略（贪心，够用且可解释）：
      1. 过滤禁忌（名称含「辣/麻辣」且 no_spicy；含「牛」且 no_beef）
      2. 每人在预算内选单价最高（价值感最好）的单品
      3. 剩余预算池给全员加购小食/饮品
    返回 dict：每人选择、总金额、人均、加购建议。
    """
    banned = []
    if no_spicy:
        banned += ["辣", "麻辣", "藤椒"]
    if no_beef:
        banned += ["牛", "牛肉"]

    def ok(name):
        return name and not any(b in name for b in banned)

    # 价格字段在不同响应里可能是 price / sellingPrice / finalPrice
    def price_of(m):
        for k in ("price", "sellingPrice", "finalPrice", "amount"):
            v = m.get(k)
            if isinstance(v, (int, float)):
                return float(v)
        # 嵌套兜底
        for k, v in m.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    if "rice" in k2.lower() and isinstance(v2, (int, float)):
                        return float(v2)
        return None

    def name_of(m):
        for k in ("name", "mealName", "productName", "title"):
            if m.get(k):
                return m[k]
        # 嵌套兜底
        for v in m.values():
            if isinstance(v, dict) and v.get("name"):
                return v["name"]
        return None

    pool = []
    for m in meals:
        nm = name_of(m)
        pr = price_of(m)
        if ok(nm) and pr and 3 <= pr <= budget_pp:
            pool.append({"name": nm, "price": round(pr, 2), "code": m.get("code")})
    if not pool:
        return {"error": "预算内没有可选餐品，试试提高人均预算",
                "预算": budget_pp, "候选数": len(meals)}
    pool.sort(key=lambda x: -x["price"])

    # 多样性优先：每人拿一个不同的（价值从高到低轮转），不够人时才允许重复
    unique = []
    seen = set()
    for item in pool:
        key = item["name"]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    picks, used = [], 0.0
    round_robin = unique + pool  # 先保证多样性，用尽后按价格补
    idx = 0
    for _ in range(people):
        placed = False
        while idx < len(round_robin):
            cand = round_robin[idx]
            idx += 1
            if used + cand["price"] <= budget_pp * people + 1e-9:
                picks.append(cand)
                used += cand["price"]
                placed = True
                break
        if not placed:
            break
    remain = budget_pp * people - used
    add_on = [p for p in pool if p["price"] <= remain] if remain > 5 else []
    taboo = []
    if no_spicy:
        taboo.append("辣类")
    if no_beef:
        taboo.append("牛类")
    return {
        "人数": people, "人均预算": budget_pp, "总预算": round(budget_pp * people, 2),
        "每人一份": picks[:people],
        "预计总支出": round(used, 2),
        "剩余空间": round(remain, 2),
        "加购建议": add_on[:3] if add_on else "预算已用满，无需加购",
        "禁忌已过滤": "、".join(taboo) if taboo else "无",
    }


# ---------------------------------------------------------------- CLI
SAMPLE = [  # 离线演示数据（2026-10-23 成都成华区真实门店菜单节选，code 为真实编码）
    {"code": "521956", "name": "巨无霸", "price": 25.0},
    {"code": "521952", "name": "麦辣鸡腿堡", "price": 23.5},
    {"code": "9900016076", "name": "板烧鸡腿堡", "price": 24.0},
    {"code": "9900016073", "name": "双层吉士汉堡", "price": 17.5},
    {"code": "9900016077", "name": "麦香鱼", "price": 15.0},
    {"code": "9900016566", "name": "麦乐鸡(5块)", "price": 12.5},
    {"code": "9900016311", "name": "中薯条", "price": 13.0},
    {"code": "100037", "name": "可口可乐(中)", "price": 9.5},
]


def main():
    ap = argparse.ArgumentParser(description="麦麦开工餐 · 麦当劳多人拼单优化")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stores", help="搜门店（city+keyword 必须同时传，见踩坑1）")
    s.add_argument("--city", required=True)
    s.add_argument("--keyword", default="麦当劳")

    s = sub.add_parser("meals", help="拉菜单")
    s.add_argument("--store", required=True)

    s = sub.add_parser("plan", help="真实 MCP 拼单优化")
    s.add_argument("--store", required=True)
    s.add_argument("--people", type=int, default=4)
    s.add_argument("--budget", type=float, default=30)
    s.add_argument("--no-spicy", action="store_true")
    s.add_argument("--no-beef", action="store_true")

    s = sub.add_parser("demo", help="离线演示（不连网）")
    s.add_argument("--people", type=int, default=4)
    s.add_argument("--budget", type=float, default=30)
    s.add_argument("--no-spicy", action="store_true")
    s.add_argument("--no-beef", action="store_true")

    a = ap.parse_args()
    token = os.environ.get("MCD_MCP_TOKEN")
    if a.cmd != "demo" and not token:
        sys.exit("[错误] 未设置 MCD_MCP_TOKEN 环境变量")

    if a.cmd == "stores":
        mcp = McdMcp(token)
        data = mcp.call("query-nearby-stores",
                        {"beType": 1, "searchType": 2,
                         "city": a.city, "keyword": a.keyword})
        for st in (data.get("data") or [])[:8]:
            print(f"{st.get('storeCode')}  {st.get('storeName')}  {st.get('address', '')[:20]}")
    elif a.cmd == "meals":
        mcp = McdMcp(token)
        data = mcp.call("query-meals",
                        {"storeCode": a.store, "orderType": 1, "beType": 1})
        meals = flatten_meals(data.get("data") or data)
        print(f"餐品 {len(meals)} 个（code 列表，名称需 query-meal-detail）")
        for m in meals[:20]:
            print(" ", m.get("code"), m.get("tags") or "")
    elif a.cmd in ("plan", "demo"):
        if a.cmd == "demo":
            result = plan_combo(SAMPLE, a.people, a.budget, no_spicy=a.no_spicy, no_beef=getattr(a,"no_beef",False))
            print("【离线演示模式】数据为 2026-10-23 成都真实菜单节选\n")
        else:
            mcp = McdMcp(token)
            data = mcp.call("query-meals",
                            {"storeCode": a.store, "orderType": 1, "beType": 1})
            result = plan_combo(flatten_meals(data.get("data") or data),
                                a.people, a.budget, no_spicy=a.no_spicy)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()