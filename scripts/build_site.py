#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 references/02-meals-raw.json 的真实菜单注入页面模板，生成 site/index.html。

用法：python3 scripts/build_site.py
依赖：模板 /tmp/app-template.html（模板已归档为 site/_template.html 时优先用归档）
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "references", "02-meals-raw.json")
TPL = os.path.join(ROOT, "_template.html")
OUT = os.path.join(ROOT, "index.html")

MAIN = {"人气热卖", "鸡肉汉堡/卷", "巨无霸牛鱼肉堡", "安格斯MAX厚牛堡", "炸鸡", "大堡口福单人餐"}
SIDE = {"小食甜品/其他", "小食拼盘/多人餐", "蘸酱炸鸡"}
DRINK = {"饮品", "麦咖啡™"}
# 套餐/周边/蘸酱/多人盘等不适合作为「每人一份」的单品
BAD = ("乐园", "套餐", "件套", "拼盘", "桶", "全家", "随心配", "单品精选", "随心选",
       "周边", "毛绒", "玩具", "礼包", "丝巾", "堡堡随心拼", "四宫格", "小食盘", "双拼十翅")

norm = lambda s: re.sub(r"\s+", "", s or "")


def kind_of(cat: str) -> str:
    c = norm(cat)
    if c in MAIN:
        return "main"
    if c in SIDE:
        return "side"
    if c in DRINK:
        return "drink"
    return "other"


def build_menu() -> list:
    d = json.load(open(RAW, encoding="utf-8"))
    data = d["result"]["structuredContent"]["data"]
    meals, cats = data["meals"], data["categories"]

    code2cat = {}
    for c in cats:
        for m in c.get("meals", []):
            code = m.get("code") if isinstance(m, dict) else m
            if code:
                code2cat[str(code)] = c["name"]

    out = []
    for code, m in meals.items():
        name = norm(m.get("name", ""))
        try:
            price = float(m.get("currentPrice"))
        except (TypeError, ValueError):
            continue
        if not name or price <= 0:
            continue
        if any(x in name for x in BAD) or name.endswith("酱"):
            continue
        k = kind_of(code2cat.get(str(code), ""))
        if k == "other":
            continue
        out.append({
            "n": name,
            "p": round(price, 2),
            "k": k,
            "s": 1 if re.search(r"辣|劲爆|香辣|川味", name) else 0,
            "b": 1 if re.search(r"牛|安格斯|巨无霸", name) else 0,
        })
    out.sort(key=lambda x: (x["k"], -x["p"]))
    return out


def main():
    tpl_path = TPL if os.path.exists(TPL) else "/tmp/app-template.html"
    if not os.path.exists(tpl_path):
        sys.exit(f"找不到模板：{tpl_path}")
    menu = build_menu()
    js = json.dumps(menu, ensure_ascii=False, separators=(",", ":"))
    html = open(tpl_path, encoding="utf-8").read().replace("/*__MENU__*/[]", js)
    if "/*__MENU__*/" in html:
        sys.exit("注入失败：模板里的 /*__MENU__*/[] 占位符没匹配上")
    open(OUT, "w", encoding="utf-8").write(html)
    from collections import Counter
    print(f"✅ {OUT}")
    print(f"   餐品 {len(menu)} 项 {dict(Counter(x['k'] for x in menu))}，页面 {len(html.encode()):,} 字节")


if __name__ == "__main__":
    main()
