#!/usr/bin/env python3
"""Rebuild GMGN intel timeline.json + index.html from baselines (+ updates/)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
STORE_ROOT = SITE_DIR.parent
MIRROR_DIR = Path("/workspace/gmgn-intel")

TZ_SHANGHAI = timezone(timedelta(hours=8))

FEATURES_PATH = STORE_ROOT / "gmgn-features-baseline.json"
CAREERS_PATH = STORE_ROOT / "gmgn-careers-baseline.json"
TUTORIALS_PATH = STORE_ROOT / "gmgn-tutorials-baseline.json"
UPDATES_DIR = SITE_DIR / "updates"

# Manual Chinese titles/summaries for known product updates (keyed by source URL or date+en title)
FEATURE_ZH = {
    "https://x.com/gmgnai/status/2111281543029178881": (
        "Skills 喊单评分：币是否真跑 + 自喊后砸盘惩罚",
        "GMGN Skills 用喊单人真实成交账本打双维分：喊的币是否真涨，以及是否在自己喊单后 15 分钟内卖出砸盘（砸盘则分数暴跌）。"
        "【功能推断】已打通喊单记录↔成交账本；产品在做 Callout/跟单风控与反割韭菜评分，超越单纯命中率。",
    ),
    "https://x.com/gmgnai/status/2110695428085960771": (
        "Skills 钱包分析可追溯利润来源",
        "GMGN Skills 钱包分析升级：可追溯利润来源，并提示自发射代币中超过 50% 会失败。帮助判断聪明钱收益质量。",
    ),
    "https://x.com/gmgnai/status/2108761437174976891": (
        "上线 gmgn-narrative Skill",
        "新增 gmgn-narrative：对照链上数据核验叙事说法是否站得住，减少被故事带节奏。",
    ),
    "https://x.com/gmgnai/status/2108564198225859055": (
        "GGC 全球赛季 1 公布",
        "GMGN Global Championship（GGC）Season 1 公布，赛期约 10/17–10/27 UTC。属赛事活动，非功能发布。",
    ),
    "https://x.com/gmgnai/status/2108131696701059138": (
        "Giga AI 升级",
        "站内 Giga AI 助手升级：更快回答代币、钱包与开发者战绩相关问题。",
    ),
    "https://x.com/gmgnai/status/2104600455657738648": (
        "上线 gmgn-contract-dd",
        "合约尽职调查 Skill：安全扣分过程更透明；未读字段一律不通过，避免漏检。",
    ),
    "https://x.com/gmgnai/status/2102734098473316533": (
        "Callout 同时显示喊单与持仓/实时 PnL",
        "Callout 更新：同时展示喊单人、持仓方、实时盈亏与历史喊单，方便对照跟单风险。",
    ),
    "https://x.com/gmgnai/status/2100785131254632646": (
        "上线 token-buy Skill",
        "token-buy Skill：解析 ticker、做安全检查并给出下单规模建议，需用户确认后执行。",
    ),
    "https://x.com/gmgnapp001/status/2100563862613537097": (
        "GMGN GO 移动社交交易上线",
        "GMGN GO 上线：移动端可关注交易者、看 Callout 与排行榜，强化社交交易体验。",
    ),
    "https://x.com/gmgnai/status/2100197212399845701": (
        "Arc 链首日上线 GMGN",
        "Arc 公链从上线首日即可在 GMGN 交易与发现。",
    ),
    "https://x.com/gmgnai/status/2100174341401170271": (
        "K 线 FOMO 喊单标记",
        "图表新增 Fomo Thesis / Fomo Top 标记，可直接在 K 线上看到 FOMO 喊单点。",
    ),
    "https://x.com/gmgnai/status/2099396799186473200": (
        "RWA / Meme 报价过滤（全链）",
        "全链支持按 RWA 与 Meme 报价类型过滤，方便筛掉不想要的报价资产。",
    ),
    "https://x.com/gmgnai/status/2098234606306861246": (
        "Heat Rank 跨链热度榜 Skill",
        "Heat Rank Skill：跨链精选热门列表，用 Skills 聚合多链热度。",
    ),
    "https://x.com/gmgnai/status/2097933008154275844": (
        "报价代币安全与流动性检查",
        "新增对 Quote 代币的安全与流动性检查，降低配对侧风险。",
    ),
    "https://x.com/gmgnai/status/2096991802230464860": (
        "多链 Trenches 合并信息流",
        "Trenches 支持 SOL/BSC/Robinhood/Base/Arc 等多链合并信息流，一屏看新盘。",
    ),
    "https://x.com/gmgnai/status/2096986626006389047": (
        "双 Dev 评分：声誉 + 实力",
        "开发者评分拆成钱包声誉与代币实力两维，便于区分人设与项目质量。",
    ),
    "https://x.com/gmgnai/status/2094799783013863557": (
        "Skills Market 上线 Chart Pattern",
        "Skills 市场新增图表形态识别 Skill，可辅助看盘。",
    ),
    "https://x.com/gmgnai/status/2093130053328764943": (
        "OpenAPI Free / Plus / Pro 套餐",
        "OpenAPI 推出 Free / Plus / Pro 限速套餐，方便按用量接入 Agent/数据。",
    ),
    "https://x.com/gmgnai/status/2090799546989494481": (
        "GMGN Card：闲置余额 5% APY",
        "GMGN Card 上线：闲置余额可享约 5% APY，并支持 Apple/Google Pay 相关场景。",
    ),
    "https://x.com/gmgnai/status/2089944717161275506": (
        "Trenches 内联迷你图",
        "Trenches 列表内嵌迷你 K 线，扫盘时可直接看走势。",
    ),
    "https://x.com/gmgnai/status/2089769132619391390": (
        "Arbitrum 上线 GMGN",
        "Arbitrum 链已可在 GMGN 使用。",
    ),
    "https://x.com/gmgnai/status/2089698059928400118": (
        "关注可信 Dev，Trenches 高亮",
        "可关注可信开发者，并在 Trenches 用自定义颜色/名称高亮其新盘。",
    ),
    "https://x.com/gmgnai/status/2085733804489220402": (
        "钱包追踪：FOMO 转入转出",
        "Wallet Tracker 支持 FOMO 钱包转入/转出跟踪，便于盯资金动向。",
    ),
    "https://x.com/gmgnai/status/2085351308715008186": (
        "Manifesto 付费高信念喊单",
        "Manifesto：付费高信念喊单产品形态上线。",
    ),
    "https://x.com/gmgnai/status/2085019822023397729": (
        "Trenches 简洁布局模式",
        "Trenches 新增 Clean Layout，减少噪音、更易扫盘。",
    ),
    "https://github.com/GMGNAI/gmgn-skills/discussions": (
        "gmgn-cli v1.5.3 支持 Robinhood",
        "gmgn-cli v1.5.3：Cooking / KOL / Smart Money / Market Signal 等能力覆盖 Robinhood。",
    ),
    "https://iq.wiki/wiki/gmgn/milestones": (
        "Robinhood 链完整接入",
        "里程碑：Robinhood Chain 完整集成（发射台、智能买入保护、API）。第三方 wiki，通知时请再核 X/Blog。",
    ),
    "https://gmgn.ai/blog/gmgn-cooking/": (
        "产品文：GMGN Cooking 说明",
        "Blog 产品向文章：解释 GMGN Cooking 如何把想法接到代币发射流程。",
    ),
    "https://gmgn.ai/blog/gmgn-skills-for-ai-agents/": (
        "产品文：GMGN Skills for AI Agents",
        "Blog 产品向文章：如何把 Claude 等 AI Agent 接到链上数据、钱包分析与交易。",
    ),
}

TUTORIAL_ZH = {
    "How to Buy Memecoins on Arc: Arc vs Robinhood Chain": (
        "教程：如何在 Arc 买 Memecoin（对比 Robinhood）",
        "介绍如何在 Arc 链购买 Memecoin，并对比 Arc 与 Robinhood Chain 的差异。",
    ),
    "How to Read FOMO Calls on the GMGN Chart — and What to Check After One Shows Up": (
        "教程：怎么在 K 线上看 FOMO 喊单",
        "讲解 GMGN 图表上的 FOMO 喊单标记，以及出现后该检查哪些安全/持仓信号。",
    ),
    "How to Read FOMO Calls on the GMGN Chart": (
        "教程：怎么在 K 线上看 FOMO 喊单",
        "讲解 GMGN 图表上的 FOMO 喊单标记，以及出现后该检查哪些安全/持仓信号。",
    ),
    "Pons vs StonkFun vs Flap: Meme Launchpads on Robinhood Chain, Solana and BSC": (
        "教程：Pons / StonkFun / Flap 发射台对比",
        "对比 Robinhood、Solana、BSC 上常见 Meme 发射台差异，帮你选入口。",
    ),
    "What Is $MEME (A Meme Coin)? Is It the Same Token as AMC Stock Token?": (
        "教程：$MEME 与 AMC 股票代币是否同一资产",
        "澄清 $MEME（Meme 币）与 AMC 股票代币是否为同一资产，避免买错。",
    ),
    "How to Buy New Robinhood Chain Launches on GMGN": (
        "教程：在 GMGN 买 Robinhood 新盘",
        "手把手：如何在 GMGN 上发现并买入 Robinhood Chain 新发射代币。",
    ),
    "BONER Is Trending on Robinhood Chain. How Do You Know Which One You're Buying?": (
        "教程：同名热盘怎么辨别买的是哪一个",
        "以 Robinhood 上热门同名盘为例，教你核对合约与标识，避免买错。",
    ),
    "What Is Artificial Inu (AI)? The NVDA-Paired Memecoin on Robinhood Chain": (
        "教程：什么是 Artificial Inu（AI）",
        "介绍 Robinhood 上与 NVDA 配对的 Memecoin Artificial Inu（AI）背景与注意点。",
    ),
    "What to Check on GMGN After You Find a Trending Memecoin": (
        "教程：发现热门 Meme 后在 GMGN 查什么",
        "热盘出现后，应在 GMGN 上依次检查安全、持仓、聪明钱与流动性等要点。",
    ),
    "How to Find Meme Coins Earlier: Using Trenches, Callouts, and Wallet Tracking": (
        "教程：用 Trenches / Callout / 钱包追踪更早发现 Meme",
        "组合 Trenches、Callout 与钱包追踪，提高发现早期 Meme 的效率。",
    ),
    "How to Find Meme Coins Earlier": (
        "教程：用 Trenches / Callout / 钱包追踪更早发现 Meme",
        "组合 Trenches、Callout 与钱包追踪，提高发现早期 Meme 的效率。",
    ),
    "What Is a Meme Coin Bundle? How to Check Bundle % and Linked Wallets on GMGN": (
        "教程：什么是 Bundle，如何查捆绑比例",
        "解释 Bundle（捆绑仓）概念，并演示在 GMGN 查看 Bundle % 与关联钱包。",
    ),
    "How to Check BSC Meme Coin Token Taxes on GMGN": (
        "教程：在 GMGN 查 BSC Meme 代币税",
        "教你如何在 GMGN 检查 BSC Meme 的买卖税/税率风险。",
    ),
    "Trading Meme Coins on BSC vs. Solana: What's Different?": (
        "教程：BSC 与 Solana 玩 Meme 有何不同",
        "对比 BSC 与 Solana 在 Meme 交易体验、费用与风险上的差异。",
    ),
    "How Can Beginners Trade Meme Coins Safely?": (
        "教程：新手如何更安全地交易 Meme",
        "面向新手的安全交易指南：钱包、滑点、蜜罐与仓位管理基础。",
    ),
    "How to Choose a Chain for Meme Coin Trading": (
        "教程：怎么选 Meme 交易链",
        "从流动性、费用、工具与风险角度，帮你选择适合的 Meme 交易链。",
    ),
    "How to Set Take-Profit, Stop-Loss, Trailing Stop, and Trailing Take-Profit on GMGN": (
        "教程：在 GMGN 设置止盈止损与追踪单",
        "详解 TP/SL、追踪止盈、追踪止损在 GMGN 上的设置方法。",
    ),
    "How to Set TP/SL/Trailing on GMGN": (
        "教程：在 GMGN 设置止盈止损与追踪单",
        "详解 TP/SL、追踪止盈、追踪止损在 GMGN 上的设置方法。",
    ),
    "How to Spot the Early Signs of Meme Rotation on Robinhood Chain with GMGN": (
        "教程：用 GMGN 发现 Robinhood 轮动早期信号",
        "讲解如何在 Robinhood 链上用 GMGN 观察叙事/资金轮动的早期迹象。",
    ),
    "How to Buy CASHCAT on Robinhood Chain: A Complete GMGN Guide": (
        "教程：在 Robinhood 用 GMGN 买 CASHCAT",
        "完整指南：通过 GMGN 在 Robinhood Chain 购买 CASHCAT。",
    ),
    "How to Track Smart Money with Claude and Other AI Agents (GMGN Skills Guide, 2026)": (
        "教程：用 Claude + GMGN Skills 跟踪聪明钱",
        "Skills 教程：把 Claude 等 AI Agent 接到 GMGN，跟踪聪明钱钱包。",
    ),
    "After CASHCAT: How to Discover, Analyze, and Trade Robinhood Chain Meme Coins with GMGN": (
        "教程：CASHCAT 之后如何用 GMGN 做 Robinhood Meme",
        "从发现、分析到交易，系统介绍用 GMGN 玩 Robinhood Chain Meme。",
    ),
    "What is Cross-Chain Meme Narrative Rotation? How to Track Multi-Chain Signals with GMGN": (
        "教程：跨链 Meme 叙事轮动怎么跟踪",
        "解释跨链叙事轮动，并说明如何用 GMGN 跟踪多链信号。",
    ),
    "How to Check If a Solana Token Is Safe with Claude and GMGN Skills": (
        "教程：用 Claude + Skills 检查 Solana 代币安全",
        "Skills 教程：结合 Claude 与 GMGN Skills 做 Solana 代币安全检查。",
    ),
    "What Is Memecoin Cooking? How GMGN Cooking Connects Ideas to Token Launches": (
        "教程/产品：什么是 Memecoin Cooking",
        "说明 Cooking 如何把创意接到发射流程（非独立发射台，而是工作流）。",
    ),
    "What Is Memecoin Cooking?": (
        "教程/产品：什么是 Memecoin Cooking",
        "说明 Cooking 如何把创意接到发射流程（非独立发射台，而是工作流）。",
    ),
    "Connect AI Agents Like Claude & Cursor to On-Chain Data, Wallet Analysis & Trading — GMGN Skills": (
        "教程/产品：GMGN Skills 对接 AI Agent",
        "介绍如何把 Claude、Cursor 等 Agent 接到链上数据、钱包分析与交易。",
    ),
    "GMGN Skills for AI Agents": (
        "教程/产品：GMGN Skills 对接 AI Agent",
        "介绍如何把 Claude、Cursor 等 Agent 接到链上数据、钱包分析与交易。",
    ),
    "How Do You Know If a Meme Coin Is Safe? A Guide to Spotting Honeypots and Rug Pulls": (
        "教程：如何判断 Meme 是否安全（蜜罐/Rug）",
        "蜜罐与 Rug 识别指南，配合 GMGN 安全检查字段一起用。",
    ),
    "How to Track and Copy Solana Smart Money Wallets (2026 Guide)": (
        "教程：跟踪并跟单 Solana 聪明钱（2026）",
        "2026 指南：在 Solana 上跟踪聪明钱钱包并做跟单。",
    ),
    "GMGN vs Axiom: Which Is Better for Beginners in 2026?": (
        "教程：GMGN vs Axiom，新手怎么选",
        "从新手视角对比 GMGN 与 Axiom 的功能与上手难度。",
    ),
    "Best Meme Coin Trading Platforms in 2026: GMGN vs Photon, BonkBot, Axiom & Trojan": (
        "教程：2026 Meme 交易平台对比",
        "横向对比 GMGN、Photon、BonkBot、Axiom、Trojan 等平台。",
    ),
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def stable_id(*parts: str) -> str:
    raw = "|".join(p.strip().lower() for p in parts if p)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def source_label_for(url: str) -> str:
    u = (url or "").lower()
    if "x.com/" in u or "twitter.com/" in u:
        return "X"
    if "/careers" in u or "/pm-" in u or "engineer" in u or "hr@" in u:
        return "Careers"
    if "blog" in u:
        return "Blog"
    if "docs.gmgn" in u:
        return "Docs"
    if "github.com" in u:
        return "GitHub"
    if "memecoin.gmgn" in u:
        return "Tutorials"
    if "iq.wiki" in u:
        return "Wiki"
    return "Web"


def to_datetime(date_str: str, collected: str | None = None) -> str:
    """Return ISO8601 with +08:00 when only a date is known (noon Shanghai)."""
    if not date_str:
        return collected or datetime.now(TZ_SHANGHAI).isoformat(timespec="seconds")
    if "T" in date_str:
        return date_str
    return f"{date_str}T12:00:00+08:00"


def make_item(
    *,
    date: str,
    category: str,
    title: str,
    summary: str,
    source_url: str,
    source_label: str | None = None,
    collected_at: str,
    datetime_str: str | None = None,
    id_hint: str | None = None,
) -> dict:
    url = source_url or ""
    iid = id_hint or stable_id(category, date, url or title)
    return {
        "id": iid,
        "date": date[:10] if date else "",
        "datetime": datetime_str or to_datetime(date, collected_at),
        "category": category,
        "title": title,
        "summary": summary,
        "source_url": url,
        "source_label": source_label or source_label_for(url),
        "collected_at": collected_at,
    }


def from_features(data: dict, collected: str) -> list[dict]:
    items = []
    for u in data.get("recent_updates") or []:
        url = u.get("source") or ""
        en_title = u.get("title") or ""
        date = u.get("date") or ""
        zh = FEATURE_ZH.get(url)
        if zh:
            title, summary = zh
        else:
            title = en_title
            summary = f"产品更新：{en_title}"
            if u.get("note"):
                summary += f"（备注：{u['note']}）"
        # Map product_blog / event / chain / feature / api all under 功能 for the site
        # (events still listed as product intel; category stays 功能 as requested)
        items.append(
            make_item(
                date=date,
                category="功能",
                title=title,
                summary=summary,
                source_url=url,
                collected_at=collected,
            )
        )
    return items


def from_careers(data: dict, collected: str) -> list[dict]:
    items = []
    for r in data.get("open_roles") or []:
        date = r.get("posted") or ""
        title = r.get("title_zh") or r.get("title_en") or "招聘岗位"
        url = r.get("url_zh") or r.get("url_en") or ""
        loc = r.get("location") or ""
        summ_en = r.get("summary") or ""
        summary = f"在招：{title}。地点/形式：{loc}。投递 hr@gmgn.ai。"
        if summ_en:
            summary += f" 要点：{summ_en}"
        items.append(
            make_item(
                date=date,
                category="招聘",
                title=f"招聘：{title}",
                summary=summary,
                source_url=url,
                source_label="Careers",
                collected_at=collected,
            )
        )
    for r in data.get("x_only_or_unlisted") or []:
        date = r.get("posted") or ""
        title = r.get("title") or "招聘岗位"
        url = r.get("source") or ""
        loc = r.get("location") or ""
        hint = r.get("apply_hint") or ""
        status = r.get("status") or ""
        summary = f"X 公布岗位（招聘站暂未收录）：{title}。{loc}。"
        if hint:
            summary += f" {hint}"
        if status:
            summary += f"（状态：{status}）"
        items.append(
            make_item(
                date=date,
                category="招聘",
                title=f"招聘：{title}",
                summary=summary,
                source_url=url,
                source_label="X",
                collected_at=collected,
            )
        )
    return items


def tutorial_zh(en_title: str) -> tuple[str, str]:
    if en_title in TUTORIAL_ZH:
        return TUTORIAL_ZH[en_title]
    # fuzzy prefix match
    for k, v in TUTORIAL_ZH.items():
        if en_title.startswith(k) or k.startswith(en_title[:40]):
            return v
    return (f"教程：{en_title}", f"GMGN 相关教程/指南：{en_title}")


def from_tutorials(data: dict, collected: str) -> list[dict]:
    items = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    # Prefer verified highlight URLs first
    for h in data.get("verified_highlight_urls") or []:
        url = h.get("url") or ""
        date = h.get("date") or ""
        en = h.get("title") or h.get("title_zh") or ""
        if h.get("title_zh") and not h.get("title"):
            title = h["title_zh"] if h["title_zh"].startswith("教程") else f"教程：{h['title_zh']}"
            summary = f"中文教程：{h['title_zh']}。"
        else:
            title, summary = tutorial_zh(en)
        key_t = title.lower()
        if url in seen_urls or key_t in seen_titles:
            continue
        if url:
            seen_urls.add(url)
        seen_titles.add(key_t)
        items.append(
            make_item(
                date=date,
                category="教程",
                title=title,
                summary=summary,
                source_url=url or "https://gmgn.ai/blog/",
                source_label="Blog",
                collected_at=collected,
            )
        )

    for t in data.get("notable_recent_blog_tutorials") or []:
        url = t.get("url") or ""
        date = t.get("date") or ""
        en = t.get("title") or ""
        title, summary = tutorial_zh(en)
        # Skip generic blog index-only duplicates when we already have a better URL
        key_t = title.lower()
        if key_t in seen_titles:
            continue
        if url and url.rstrip("/") == "https://gmgn.ai/blog" and any(
            title == tutorial_zh(x.get("title", ""))[0]
            for x in (data.get("verified_highlight_urls") or [])
        ):
            continue
        if url in seen_urls and url.rstrip("/") != "https://gmgn.ai/blog":
            continue
        if url and url.rstrip("/") != "https://gmgn.ai/blog":
            seen_urls.add(url)
        seen_titles.add(key_t)
        # Prefer verified URL from map if blog index placeholder
        if not url or url.rstrip("/") == "https://gmgn.ai/blog":
            # try find verified match by title
            for h in data.get("verified_highlight_urls") or []:
                ht = h.get("title") or ""
                if ht and (ht in en or en.startswith(ht)):
                    url = h.get("url") or url
                    break
            if not url or url.rstrip("/") == "https://gmgn.ai/blog":
                url = "https://gmgn.ai/blog/"
        items.append(
            make_item(
                date=date,
                category="教程",
                title=title,
                summary=summary
                + ("" if t.get("url_verified") else "（链接以 Blog 首页为准，具体 slug 可能变动）"),
                source_url=url,
                source_label="Blog",
                collected_at=collected,
            )
        )
    return items


def load_updates_dir() -> list[dict]:
    items = []
    if not UPDATES_DIR.is_dir():
        return items
    for p in sorted(UPDATES_DIR.glob("*.json")):
        try:
            data = load_json(p)
        except Exception:
            continue
        if isinstance(data, list):
            items.extend(data)
        elif isinstance(data, dict) and "items" in data:
            items.extend(data["items"])
        elif isinstance(data, dict) and "id" in data:
            items.append(data)
    return items


def dedupe(items: list[dict]) -> list[dict]:
    by_url: dict[str, dict] = {}
    by_title_date: dict[str, dict] = {}
    result: list[dict] = []

    def score(it: dict) -> int:
        url = it.get("source_url") or ""
        s = 0
        if url and url.rstrip("/") != "https://gmgn.ai/blog":
            s += 2
        if it.get("summary"):
            s += 1
        return s

    for it in items:
        url = (it.get("source_url") or "").rstrip("/")
        title_key = f"{it.get('category')}|{it.get('date')}|{(it.get('title') or '').lower()}"
        # URL dedupe (ignore generic blog index)
        if url and url != "https://gmgn.ai/blog":
            prev = by_url.get(url)
            if prev:
                if score(it) > score(prev):
                    # replace in result
                    idx = result.index(prev)
                    result[idx] = it
                    by_url[url] = it
                    by_title_date[title_key] = it
                continue
            by_url[url] = it
        prev_td = by_title_date.get(title_key)
        if prev_td:
            if score(it) > score(prev_td):
                idx = result.index(prev_td)
                result[idx] = it
                by_title_date[title_key] = it
                if url and url != "https://gmgn.ai/blog":
                    by_url[url] = it
            continue
        by_title_date[title_key] = it
        result.append(it)
    return result


def sort_items(items: list[dict]) -> list[dict]:
    def key(it: dict):
        dt = it.get("datetime") or it.get("date") or ""
        return dt

    return sorted(items, key=key, reverse=True)


def build_timeline() -> tuple[list[dict], str]:
    features = load_json(FEATURES_PATH)
    careers = load_json(CAREERS_PATH)
    tutorials = load_json(TUTORIALS_PATH)

    collected = (
        features.get("last_checked")
        or careers.get("last_checked")
        or datetime.now(TZ_SHANGHAI).isoformat(timespec="seconds")
    )

    items: list[dict] = []
    items.extend(from_features(features, collected))
    items.extend(from_careers(careers, collected))
    items.extend(from_tutorials(tutorials, collected))
    items.extend(load_updates_dir())

    # normalize category labels
    for it in items:
        cat = it.get("category") or ""
        if cat in ("feature", "product", "chain", "api", "event", "product_blog", "功能"):
            it["category"] = "功能"
        elif cat in ("career", "careers", "hiring", "招聘"):
            it["category"] = "招聘"
        elif cat in ("tutorial", "tutorials", "guide", "教程"):
            it["category"] = "教程"
        if not it.get("id"):
            it["id"] = stable_id(it.get("category", ""), it.get("date", ""), it.get("source_url") or it.get("title", ""))
        if not it.get("datetime"):
            it["datetime"] = to_datetime(it.get("date", ""), collected)
        if not it.get("collected_at"):
            it["collected_at"] = collected
        if not it.get("source_label"):
            it["source_label"] = source_label_for(it.get("source_url", ""))

    items = dedupe(items)
    items = sort_items(items)
    generated_at = datetime.now(TZ_SHANGHAI).isoformat(timespec="seconds")
    return items, generated_at


def render_html(items: list[dict], generated_at: str) -> str:
    counts = {"功能": 0, "招聘": 0, "教程": 0}
    for it in items:
        c = it.get("category")
        if c in counts:
            counts[c] += 1

    # Format display time Asia/Shanghai
    try:
        dt = datetime.fromisoformat(generated_at)
        last_updated_label = dt.strftime("%Y-%m-%d %H:%M") + "（上海时间）"
    except Exception:
        last_updated_label = generated_at

    payload = json.dumps(items, ensure_ascii=False)
    # Escape for script tag safety
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>GMGN 情报站</title>
<meta name="description" content="GMGN 新功能、招聘与教程自动收集时间线" />
<style>
  :root {{
    --bg: #0b0f14;
    --bg2: #121821;
    --card: #161d28;
    --card-hover: #1c2533;
    --border: #243044;
    --text: #e8eef7;
    --muted: #8b9bb4;
    --accent: #6ee7b7;
    --accent2: #60a5fa;
    --warn: #fbbf24;
    --pink: #f472b6;
    --func: #34d399;
    --hire: #fbbf24;
    --tut: #60a5fa;
    --line: #2a3548;
    --shadow: 0 8px 28px rgba(0,0,0,.35);
    --radius: 14px;
    --font: "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
            "Noto Sans SC", system-ui, sans-serif;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: var(--font); }}
  body {{
    min-height: 100vh;
    background:
      radial-gradient(1200px 600px at 10% -10%, rgba(52,211,153,.12), transparent 50%),
      radial-gradient(900px 500px at 90% 0%, rgba(96,165,250,.10), transparent 45%),
      var(--bg);
  }}
  a {{ color: var(--accent2); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .wrap {{ max-width: 820px; margin: 0 auto; padding: 28px 18px 64px; }}
  header.hero {{
    background: linear-gradient(145deg, rgba(22,29,40,.95), rgba(18,24,33,.9));
    border: 1px solid var(--border);
    border-radius: calc(var(--radius) + 4px);
    padding: 28px 24px 22px;
    box-shadow: var(--shadow);
    margin-bottom: 22px;
  }}
  .brand {{
    display: flex; align-items: center; gap: 12px; margin-bottom: 8px;
  }}
  .logo {{
    width: 40px; height: 40px; border-radius: 12px;
    background: linear-gradient(135deg, #34d399, #60a5fa);
    display: grid; place-items: center; font-weight: 800; color: #062016; font-size: 14px;
  }}
  h1 {{ margin: 0; font-size: 1.65rem; letter-spacing: .02em; }}
  .subtitle {{ margin: 8px 0 0; color: var(--muted); line-height: 1.55; font-size: .95rem; }}
  .meta {{
    margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px 14px;
    color: var(--muted); font-size: .85rem;
  }}
  .pill {{
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 999px; padding: 4px 10px;
  }}
  .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
  .dot.func {{ background: var(--func); }}
  .dot.hire {{ background: var(--hire); }}
  .dot.tut {{ background: var(--tut); }}
  .filters {{
    display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px;
    position: sticky; top: 0; z-index: 20;
    padding: 10px 0; background: linear-gradient(180deg, rgba(11,15,20,.96), rgba(11,15,20,.88));
    backdrop-filter: blur(8px);
  }}
  .filters button {{
    border: 1px solid var(--border); background: var(--card); color: var(--text);
    border-radius: 999px; padding: 8px 14px; cursor: pointer; font-size: .9rem;
    transition: .15s ease;
  }}
  .filters button:hover {{ background: var(--card-hover); }}
  .filters button.active {{
    border-color: transparent;
    background: linear-gradient(135deg, rgba(52,211,153,.25), rgba(96,165,250,.25));
    box-shadow: inset 0 0 0 1px rgba(110,231,183,.35);
  }}
  .timeline {{ position: relative; padding-left: 22px; }}
  .timeline::before {{
    content: ""; position: absolute; left: 7px; top: 6px; bottom: 6px;
    width: 2px; background: var(--line);
  }}
  .item {{
    position: relative; margin-bottom: 14px;
  }}
  .item::before {{
    content: ""; position: absolute; left: -19px; top: 18px;
    width: 12px; height: 12px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 0 3px rgba(52,211,153,.18);
  }}
  .item[data-cat="招聘"]::before {{ background: var(--hire); box-shadow: 0 0 0 3px rgba(251,191,36,.18); }}
  .item[data-cat="教程"]::before {{ background: var(--tut); box-shadow: 0 0 0 3px rgba(96,165,250,.18); }}
  .card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 14px 16px 14px;
    transition: .15s ease;
  }}
  .card:hover {{ background: var(--card-hover); border-color: #314159; }}
  .row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 8px; }}
  .badge {{
    font-size: .75rem; font-weight: 700; letter-spacing: .04em;
    border-radius: 6px; padding: 3px 8px;
  }}
  .badge.功能 {{ background: rgba(52,211,153,.15); color: var(--func); }}
  .badge.招聘 {{ background: rgba(251,191,36,.15); color: var(--hire); }}
  .badge.教程 {{ background: rgba(96,165,250,.15); color: var(--tut); }}
  .date {{ color: var(--muted); font-size: .85rem; }}
  .src {{
    margin-left: auto; font-size: .8rem; color: var(--muted);
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 6px; padding: 2px 8px;
  }}
  .title {{ margin: 0 0 6px; font-size: 1.05rem; line-height: 1.4; }}
  .summary {{ margin: 0; color: #c5d0e0; font-size: .92rem; line-height: 1.6; }}
  .link {{ display: inline-block; margin-top: 10px; font-size: .88rem; }}
  .empty {{
    text-align: center; padding: 48px 16px; color: var(--muted);
    border: 1px dashed var(--border); border-radius: var(--radius);
    background: rgba(22,29,40,.5);
  }}
  footer {{
    margin-top: 28px; color: var(--muted); font-size: .8rem; text-align: center;
  }}
  .hidden {{ display: none !important; }}
</style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <div class="brand">
        <div class="logo">G</div>
        <h1>GMGN 情报站</h1>
      </div>
      <p class="subtitle">自动收集的 GMGN 新功能、招聘与教程更新，按时间线展示，最新在最上。数据来自官方 X、Blog、招聘页与文档基线。</p>
      <div class="meta">
        <span class="pill">最近生成：{last_updated_label}</span>
        <span class="pill"><span class="dot func"></span>功能 {counts["功能"]}</span>
        <span class="pill"><span class="dot hire"></span>招聘 {counts["招聘"]}</span>
        <span class="pill"><span class="dot tut"></span>教程 {counts["教程"]}</span>
        <span class="pill">合计 {len(items)}</span>
      </div>
    </header>

    <nav class="filters" id="filters" aria-label="分类筛选">
      <button type="button" data-filter="全部" class="active">全部</button>
      <button type="button" data-filter="功能">功能</button>
      <button type="button" data-filter="招聘">招聘</button>
      <button type="button" data-filter="教程">教程</button>
    </nav>

    <div class="timeline" id="timeline"></div>
    <div class="empty hidden" id="empty">当前分类暂无条目。换个筛选，或等下次例行扫描写入新情报。</div>

    <footer>
      由 GMGN 情报 bot 维护 · 运行 <code>build.py</code> 从基线与 <code>updates/</code> 重新生成 ·
      也可加载同目录 <code>timeline.json</code>
    </footer>
  </div>

  <script id="timeline-data" type="application/json">{payload}</script>
  <script>
    const embedded = JSON.parse(document.getElementById('timeline-data').textContent);
    let items = embedded;

    async function maybeRefresh() {{
      try {{
        const res = await fetch('./timeline.json', {{ cache: 'no-store' }});
        if (res.ok) {{
          const remote = await res.json();
          if (Array.isArray(remote) && remote.length) items = remote;
        }}
      }} catch (_) {{ /* offline / file:// — use embedded */ }}
      render(currentFilter);
    }}

    let currentFilter = '全部';
    const timelineEl = document.getElementById('timeline');
    const emptyEl = document.getElementById('empty');

    function escapeHtml(s) {{
      return String(s ?? '').replace(/[&<>"']/g, c => ({{
        '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
      }})[c]);
    }}

    function render(filter) {{
      currentFilter = filter;
      const list = filter === '全部' ? items : items.filter(i => i.category === filter);
      timelineEl.innerHTML = '';
      if (!list.length) {{
        emptyEl.classList.remove('hidden');
        return;
      }}
      emptyEl.classList.add('hidden');
      for (const it of list) {{
        const div = document.createElement('article');
        div.className = 'item';
        div.dataset.cat = it.category || '';
        const url = it.source_url || '#';
        const hasLink = url && url !== '#';
        div.innerHTML = `
          <div class="card">
            <div class="row">
              <span class="badge ${{escapeHtml(it.category)}}">${{escapeHtml(it.category)}}</span>
              <span class="date">${{escapeHtml(it.date)}}</span>
              <span class="src">${{escapeHtml(it.source_label || '')}}</span>
            </div>
            <h2 class="title">${{escapeHtml(it.title)}}</h2>
            <p class="summary">${{escapeHtml(it.summary)}}</p>
            ${{hasLink ? `<a class="link" href="${{escapeHtml(url)}}" target="_blank" rel="noopener noreferrer">查看来源 →</a>` : ''}}
          </div>`;
        timelineEl.appendChild(div);
      }}
    }}

    document.getElementById('filters').addEventListener('click', (e) => {{
      const btn = e.target.closest('button[data-filter]');
      if (!btn) return;
      document.querySelectorAll('#filters button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      render(btn.dataset.filter);
    }});

    render('全部');
    maybeRefresh();
  </script>
</body>
</html>
"""


