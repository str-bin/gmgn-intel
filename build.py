#!/usr/bin/env python3
"""Rebuild GMGN intel timeline.json + index.html from baselines (+ updates/)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
_KNOWN_STORE = Path("/cursor/stores/store-96e8c890-c974-40ba-84ee-930a023c3a7a")
# Prefer adjacent store root (site/ next to baselines); fall back to known store id.
STORE_ROOT = SITE_DIR.parent if (SITE_DIR.parent / "gmgn-features-baseline.json").exists() else _KNOWN_STORE
MIRROR_DIR = Path("/workspace/gmgn-intel")
# Always keep both site copies in sync when build runs from either location.
SITE_DESTS = []
for _d in (SITE_DIR, STORE_ROOT / "site", MIRROR_DIR):
    if _d not in SITE_DESTS:
        SITE_DESTS.append(_d)

TZ_SHANGHAI = timezone(timedelta(hours=8))

FEATURES_PATH = STORE_ROOT / "gmgn-features-baseline.json"
CAREERS_PATH = STORE_ROOT / "gmgn-careers-baseline.json"
TUTORIALS_PATH = STORE_ROOT / "gmgn-tutorials-baseline.json"
UPDATES_DIR = SITE_DIR / "updates"
SCAN_STATUS_NAME = "scan-status.json"

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



def now_shanghai() -> datetime:
    return datetime.now(TZ_SHANGHAI)


def format_shanghai_label(iso_or_dt) -> str:
    """Human label in Asia/Shanghai, e.g. 2026-10-18 09:00 Asia/Shanghai."""
    if isinstance(iso_or_dt, datetime):
        dt = iso_or_dt
    else:
        s = str(iso_or_dt or "").strip()
        if not s:
            return ""
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return s
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_SHANGHAI)
    local = dt.astimezone(TZ_SHANGHAI)
    return local.strftime("%Y-%m-%d %H:%M") + " Asia/Shanghai"


def load_scan_status() -> dict:
    """Load scan-status.json from site dirs (newest mtime wins)."""
    best = None
    best_mtime = -1.0
    for dest in SITE_DESTS:
        p = dest / SCAN_STATUS_NAME
        if not p.exists():
            continue
        try:
            m = p.stat().st_mtime
            data = json.loads(p.read_text(encoding="utf-8"))
            if m >= best_mtime and isinstance(data, dict):
                best = data
                best_mtime = m
        except Exception:
            continue
    return best or {}


def resolve_scan_status(
    features: dict | None = None,
    *,
    override: dict | None = None,
) -> dict:
    """Merge CLI/file override with baselines into a displayable scan status."""
    features = features or {}
    file_st = load_scan_status()
    ov = override or {}

    last_checked = (
        ov.get("last_checked")
        or file_st.get("last_checked")
        or features.get("last_checked")
        or ""
    )
    last_checked_label = (
        ov.get("last_checked_label")
        or file_st.get("last_checked_label")
        or features.get("last_checked_label")
        or format_shanghai_label(last_checked)
    )

    if "has_new" in ov:
        has_new = bool(ov.get("has_new"))
    elif "has_new" in file_st:
        has_new = bool(file_st.get("has_new"))
    else:
        has_new = False

    if "new_count" in ov:
        try:
            new_count = int(ov.get("new_count") or 0)
        except Exception:
            new_count = 0
    elif "new_count" in file_st:
        try:
            new_count = int(file_st.get("new_count") or 0)
        except Exception:
            new_count = 0
    else:
        new_count = 0

    if has_new and new_count <= 0:
        new_count = max(new_count, 1)
    if not has_new:
        new_count = 0

    if has_new:
        result = f"有新增 · {new_count} 条" if new_count else "有新增"
        result_short = "有新增"
    else:
        result = "无新增"
        result_short = "无新增"

    if ov.get("result"):
        result = str(ov["result"])
        result_short = result

    return {
        "last_checked": last_checked,
        "last_checked_label": last_checked_label,
        "has_new": has_new,
        "new_count": new_count,
        "result": result,
        "result_short": result_short,
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


def _feature_bullets(pf: dict | None) -> str:
    """Format product_features dict into 【已有】/【在推】/【要做】 bullets."""
    if not pf:
        return ""
    parts: list[str] = []
    mapping = [
        ("already", "【已有】"),
        ("pushing", "【在推】"),
        ("building", "【要做/从招聘推断】"),
    ]
    for key, label in mapping:
        bullets = pf.get(key) or []
        if not bullets:
            continue
        parts.append(label)
        for b in bullets:
            parts.append(f"• {b}")
    plus = pf.get("plus_signals") or []
    if plus:
        parts.append("【加分信号/相邻能力】")
        for b in plus:
            parts.append(f"• {b}")
    return ("\n" + "\n".join(parts)) if parts else ""


def from_careers(data: dict, collected: str) -> list[dict]:
    """Careers → timeline: lead with PRODUCT DIRECTION, not job titles."""
    items = []
    for r in data.get("open_roles") or []:
        date = r.get("posted") or ""
        role = r.get("title_zh") or r.get("title_en") or ""
        url = r.get("url_zh") or r.get("url_en") or ""
        pf = r.get("product_features") or {}
        title = r.get("timeline_title") or (
            f"产品方向信号（招聘）：{role}" if role else "产品方向信号（招聘）"
        )
        # Lead with capability; mention JD only as evidence footnote
        head = "从招聘 JD 推断的产品能力方向（岗位名不重要，看要建什么）。"
        if role:
            head += f" 证据岗：{role}。"
        head += " 投递 hr@gmgn.ai。"
        summary = head + _feature_bullets(pf)
        if not pf and r.get("summary"):
            summary += f"\n【要做/从招聘推断】\n• {r['summary']}"
        items.append(
            make_item(
                date=date,
                category="招聘",
                title=title,
                summary=summary,
                source_url=url,
                source_label="Careers JD",
                collected_at=collected,
            )
        )
    for r in data.get("x_only_or_unlisted") or []:
        date = r.get("posted") or ""
        role = r.get("title") or ""
        url = r.get("source") or ""
        pf = r.get("product_features") or {}
        title = r.get("timeline_title") or (
            f"产品方向信号（X 招聘）：{role}" if role else "产品方向信号（X 招聘）"
        )
        head = "从 X 招聘帖推断的产品能力方向（岗位名不重要）。"
        if role:
            head += f" 证据：{role}。"
        if r.get("apply_hint"):
            head += f" {r['apply_hint']}。"
        if r.get("status"):
            head += f"（{r['status']}）"
        summary = head + _feature_bullets(pf)
        items.append(
            make_item(
                date=date,
                category="招聘",
                title=title,
                summary=summary,
                source_url=url,
                source_label="X",
                collected_at=collected,
            )
        )
    # Optional roadmap rollup entry (newest product-direction summary)
    roadmap = data.get("product_roadmap_from_hiring") or {}
    themes = roadmap.get("themes") or []
    if themes and roadmap.get("summary_zh"):
        # One rollup card dated to last_checked day so it sits near top when refreshed
        lc = (data.get("last_checked") or collected)[:10]
        bullets = ["【要做/从招聘推断｜总览】"]
        for t in themes:
            if (t.get("signal_strength") or "") in ("strong", "medium"):
                building = t.get("building") or []
                tip = building[0] if building else ""
                line = f"• {t.get('title_zh')}"
                if tip:
                    line += f" — 例：{tip}"
                bullets.append(line)
        items.append(
            make_item(
                date=lc,
                category="招聘",
                title="招聘信号汇总：GMGN 正在加码的产品能力",
                summary=(roadmap.get("summary_zh") or "") + "\n" + "\n".join(bullets),
                source_url=(data.get("channels") or {}).get("careers_hub_zh")
                or "https://gmgn.ai/blog/zh-cn/careers/",
                source_label="Careers 汇总",
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
        summary = it.get("summary") or ""
        s = 0
        if url and url.rstrip("/") != "https://gmgn.ai/blog":
            s += 2
        if summary:
            s += 1
        # Prefer entries that spell out 功能点 / longer analysis
        if "【已有】" in summary or "【要做" in summary or "【在推】" in summary:
            s += 5
        s += min(len(summary) // 80, 5)
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


def build_watch_sources(features: dict) -> dict:
    """Build left-panel watch list from features baseline official_channels / watch_x_accounts."""
    ch = features.get("official_channels") or {}
    watch = features.get("watch_x_accounts") or ["@gmgnai", "@gmgnapp001", "@haze0x"]

    x_meta = {
        "@gmgnai": {
            "title": "@gmgnai",
            "url": (ch.get("x_primary") or {}).get("url") or "https://x.com/gmgnai",
            "intro": "官方主账号。产品新功能、链上能力与活动公告的主发布渠道；文档亦指向其 Highlights。",
            "extra": (ch.get("x_primary") or {}).get("highlights"),
            "extra_label": "Highlights",
        },
        "@gmgnapp001": {
            "title": "@gmgnapp001",
            "url": (ch.get("x_app") or {}).get("url") or "https://x.com/gmgnapp001",
            "intro": "App / 产品演示账号。常发功能视频与 GO/移动端演示，常被 @gmgnai 引用。",
            "extra": None,
            "extra_label": None,
        },
        "@haze0x": {
            "title": "@haze0x",
            "url": (ch.get("x_haze") or {}).get("url") or "https://x.com/haze0x",
            "intro": "Haze（Cooking gmgn.ai）。招聘置顶与产品路线/风向；与招聘页互补，偶有未上 Hub 的岗位。",
            "extra": None,
            "extra_label": None,
        },
    }

    x_accounts = []
    for handle in watch:
        meta = x_meta.get(handle) or {
            "title": handle,
            "url": f"https://x.com/{handle.lstrip('@')}",
            "intro": "日常监控中的 X 账号。",
            "extra": None,
            "extra_label": None,
        }
        x_accounts.append(meta)

    websites = [
        {
            "title": "GMGN 官网",
            "url": ch.get("website") or "https://gmgn.ai",
            "intro": "产品站。站内 Feature Updates 弹窗是官方更新源之一（无独立公开 URL，需站内打开）。",
        },
        {
            "title": "Blog（教程/指南）",
            "url": ch.get("blog") or "https://gmgn.ai/blog/",
            "intro": "英文 Blog：交易教程与产品用法；中文见 blog/zh-cn。",
        },
        {
            "title": "中文 Blog",
            "url": ch.get("blog_zh") or "https://gmgn.ai/blog/zh-cn/",
            "intro": "中文博客与部分本地化教程入口。",
        },
        {
            "title": "招聘页（中文）",
            "url": ch.get("careers_hub_zh") or "https://gmgn.ai/blog/zh-cn/careers/",
            "intro": "在招岗位 Hub（投递 hr@gmgn.ai）。可从 JD 推断产品在加码的能力方向。",
        },
        {
            "title": "招聘页（英文）",
            "url": ch.get("careers_hub_en") or "https://gmgn.ai/blog/careers/",
            "intro": "英文招聘 Hub，与中文页及 @haze0x 置顶互补。",
        },
        {
            "title": "文档更新说明",
            "url": ch.get("docs_update_page") or "https://docs.gmgn.ai/index/gmgn-update-announcement",
            "intro": "Docs 上的更新公告页；官方说明与 X Highlights 并列的更新渠道。",
        },
        {
            "title": "Docs 首页",
            "url": ch.get("docs_home") or "https://docs.gmgn.ai",
            "intro": "产品文档总入口，含 API / Skills / 功能说明。",
        },
        {
            "title": "Memecoin 教程站",
            "url": ch.get("memecoin_tutorials") or "https://memecoin.gmgn.ai/",
            "intro": "面向 meme 交易的专题教程站，补 Blog 之外的用法说明。",
        },
        {
            "title": "AI Hub / Skills",
            "url": ch.get("ai_hub") or "https://gmgn.ai/ai",
            "intro": "Giga AI 与 Skills Market；新 Skill 上线常在此可见。",
        },
        {
            "title": "GitHub Discussions",
            "url": ch.get("github_discussions") or "https://github.com/GMGNAI/gmgn-skills/discussions",
            "intro": "gmgn-skills 讨论区，偶有能力与接入相关更新。",
        },
    ]

    return {
        "x_accounts": x_accounts,
        "websites": websites,
        "last_checked": features.get("last_checked") or "",
        "last_checked_label": features.get("last_checked_label") or "",
    }


def _esc_html(s: str) -> str:
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _valid_http_url(u: object) -> str:
    """Return stripped http(s) URL, or empty string if missing/invalid."""
    if not isinstance(u, str):
        return ""
    s = u.strip()
    if not s:
        return ""
    if s.startswith(("http://", "https://")):
        return s
    return ""


def render_sources_panel(sources: dict) -> str:
    """Left panel: watched X accounts + websites. Never nest <a>, never empty chips."""
    x_blocks = []
    for acc in sources.get("x_accounts") or []:
        url = _valid_http_url(acc.get("url")) or "#"
        title = _esc_html(acc.get("title", ""))
        intro = _esc_html(acc.get("intro", ""))
        extra_url = _valid_http_url(acc.get("extra"))
        extra_label = (acc.get("extra_label") or "").strip()
        extra = ""
        # Only render a secondary link when both URL and label are real (no empty pill).
        if extra_url and extra_label:
            extra = (
                f'<a class="src-extra" href="{_esc_html(extra_url)}" target="_blank" '
                f'rel="noopener noreferrer">{_esc_html(extra_label)} →</a>'
            )
        # Card is NOT an <a> — title + optional extra are separate links (avoids nested <a> empty box).
        title_html = (
            f'<a class="src-title" href="{_esc_html(url)}" target="_blank" '
            f'rel="noopener noreferrer">{title}</a>'
            if url != "#"
            else f'<div class="src-title">{title}</div>'
        )
        x_blocks.append(
            f'<article class="src-card">'
            f'<div class="src-kind x" aria-hidden="true">X</div>'
            f'<div class="src-body">'
            f"{title_html}"
            f'<div class="src-intro">{intro}</div>'
            f"{extra}"
            f"</div></article>"
        )

    web_blocks = []
    for site in sources.get("websites") or []:
        url = _valid_http_url(site.get("url")) or "#"
        title = _esc_html(site.get("title", ""))
        intro = _esc_html(site.get("intro", ""))
        title_html = (
            f'<a class="src-title" href="{_esc_html(url)}" target="_blank" '
            f'rel="noopener noreferrer">{title}</a>'
            if url != "#"
            else f'<div class="src-title">{title}</div>'
        )
        web_blocks.append(
            f'<article class="src-card">'
            f'<div class="src-kind web" aria-hidden="true">站</div>'
            f'<div class="src-body">'
            f"{title_html}"
            f'<div class="src-intro">{intro}</div>'
            f"</div></article>"
        )

    scan_hint = ""
    label = (sources.get("last_checked_label") or sources.get("last_checked") or "").strip()
    result = (sources.get("scan_result") or "").strip()
    if label or result:
        parts = []
        if label:
            parts.append(f"最近扫描：{_esc_html(label)}")
        if result:
            parts.append(f"本次：{_esc_html(result)}")
        scan_hint = f'<div class="panel-hint">{" · ".join(parts)}</div>'

    x_count = len(sources.get("x_accounts") or [])
    web_count = len(sources.get("websites") or [])
    count_label = f"{x_count + web_count} 个来源"

    return (
        '<aside class="panel-left" id="watch-panel" aria-label="正在盯着的来源">'
        '<button type="button" class="panel-toggle" id="watch-toggle" '
        'aria-expanded="true" aria-controls="watch-body">'
        '<div class="panel-head">'
        '<div class="panel-title-row">'
        "<h2>正在盯着</h2>"
        f'<span class="panel-count">{_esc_html(count_label)}</span>'
        '<span class="chevron" aria-hidden="true"></span>'
        "</div>"
        '<p class="panel-desc">日常扫描的 X 账号与网站；有变化写入右侧时间线。</p>'
        f"{scan_hint}"
        "</div>"
        "</button>"
        '<div class="panel-body" id="watch-body">'
        '<section class="src-section">'
        "<h3>X 账号</h3>"
        f'<div class="src-list">{"".join(x_blocks)}</div>'
        "</section>"
        '<section class="src-section">'
        "<h3>网站 / 文档</h3>"
        f'<div class="src-list">{"".join(web_blocks)}</div>'
        "</section>"
        "</div>"
        "</aside>"
    )

CSS_TEMPLATE = '''
  :root {
    --bg: #000000;
    --bg-elevated: #0a0a0a;
    --bg-hover: #111111;
    --border: #1a1a1a;
    --border-hover: #333333;
    --text: #ededed;
    --text-secondary: #a1a1a1;
    --text-tertiary: #666666;
    --accent: #fff;
    --accent-muted: #888;
    --func: #50e3c2;
    --hire: #f5a623;
    --tut: #0070f3;
    --line: #222;
    --radius: 8px;
    --left-w: 300px;
    --font: "Inter", "Geist", ui-sans-serif, system-ui, -apple-system, "Segoe UI",
            "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC",
            sans-serif;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0;
    background: var(--bg); color: var(--text);
    font-family: var(--font);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  body { min-height: 100vh; }
  a { color: var(--text); text-decoration: none; }
  a:hover { color: #fff; }
  code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: .85em; color: var(--text-secondary);
  }
  .shell {
    max-width: 1200px; margin: 0 auto; padding: 32px 24px 64px;
  }
  header.hero {
    border-bottom: 1px solid var(--border);
    padding: 0 0 24px;
    margin-bottom: 24px;
  }
  .brand {
    display: flex; align-items: center; gap: 12px; margin-bottom: 8px;
  }
  .logo {
    width: 28px; height: 28px; border-radius: 6px;
    background: #fff; color: #000;
    display: grid; place-items: center; font-weight: 700; font-size: 13px;
    letter-spacing: -0.02em;
  }
  h1 {
    margin: 0; font-size: 1.25rem; font-weight: 600;
    letter-spacing: -0.02em; line-height: 1.2;
  }
  .subtitle {
    margin: 8px 0 0; color: var(--text-secondary);
    line-height: 1.55; font-size: .875rem; max-width: 56rem;
  }
  .meta {
    margin-top: 16px; display: flex; flex-wrap: wrap; gap: 8px;
    color: var(--text-secondary); font-size: .75rem;
  }
  .pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: transparent; border: 1px solid var(--border);
    border-radius: 999px; padding: 4px 10px; color: var(--text-secondary);
  }
  .pill.scan-time {
    border-color: #333; color: var(--text);
  }
  .pill.result-new {
    border-color: rgba(80, 227, 194, 0.45); color: var(--func);
  }
  .pill.result-quiet {
    border-color: var(--border); color: var(--text-secondary);
  }
  .dot { width: 6px; height: 6px; border-radius: 50%; }
  .dot.func { background: var(--func); }
  .dot.hire { background: var(--hire); }
  .dot.tut { background: var(--tut); }

  .layout {
    display: grid;
    grid-template-columns: var(--left-w) minmax(0, 1fr);
    gap: 32px;
    align-items: start;
  }

  .panel-left {
    position: sticky; top: 16px;
    max-height: calc(100vh - 32px);
    overflow: auto;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg-elevated);
    padding: 0;
  }
  .panel-left::-webkit-scrollbar { width: 4px; }
  .panel-left::-webkit-scrollbar-thumb { background: #333; border-radius: 999px; }
  .panel-toggle {
    display: block; width: 100%; text-align: left;
    background: transparent; border: 0; color: inherit;
    padding: 16px; cursor: pointer;
    font: inherit;
  }
  .panel-toggle:hover { background: var(--bg-hover); }
  .panel-toggle:focus-visible {
    outline: 2px solid var(--accent, #0070f3);
    outline-offset: -2px;
  }
  .panel-title-row {
    display: flex; align-items: center; gap: 8px;
  }
  .panel-title-row h2 {
    margin: 0; font-size: .9375rem; font-weight: 600;
    letter-spacing: -0.01em; flex: 0 1 auto;
  }
  .panel-count {
    font-size: .6875rem; color: var(--text-tertiary);
    border: 1px solid var(--border); border-radius: 999px;
    padding: 1px 7px; line-height: 1.4;
  }
  .chevron {
    margin-left: auto; flex: 0 0 auto;
    width: 16px; height: 16px; position: relative;
    transition: transform .18s ease;
  }
  .chevron::before {
    content: ""; position: absolute; inset: 4px;
    border-right: 1.5px solid var(--text-secondary);
    border-bottom: 1.5px solid var(--text-secondary);
    transform: rotate(45deg); /* points down when expanded */
  }
  .panel-left.is-collapsed .chevron { transform: rotate(-90deg); } /* points right */
  .panel-desc {
    margin: 6px 0 0; color: var(--text-secondary); font-size: .75rem; line-height: 1.5;
  }
  .panel-hint {
    margin-top: 10px; font-size: .6875rem; color: var(--text-tertiary);
    border-top: 1px solid var(--border); padding-top: 10px;
  }
  .panel-body { padding: 0 16px 16px; }
  .panel-left.is-collapsed .panel-desc,
  .panel-left.is-collapsed .panel-hint,
  .panel-left.is-collapsed .panel-body { display: none; }
  .panel-left.is-collapsed {
    max-height: none; overflow: visible;
  }
  .panel-left.is-collapsed .panel-toggle { padding-bottom: 14px; }
  .src-section { margin-top: 18px; }
  .src-section h3 {
    margin: 0 0 8px; font-size: .6875rem; letter-spacing: .08em;
    text-transform: uppercase; color: var(--text-tertiary); font-weight: 500;
  }
  .src-list { display: flex; flex-direction: column; gap: 2px; }
  .src-card {
    display: flex; gap: 10px; align-items: flex-start;
    border-radius: 6px; padding: 8px;
    transition: background .12s ease;
  }
  .src-card:hover { background: var(--bg-hover); }
  .src-kind {
    flex: 0 0 auto; width: 22px; height: 22px; border-radius: 4px;
    display: grid; place-items: center;
    font-size: .625rem; font-weight: 600;
    border: 1px solid var(--border); color: var(--text-secondary);
    margin-top: 1px;
  }
  .src-kind.x { color: var(--text-secondary); }
  .src-kind.web { color: var(--text-secondary); }
  .src-body { min-width: 0; flex: 1; }
  a.src-title, .src-title {
    display: block;
    font-size: .8125rem; font-weight: 500; line-height: 1.35;
    margin-bottom: 2px; color: var(--text);
    letter-spacing: -0.01em;
  }
  a.src-title:hover { color: #fff; text-decoration: underline; text-underline-offset: 2px; }
  .src-intro {
    font-size: .6875rem; color: var(--text-tertiary); line-height: 1.45;
  }
  a.src-extra {
    display: inline-block; margin-top: 6px;
    font-size: .6875rem; color: var(--text-secondary);
    border: none; padding: 0; background: none;
  }
  a.src-extra:hover { color: #fff; text-decoration: underline; text-underline-offset: 2px; }

  .panel-right { min-width: 0; }
  .panel-right-head {
    display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between;
    gap: 8px; margin-bottom: 12px;
  }
  .panel-right-head h2 {
    margin: 0; font-size: .9375rem; font-weight: 600; letter-spacing: -0.01em;
  }
  .panel-right-head .hint {
    color: var(--text-tertiary); font-size: .75rem;
  }

  .filters {
    display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 16px;
    position: sticky; top: 0; z-index: 20;
    padding: 8px 0;
    background: rgba(0,0,0,.85);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
  }
  .filters button {
    border: 1px solid var(--border); background: transparent; color: var(--text-secondary);
    border-radius: 999px; padding: 5px 12px; cursor: pointer; font-size: .8125rem;
    font-family: inherit; transition: .12s ease;
  }
  .filters button:hover { border-color: var(--border-hover); color: var(--text); }
  .filters button.active {
    border-color: #fff; background: #fff; color: #000; font-weight: 500;
  }
  .timeline { position: relative; padding-left: 20px; }
  .timeline::before {
    content: ""; position: absolute; left: 5px; top: 4px; bottom: 4px;
    width: 1px; background: var(--line);
  }
  .item { position: relative; margin-bottom: 12px; }
  .item::before {
    content: ""; position: absolute; left: -17px; top: 16px;
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--text-tertiary); border: 1px solid var(--bg);
  }
  .item[data-cat="功能"]::before { background: var(--func); }
  .item[data-cat="招聘"]::before { background: var(--hire); }
  .item[data-cat="教程"]::before { background: var(--tut); }
  .card {
    border: 1px solid var(--border);
    border-radius: var(--radius); padding: 14px 16px;
    background: var(--bg-elevated);
    transition: border-color .12s ease;
  }
  .card:hover { border-color: var(--border-hover); }
  .row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 8px; }
  .badge {
    font-size: .6875rem; font-weight: 500; letter-spacing: .02em;
    border-radius: 4px; padding: 2px 7px;
    border: 1px solid var(--border);
  }
  .badge.功能 { color: var(--func); border-color: rgba(80,227,194,.25); }
  .badge.招聘 { color: var(--hire); border-color: rgba(245,166,35,.25); }
  .badge.教程 { color: var(--tut); border-color: rgba(0,112,243,.3); }
  .date { color: var(--text-tertiary); font-size: .75rem; }
  .src {
    margin-left: auto; font-size: .6875rem; color: var(--text-tertiary);
    border: 1px solid var(--border); border-radius: 4px; padding: 1px 6px;
  }
  .src:empty { display: none; }
  .title {
    margin: 0 0 6px; font-size: .9375rem; line-height: 1.4;
    font-weight: 500; letter-spacing: -0.01em;
  }
  .summary {
    margin: 0; color: var(--text-secondary); font-size: .8125rem;
    line-height: 1.65; white-space: pre-wrap;
  }
  .summary .fp-label {
    display: inline-block;
    font-weight: 700;
    letter-spacing: .01em;
    color: #fff;
    border-radius: 4px;
    padding: 1px 7px;
    margin: 6px 0 2px;
    line-height: 1.5;
  }
  .summary .fp-label.fp-already {
    background: rgba(80, 227, 194, .18);
    border: 1px solid rgba(80, 227, 194, .4);
    color: #7dffd6;
  }
  .summary .fp-label.fp-pushing {
    background: rgba(0, 112, 243, .2);
    border: 1px solid rgba(0, 112, 243, .45);
    color: #7eb6ff;
  }
  .summary .fp-label.fp-building {
    background: rgba(245, 166, 35, .2);
    border: 1px solid rgba(245, 166, 35, .45);
    color: #ffc86b;
  }
  .summary .fp-label.fp-other {
    background: rgba(255, 255, 255, .1);
    border: 1px solid rgba(255, 255, 255, .18);
    color: #fff;
  }
  .summary .fp-line {
    display: block;
    font-weight: 700;
    color: #f5f5f5;
    background: linear-gradient(90deg, rgba(255,255,255,.1), rgba(255,255,255,.03) 70%, transparent);
    border-left: 2px solid rgba(255,255,255,.35);
    padding: 3px 10px;
    margin: 3px 0;
    border-radius: 0 6px 6px 0;
  }
  .summary .fp-line.fp-already { border-left-color: rgba(80, 227, 194, .7); background: linear-gradient(90deg, rgba(80,227,194,.14), transparent); }
  .summary .fp-line.fp-pushing { border-left-color: rgba(0, 112, 243, .7); background: linear-gradient(90deg, rgba(0,112,243,.14), transparent); }
  .summary .fp-line.fp-building { border-left-color: rgba(245, 166, 35, .75); background: linear-gradient(90deg, rgba(245,166,35,.14), transparent); }
  .summary .fp-line.fp-other { border-left-color: rgba(255,255,255,.4); }
  .link {
    display: inline-block; margin-top: 10px; font-size: .8125rem;
    color: var(--text-secondary);
  }
  .link:hover { color: #fff; text-decoration: underline; text-underline-offset: 2px; }
  .empty {
    text-align: center; padding: 48px 16px; color: var(--text-tertiary);
    border: 1px dashed var(--border); border-radius: var(--radius);
    font-size: .875rem;
  }
  footer {
    margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--border);
    color: var(--text-tertiary); font-size: .75rem; text-align: center;
  }
  .hidden { display: none !important; }

  @media (max-width: 960px) {
    .layout { grid-template-columns: 1fr; gap: 24px; }
    .panel-left { position: static; max-height: none; overflow: visible; }
  }
  @media (max-width: 560px) {
    .shell { padding: 20px 16px 48px; }
    h1 { font-size: 1.125rem; }
  }
'''

JS_TEMPLATE = '''
    const embedded = JSON.parse(document.getElementById('timeline-data').textContent);
    let items = embedded;

    async function maybeRefresh() {
      try {
        const res = await fetch('./timeline.json', { cache: 'no-store' });
        if (res.ok) {
          const remote = await res.json();
          if (Array.isArray(remote) && remote.length) items = remote;
        }
      } catch (_) { /* offline / file:// — use embedded */ }
      render(currentFilter);
    }

    let currentFilter = '全部';
    const timelineEl = document.getElementById('timeline');
    const emptyEl = document.getElementById('empty');

    function escapeHtml(s) {
      return String(s ?? '').replace(/[&<>"']/g, c => ({
        '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
      })[c]);
    }

    function fpKind(label) {
      if (label.includes('已有')) return 'fp-already';
      if (label.includes('在推')) return 'fp-pushing';
      if (label.includes('要做') || label.includes('招聘推断') || label.includes('加分')) return 'fp-building';
      if (label.includes('功能推断') || label.includes('相邻')) return 'fp-other';
      return 'fp-other';
    }

    function formatSummary(raw) {
      const text = String(raw ?? '');
      if (!text) return '';
      const lines = text.split('\\n');
      let kind = null;
      const out = [];
      for (const line of lines) {
        const trimmed = line.trim();
        const labelMatch = trimmed.match(/^(【[^】]+】)[ \\t]*(.*)$/);
        if (labelMatch && /^【/.test(trimmed)) {
          const lab = labelMatch[1];
          const rest = (labelMatch[2] || '').trim();
          kind = fpKind(lab);
          out.push('<span class="fp-label ' + kind + '">' + escapeHtml(lab) + '</span>');
          if (rest) {
            out.push('<span class="fp-line ' + kind + '">' + escapeHtml(rest) + '</span>');
          }
          continue;
        }
        if (kind && /^[•*-]/.test(trimmed)) {
          out.push('<span class="fp-line ' + kind + '">' + escapeHtml(trimmed) + '</span>');
          continue;
        }
        if (!trimmed) {
          out.push('');
          continue;
        }
        out.push(escapeHtml(line));
      }
      return out.join('\\n');
    }

    function render(filter) {
      currentFilter = filter;
      const list = filter === '全部' ? items : items.filter(i => i.category === filter);
      timelineEl.innerHTML = '';
      if (!list.length) {
        emptyEl.classList.remove('hidden');
        return;
      }
      emptyEl.classList.add('hidden');
      for (const it of list) {
        const div = document.createElement('article');
        div.className = 'item';
        div.dataset.cat = it.category || '';
        const url = it.source_url || '#';
        const hasLink = url && url !== '#';
        div.innerHTML = `
          <div class="card">
            <div class="row">
              <span class="badge ${escapeHtml(it.category)}">${escapeHtml(it.category)}</span>
              <span class="date">${escapeHtml(it.date)}</span>
              ${it.source_label ? `<span class="src">${escapeHtml(it.source_label)}</span>` : ''}
            </div>
            <h2 class="title">${escapeHtml(it.title)}</h2>
            <div class="summary">${formatSummary(it.summary)}</div>
            ${hasLink ? `<a class="link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">查看来源 →</a>` : ''}
          </div>`;
        timelineEl.appendChild(div);
      }
    }

    document.getElementById('filters').addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-filter]');
      if (!btn) return;
      document.querySelectorAll('#filters button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      render(btn.dataset.filter);
    });

    render('全部');
    maybeRefresh();

    (function initWatchCollapse() {
      const panel = document.getElementById('watch-panel');
      const toggle = document.getElementById('watch-toggle');
      if (!panel || !toggle) return;
      const KEY = 'gmgn-watch-collapsed';
      function apply(collapsed) {
        panel.classList.toggle('is-collapsed', collapsed);
        toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      }
      let stored = null;
      try { stored = localStorage.getItem(KEY); } catch (_) {}
      if (stored === '1') apply(true);
      else if (stored === '0') apply(false);
      else apply(window.matchMedia('(max-width: 960px)').matches);
      toggle.addEventListener('click', () => {
        const next = !panel.classList.contains('is-collapsed');
        apply(next);
        try { localStorage.setItem(KEY, next ? '1' : '0'); } catch (_) {}
      });
    })();
'''


def render_html(
    items: list[dict],
    generated_at: str,
    sources: dict | None = None,
    scan_status: dict | None = None,
) -> str:
    counts = {"功能": 0, "招聘": 0, "教程": 0}
    for it in items:
        c = it.get("category")
        if c in counts:
            counts[c] += 1

    features = load_json(FEATURES_PATH) if FEATURES_PATH.exists() else {}
    scan = resolve_scan_status(features, override=scan_status)
    scan_time_label = (scan.get("last_checked_label") or format_shanghai_label(scan.get("last_checked")) or "").strip()
    if not scan_time_label:
        try:
            dt = datetime.fromisoformat(generated_at)
            scan_time_label = dt.strftime("%Y-%m-%d %H:%M") + " Asia/Shanghai"
        except Exception:
            scan_time_label = generated_at
    scan_result = (scan.get("result") or ("有新增" if scan.get("has_new") else "无新增")).strip()
    result_class = "result-new" if scan.get("has_new") else "result-quiet"

    if sources is None:
        sources = build_watch_sources(features)
    # Inject scan fields so left panel stays in sync with hero
    sources = dict(sources)
    sources["last_checked"] = scan.get("last_checked") or sources.get("last_checked") or ""
    sources["last_checked_label"] = scan_time_label
    sources["scan_result"] = scan_result

    sources_html = render_sources_panel(sources)

    payload = json.dumps(items, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("</", "<\\/")

    css = CSS_TEMPLATE
    js = JS_TEMPLATE

    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        "<title>GMGN 情报站</title>\n"
        '<meta name="description" content="GMGN 新功能、招聘与教程自动收集时间线" />\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />\n'
        "<style>\n"
        f"{css}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        '  <div class="shell">\n'
        '    <header class="hero">\n'
        '      <div class="brand">\n'
        '        <div class="logo">G</div>\n'
        "        <h1>GMGN 情报站</h1>\n"
        "      </div>\n"
        '      <p class="subtitle">自动收集的 GMGN 新功能、招聘与教程更新。左侧是正在盯着的账号与网站；右侧是时间线（最新在上）。摘要中的【已有】/【在推】/【要做】标出可推断的功能点。</p>\n'
        '      <div class="meta">\n'
        f'        <span class="pill scan-time">最近扫描：{_esc_html(scan_time_label)}</span>\n'
        f'        <span class="pill {result_class}">本次：{_esc_html(scan_result)}</span>\n'
        f'        <span class="pill"><span class="dot func"></span>功能 {counts["功能"]}</span>\n'
        f'        <span class="pill"><span class="dot hire"></span>招聘 {counts["招聘"]}</span>\n'
        f'        <span class="pill"><span class="dot tut"></span>教程 {counts["教程"]}</span>\n'
        f'        <span class="pill">合计 {len(items)}</span>\n'
        "      </div>\n"
        "    </header>\n"
        '    <div class="layout">\n'
        f"      {sources_html}\n"
        '      <main class="panel-right" aria-label="情报时间线">\n'
        '        <div class="panel-right-head">\n'
        "          <h2>情报时间线</h2>\n"
        '          <span class="hint">最新在上 · 可按类别筛选</span>\n'
        "        </div>\n"
        '        <nav class="filters" id="filters" aria-label="分类筛选">\n'
        '          <button type="button" data-filter="全部" class="active">全部</button>\n'
        '          <button type="button" data-filter="功能">功能</button>\n'
        '          <button type="button" data-filter="招聘">招聘</button>\n'
        '          <button type="button" data-filter="教程">教程</button>\n'
        "        </nav>\n"
        '        <div class="timeline" id="timeline"></div>\n'
        '        <div class="empty hidden" id="empty">当前分类暂无条目。换个筛选，或等下次例行扫描写入新情报。</div>\n'
        "      </main>\n"
        "    </div>\n"
        "    <footer>\n"
        "      由 GMGN 情报 bot 维护 · 运行 <code>build.py</code> 从基线与 <code>updates/</code> 重新生成 ·\n"
        "      也可加载同目录 <code>timeline.json</code>\n"
        "    </footer>\n"
        "  </div>\n"
        f'  <script id="timeline-data" type="application/json">{payload}</script>\n'
        "<script>\n"
        f"{js}\n"
        "</script>\n"
        "</body>\n"
        "</html>\n"
    )

def write_outputs(
    items: list[dict],
    generated_at: str,
    sources: dict | None = None,
    scan_status: dict | None = None,
) -> None:
    features = load_json(FEATURES_PATH) if FEATURES_PATH.exists() else {}
    scan = resolve_scan_status(features, override=scan_status)

    meta = {
        "generated_at": generated_at,
        "generated_at_label": "Asia/Shanghai",
        "count": len(items),
        "by_category": {
            "功能": sum(1 for i in items if i["category"] == "功能"),
            "招聘": sum(1 for i in items if i["category"] == "招聘"),
            "教程": sum(1 for i in items if i["category"] == "教程"),
        },
        "last_checked": scan.get("last_checked") or "",
        "last_checked_label": scan.get("last_checked_label") or "",
        "scan_has_new": bool(scan.get("has_new")),
        "scan_new_count": int(scan.get("new_count") or 0),
        "scan_result": scan.get("result") or "",
    }
    timeline_doc = items  # canonical is a plain array as specified

    if sources is None:
        sources = build_watch_sources(features)
    html = render_html(items, generated_at, sources, scan)
    timeline_text = json.dumps(timeline_doc, ensure_ascii=False, indent=2) + "\n"
    meta_text = json.dumps(meta, ensure_ascii=False, indent=2) + "\n"
    scan_text = json.dumps(scan, ensure_ascii=False, indent=2) + "\n"

    destinations: list[Path] = []
    for d in SITE_DESTS:
        if d not in destinations:
            destinations.append(d)

    src_build = Path(__file__).resolve()
    src_readme = SITE_DIR / "README.md"
    if not src_readme.exists():
        alt = STORE_ROOT / "site" / "README.md"
        if alt.exists():
            src_readme = alt

    for dest in destinations:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "updates").mkdir(parents=True, exist_ok=True)
        (dest / "timeline.json").write_text(timeline_text, encoding="utf-8")
        (dest / "index.html").write_text(html, encoding="utf-8")
        (dest / "build-meta.json").write_text(meta_text, encoding="utf-8")
        (dest / SCAN_STATUS_NAME).write_text(scan_text, encoding="utf-8")
        if dest.resolve() != src_build.parent.resolve():
            (dest / "build.py").write_text(src_build.read_text(encoding="utf-8"), encoding="utf-8")
        if src_readme.exists() and dest.resolve() != src_readme.parent.resolve():
            (dest / "README.md").write_text(src_readme.read_text(encoding="utf-8"), encoding="utf-8")

    print(json.dumps({"ok": True, "meta": meta, "scan": scan, "wrote": [str(d) for d in destinations]}, ensure_ascii=False))


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Rebuild GMGN intel site from baselines (+ updates/).")
    ap.add_argument("--has-new", dest="has_new", action="store_true", default=None, help="Mark this scan as having new items")
    ap.add_argument("--no-new", dest="has_new", action="store_false", help="Mark this scan as quiet (无新增)")
    ap.add_argument("--new-count", type=int, default=None, help="Number of new timeline items this scan")
    ap.add_argument("--last-checked", default=None, help="ISO timestamp of this scan (Asia/Shanghai)")
    ap.add_argument("--last-checked-label", default=None, help="Display label for scan time")
    ap.add_argument("--result", default=None, help="Override result text, e.g. 有新增 · 2 条")
    args = ap.parse_args()

    items, generated_at = build_timeline()
    features = load_json(FEATURES_PATH) if FEATURES_PATH.exists() else {}
    sources = build_watch_sources(features)

    override: dict = {}
    if args.last_checked:
        override["last_checked"] = args.last_checked
    if args.last_checked_label:
        override["last_checked_label"] = args.last_checked_label
    if args.has_new is not None:
        override["has_new"] = bool(args.has_new)
    if args.new_count is not None:
        override["new_count"] = int(args.new_count)
        if "has_new" not in override:
            override["has_new"] = args.new_count > 0
    if args.result:
        override["result"] = args.result

    # Always refresh last_checked from baselines when not explicitly set, so quiet scans still update the site clock.
    if "last_checked" not in override and features.get("last_checked"):
        override["last_checked"] = features["last_checked"]
        override["last_checked_label"] = features.get("last_checked_label") or format_shanghai_label(features["last_checked"])

    write_outputs(items, generated_at, sources, override or None)


if __name__ == "__main__":
    main()