def write_outputs(items: list[dict], generated_at: str) -> None:
    meta = {
        "generated_at": generated_at,
        "generated_at_label": "Asia/Shanghai",
        "count": len(items),
        "by_category": {
            "功能": sum(1 for i in items if i["category"] == "功能"),
            "招聘": sum(1 for i in items if i["category"] == "招聘"),
            "教程": sum(1 for i in items if i["category"] == "教程"),
        },
    }
    timeline_doc = items  # canonical is a plain array as specified

    html = render_html(items, generated_at)
    timeline_text = json.dumps(timeline_doc, ensure_ascii=False, indent=2) + "\n"
    meta_text = json.dumps(meta, ensure_ascii=False, indent=2) + "\n"

    destinations = [SITE_DIR]
    if MIRROR_DIR != SITE_DIR:
        destinations.append(MIRROR_DIR)

    for dest in destinations:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "updates").mkdir(parents=True, exist_ok=True)
        (dest / "timeline.json").write_text(timeline_text, encoding="utf-8")
        (dest / "index.html").write_text(html, encoding="utf-8")
        (dest / "build-meta.json").write_text(meta_text, encoding="utf-8")
        # Keep build.py & README in mirror too
        if dest == MIRROR_DIR:
            src_build = SITE_DIR / "build.py"
            if src_build.exists():
                (dest / "build.py").write_text(src_build.read_text(encoding="utf-8"), encoding="utf-8")
            src_readme = SITE_DIR / "README.md"
            if src_readme.exists():
                (dest / "README.md").write_text(src_readme.read_text(encoding="utf-8"), encoding="utf-8")

    print(json.dumps({"ok": True, "meta": meta, "wrote": [str(d) for d in destinations]}, ensure_ascii=False))


def main() -> None:
    items, generated_at = build_timeline()
    write_outputs(items, generated_at)


if __name__ == "__main__":
    main()
