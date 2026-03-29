#!/usr/bin/env python3
"""
逐页请求 tlidb 技能详情（当前赛季首张卡片），解析「标签 + 数值」行，写入
activeSkillTags.json / supportSkillTags.json 中每条技能的 statRows 字段；
并写入 wikiCardNarrative（卡片内简介/详情等叙述纯文本，供前端悬停展示）。

主动技能：damageMultiplierByLevel 长度 20（1–20 级）；法术等带「点」基础伤害时另有
skillBaseDamageByLevel（同长度，如 8-14、每秒 3 点等展示串）。纯武器倍率技能不写后者。
辅助技能：supportDamageBonusByLevel 长度 40（1–40 级）。
专属崇高/华贵辅助：优先解析「成长 /3」两列表格，得到 T0–T2 三档增伤展示串，写入
supportDamageBonusByTier（长度 3，下标 0/1/2 对应 wiki 的 Tier 0/1/2）。
若无 /3 表，再尝试从卡片取固定「被辅助技能额外 +N%」并复制为 40 档 supportDamageBonusByLevel。

用法（仓库根目录）:
  python sync_skill_page_stats.py
  python sync_skill_page_stats.py --active-only
  python sync_skill_page_stats.py --id Leap_Attack
  python sync_skill_page_stats.py --limit 20   # 每个列表只抓前 20 条（试跑）
  python sync_skill_page_stats.py --exclusive-support-only   # 仅崇高/华贵两个 JSON
"""
from __future__ import annotations

import argparse
import json
import re
import time
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ACTIVE_FILE = Path("torchlight-builder/src/data/skills/activeSkillTags.json")
SUPPORT_FILE = Path("torchlight-builder/src/data/skills/supportSkillTags.json")
NOBLE_SUPPORT_FILE = Path("torchlight-builder/src/data/skills/nobleSupportSkillTags.json")
MAGNIFICENT_SUPPORT_FILE = Path(
    "torchlight-builder/src/data/skills/magnificentSupportSkillTags.json"
)
BASE_URL = "https://tlidb.com/cn/{}"
REQUEST_DELAY_S = 0.22
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def fetch_html(skill_id: str) -> str | None:
    url = BASE_URL.format(skill_id)
    req = Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://tlidb.com/"})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=45) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except (HTTPError, URLError, TimeoutError, OSError):
            time.sleep(0.8 * (attempt + 1))
    return None


def extract_current_popup_card_html(html: str) -> str:
    """取当前赛季卡片 HTML（排除带 previousItem 的旧赛季卡）。"""
    needle = 'class="card ui_item popupItem"'
    pos = 0
    while True:
        i = html.find(needle, pos)
        if i < 0:
            return ""
        gt = html.find(">", i)
        if gt < 0:
            return ""
        open_tag = html[i : gt + 1]
        if "previousItem" in open_tag:
            pos = i + 1
            continue
        start = i
        j = html.find('<div class="card ui_item', i + len(needle))
        if j < 0:
            return html[start:]
        return html[start:j]


def extract_wiki_card_narrative_plain(card_html: str) -> str:
    """
    从当前赛季 popup 卡片取出「简介 / 详情」等叙述正文（去掉表格与已单独解析的 stat 行），
    供前端悬停卡片展示，替代跳转 tlidb。
    """
    if not card_html or not card_html.strip():
        return ""
    t = card_html.strip()
    # extract_current_popup_card_html 有时从属性片段起剪，去掉残缺开标签
    if t.startswith("class=") or t.startswith('class="'):
        gt = t.find(">")
        if gt >= 0:
            t = t[gt + 1 :]
    t = t.lstrip()
    t = re.sub(r"<table[^>]*DataTable[^>]*>[\s\S]*?</table>", " ", t, flags=re.I)
    t = re.sub(
        r'<div class="d-flex justify-content-center">\s*<div>[^<]*</div>\s*'
        r'<div class="ps-2">[^<]*</div>\s*</div>',
        " ",
        t,
        flags=re.I | re.S,
    )
    plain = unescape(t)
    plain = re.sub(r"<br\s*/?>", "\n", plain, flags=re.I)
    plain = re.sub(r"</p\s*>", "\n", plain, flags=re.I)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = plain.replace("&nbsp;", " ").replace("&#160;", " ")
    plain = re.sub(r"[\t\xa0]+", " ", plain)
    plain = re.sub(r" *\n *", "\n", plain)
    plain = re.sub(r" {2,}", " ", plain)
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    return plain.strip()


def extract_stat_rows(card_html: str) -> list[dict[str, str]]:
    pat = re.compile(
        r'<div class="d-flex justify-content-center">\s*'
        r"<div>([^<]+)</div>\s*"
        r'<div class="ps-2">([^<]*)</div>\s*</div>',
        re.S,
    )
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw_label, raw_value in pat.findall(card_html):
        label = unescape(raw_label).strip()
        value = unescape(raw_value).strip()
        if label.endswith("：") or label.endswith(":"):
            label = label[:-1].strip()
        if not label or not value:
            continue
        key = (label, value)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"label": label, "value": value})
    return rows


def _td_plain_text(fragment: str) -> str:
    t = unescape(fragment)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _normalize_pct_display(s: str) -> str:
    t = s.strip()
    if not t:
        return ""
    if t.startswith("+"):
        t = t[1:].strip()
    return t if t.endswith("%") else (t + "%" if re.fullmatch(r"[\d.]+", t) else t)


def _skill_base_damage_from_damage_column(raw_td: str) -> str:
    """
    成长表第三列（damage）：提取技能基础伤害数值展示（如 8-14、3、3-3），
    排除「造成 …% 武器攻击伤害」等纯武器倍率行。
    """
    if not raw_td or not raw_td.strip():
        return ""
    plain = _td_plain_text(raw_td)
    if not plain:
        return ""
    # 纯武器百分比，无法术/点数的 flat 段
    if "武器" in plain and "%" in plain:
        return ""
    m = re.search(r'text-mod[^>]*>([^<]+)</span>\s*点', raw_td, re.S)
    if m:
        s = m.group(1).strip()
        if s and "%" not in s:
            return re.sub(r"\s+", "", s)
    # 「造成 8-14 法术火焰伤害」：数字与「伤害」之间不能出现 %
    m2 = re.search(
        r"造成\s*([\d.]+\s*-\s*[\d.]+|[\d.]+)\s+[^%]*伤害",
        plain,
    )
    if m2:
        return re.sub(r"\s+", "", m2.group(1).strip())
    # 如「造成每秒 3 持续腐蚀伤害」（无「点」字）
    m_per_s = re.search(
        r"造成每秒\s*([\d.]+\s*-\s*[\d.]+|[\d.]+)\s+[^%]*伤害",
        plain,
    )
    if m_per_s:
        return re.sub(r"\s+", "", m_per_s.group(1).strip())
    pats = [
        r"造成每秒\s*([\d.]+\s*-\s*[\d.]+|[\d.]+)\s*点",
        r"每秒\s*([\d.]+\s*-\s*[\d.]+|[\d.]+)\s*点",
        r"造成\s*([\d.]+\s*-\s*[\d.]+|[\d.]+)\s*点(?:法术|物理|闪电|火焰|冰冷|腐蚀|混沌|持续)?伤害",
    ]
    for pat in pats:
        m3 = re.search(pat, plain)
        if m3:
            return re.sub(r"\s+", "", m3.group(1).strip())
    return ""


def extract_active_level_curves(
    html: str,
) -> tuple[list[str] | None, list[str] | None]:
    """
    主动 1–20 级：伤害倍率 + 可选的第三列基础点伤。
    返回 (damageMultiplierByLevel, skillBaseDamageByLevel)；后者若全无则 None。
    """
    anchor = html.find("成长 /40")
    if anchor < 0:
        anchor = html.find("成长/40")
    if anchor < 0:
        anchor = html.find("成长")
    window = html[anchor:] if anchor >= 0 else html
    tm = re.search(r"<table[^>]*DataTable[^>]*>", window)
    if not tm:
        return None, None
    start = tm.start()
    rest = window[start:]
    end = rest.find("</table>")
    if end < 0:
        return None, None
    table_html = rest[:end]
    tr_pat = re.compile(r"<tr>.*?</tr>", re.S | re.I)
    td_pat = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
    mult: dict[int, str] = {}
    base: dict[int, str] = {}
    for tr in tr_pat.findall(table_html):
        tds = td_pat.findall(tr)
        if len(tds) < 2:
            continue
        lv_s = _td_plain_text(tds[0])
        if not lv_s.isdigit():
            continue
        lv = int(lv_s)
        if not 1 <= lv <= 20:
            continue
        col2 = _td_plain_text(tds[1])
        val = ""
        if col2 and "%" in col2:
            val = _normalize_pct_display(col2)
        elif len(tds) >= 4:
            desc = tds[3]
            m = re.search(
                r"造成\s*<span[^>]*text-mod[^>]*>([^<]+)</span>\s*武器",
                desc,
                re.S,
            )
            if m:
                val = _normalize_pct_display(m.group(1))
            if not val:
                plain = _td_plain_text(desc)
                m2 = re.search(r"造成\s*([\d.]+%)\s*武器", plain)
                if m2:
                    val = m2.group(1)
        if not val and len(tds) >= 3:
            col3_plain = _td_plain_text(tds[2])
            if "造成" in col3_plain:
                m3 = re.search(r"造成\s*([\d.]+%)", col3_plain)
                if m3:
                    val = m3.group(1)
        if not val:
            return None, None
        mult[lv] = val
        base[lv] = _skill_base_damage_from_damage_column(tds[2]) if len(tds) >= 3 else ""
    if len(mult) != 20:
        return None, None
    mult_list = [mult[i] for i in range(1, 21)]
    base_list = [base.get(i, "") for i in range(1, 21)]
    base_out = (
        base_list if any(x.strip() for x in base_list) else None
    )
    return mult_list, base_out


def _normalize_support_bonus_cell(raw: str) -> str:
    s = _td_plain_text(raw)
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b != 0:
            x = a / b
            if abs(x - round(x)) < 1e-9:
                return str(int(round(x)))
            t = f"{x:.4f}".rstrip("0").rstrip(".")
            return t
    return s


def _pick_support_growth_value_column(header_plain: list[str]) -> int:
    """
    成长表为多列时：第一列一般为 level，第二列（下标 1）为「被辅助技能」主效果数值列
    （与旧版两列「level / 值」语义一致；tlidb 多列表常在第 2 列给「额外伤害」等）。
    """
    if len(header_plain) <= 1:
        return 1
    return 1


def extract_support_damage_bonus_by_level(html: str) -> list[str] | None:
    """辅助技能 1–40 级：成长区 DataTable，支持 2 列（level/值）或多列表头。"""
    anchor = html.find("成长 /40")
    if anchor < 0:
        anchor = html.find("成长/40")
    if anchor < 0:
        anchor = html.find("成长")
    window = html[anchor:] if anchor >= 0 else html
    tm = re.search(r"<table[^>]*DataTable[^>]*>", window)
    if not tm:
        return None
    start = tm.start()
    rest = window[start:]
    end = rest.find("</table>")
    if end < 0:
        return None
    table_html = rest[:end]
    tr_pat = re.compile(r"<tr>.*?</tr>", re.S | re.I)
    td_pat = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
    th_pat = re.compile(r"<th[^>]*>(.*?)</th>", re.S | re.I)
    trs = tr_pat.findall(table_html)
    if not trs:
        return None

    value_col = 1
    data_trs = trs
    first_tr = trs[0]
    ths = th_pat.findall(first_tr)
    if ths:
        header_plain = [_td_plain_text(h) for h in ths]
        if len(header_plain) > 2:
            value_col = _pick_support_growth_value_column(header_plain)
        data_trs = trs[1:]

    pairs: dict[int, str] = {}
    for tr in data_trs:
        tds = td_pat.findall(tr)
        if len(tds) < 2:
            continue
        lv_s = _td_plain_text(tds[0])
        if not lv_s.isdigit():
            continue
        lv = int(lv_s)
        if not 1 <= lv <= 40:
            continue
        if len(tds) == 2:
            cell_idx = 1
        else:
            cell_idx = value_col if value_col < len(tds) else 1
        val = _normalize_support_bonus_cell(tds[cell_idx])
        if not val:
            continue
        pairs[lv] = val
    if len(pairs) != 40:
        return None
    return [pairs[i] for i in range(1, 41)]


def _tier_row_damage_display(raw_td: str) -> str:
    """成长 /3 第二列：取「… +(...)… % 伤害」中紧挨 % 前的 text-mod 展示串。"""
    pct = r"(?:%|％|&#37;)"
    matches = re.findall(
        rf'<span[^>]*class="[^"]*text-mod[^"]*"[^>]*>([^<]+)</span>'
        rf'(?:\s|&nbsp;)*{pct}(?:\s|&nbsp;)*(?:伤害)?',
        raw_td,
        re.S | re.I,
    )
    for candidate in reversed(matches):
        inner = unescape(candidate.strip())
        inner = (
            inner.replace("&ndash;", "-")
            .replace("&#8211;", "-")
            .replace("&mdash;", "-")
            .replace("–", "-")
            .replace("—", "-")
        )
        inner = re.sub(r"\s+", "", inner)
        if not inner:
            continue
        # 常见 +(a-b)%；部分技能为负向修正 (-10--8)% 等
        if re.search(r"\d", inner):
            return inner
    # 无「%」紧贴时：取最后一个含数字的 text-mod（部分页面结构不同）
    for m in reversed(
        list(re.finditer(r'class="[^"]*text-mod[^"]*"[^>]*>([^<]+)</span>', raw_td, re.I))
    ):
        inner = unescape(m.group(1).strip())
        inner = (
            inner.replace("&ndash;", "-")
            .replace("&#8211;", "-")
            .replace("&mdash;", "-")
            .replace("–", "-")
            .replace("—", "-")
        )
        inner = re.sub(r"\s+", "", inner)
        if re.search(r"\d", inner):
            plain = _td_plain_text(raw_td)
            if "%" in plain or "伤害" in plain:
                return inner
    return ""


def extract_support_damage_bonus_by_tier(html: str) -> list[str] | None:
    """
    专属辅助「成长 /3」：两列 Tier(0–2) / 描述，解析三档增伤（与 T0/T1/T2 对齐）。
    返回 [tier0, tier1, tier2] 展示串，不含百分号后缀（由前端按需补 %）。
    """
    m = re.search(r"成长\s*/\s*3", html)
    if not m:
        return None
    window = html[m.start() : m.start() + 16000]
    tm = re.search(r"<table[^>]*DataTable[^>]*>", window)
    if not tm:
        return None
    rest = window[tm.start() :]
    end = rest.find("</table>")
    if end < 0:
        return None
    table_html = rest[:end]
    tr_pat = re.compile(r"<tr>.*?</tr>", re.S | re.I)
    td_pat = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
    by_tier: dict[int, str] = {}
    for tr in tr_pat.findall(table_html):
        tds = td_pat.findall(tr)
        if len(tds) != 2:
            continue
        tier_s = _td_plain_text(tds[0])
        if not tier_s.isdigit():
            continue
        tier = int(tier_s)
        if tier not in (0, 1, 2):
            continue
        val = _tier_row_damage_display(tds[1])
        if not val:
            return None
        by_tier[tier] = val
    if len(by_tier) != 3:
        return None
    return [by_tier[i] for i in range(3)]


def extract_support_flat_bonus_percent_from_card(card_html: str) -> str | None:
    """
    专属辅助等：无标准 1–40 成长表时，从当前赛季卡片描述中取固定「额外伤害」百分比。
    匹配：被辅助技能额外 <span class="text-mod">+20</span>% 伤害
    """
    patterns = [
        r"被辅助技能额外\s*"
        r'<span[^>]*class="[^"]*text-mod[^"]*"[^>]*>\s*\+?\s*'
        r"([0-9]+(?:\.[0-9]+)?)\s*</span>\s*%",
        r"被辅助技能[\s\S]{0,200}?"
        r'<span[^>]*class="[^"]*text-mod[^"]*"[^>]*>\s*\+?\s*'
        r"([0-9]+(?:\.[0-9]+)?)\s*</span>\s*%",
        r"额外\s*"
        r'<span[^>]*text-mod[^>]*>\s*\+?\s*([0-9]+(?:\.[0-9]+)?)\s*</span>\s*%\s*'
        r"伤害",
    ]
    for pat in patterns:
        m = re.search(pat, card_html, re.S | re.I)
        if m:
            return m.group(1).strip()
    plain = re.sub(r"<[^>]+>", " ", unescape(card_html))
    plain = re.sub(r"\s+", " ", plain)
    m2 = re.search(
        r"被辅助技能[^\d]{0,80}额外\s*\+?\s*([0-9]+(?:\.[0-9]+)?)\s*%",
        plain,
    )
    if m2:
        return m2.group(1).strip()
    return None


def stat_rows_for_skill(skill_id: str) -> list[dict[str, str]] | None:
    html = fetch_html(skill_id)
    if html is None:
        return None
    card = extract_current_popup_card_html(html)
    if not card:
        return []
    return extract_stat_rows(card)


def active_skill_extended_stats(
    skill_id: str,
) -> tuple[
    list[dict[str, str]] | None, list[str] | None, list[str] | None, str
]:
    """statRows、damageMultiplierByLevel（20）、skillBaseDamageByLevel（20，可选）、wiki 卡片叙述。"""
    html = fetch_html(skill_id)
    if html is None:
        return None, None, None, ""
    card = extract_current_popup_card_html(html)
    stat_rows = extract_stat_rows(card) if card else []
    narrative = extract_wiki_card_narrative_plain(card) if card else ""
    mult_list, base_list = extract_active_level_curves(html)
    return stat_rows, mult_list, base_list, narrative


def _is_wiki_exclusive_support_id(skill_id: str) -> bool:
    """slug 含 (Noble)/(Magnificent)，禁止误用页面内其它「成长/40」表。"""
    s = skill_id.strip().lower()
    if "%28noble%29" in s or "%28magnificent%29" in s:
        return True
    return "(noble)" in s or "(magnificent)" in s


def support_skill_extended_stats(
    skill_id: str,
) -> tuple[
    list[dict[str, str]] | None, list[str] | None, list[str] | None, str
]:
    """
    statRows；
    supportDamageBonusByLevel（40 项）与普通辅助；
    supportDamageBonusByTier（3 项）与专属辅助 T0–T2，二者最多填其一；
    wiki 卡片叙述纯文本。
    """
    html = fetch_html(skill_id)
    if html is None:
        return None, None, None, ""
    card = extract_current_popup_card_html(html)
    stat_rows = extract_stat_rows(card) if card else []
    narrative = extract_wiki_card_narrative_plain(card) if card else ""
    bonus_by_level: list[str] | None = None
    bonus_by_tier: list[str] | None = None

    if _is_wiki_exclusive_support_id(skill_id):
        bonus_by_tier = extract_support_damage_bonus_by_tier(html)
        if bonus_by_tier is None and card:
            flat_pct = extract_support_flat_bonus_percent_from_card(card)
            if flat_pct:
                bonus_by_tier = [flat_pct, flat_pct, flat_pct]
    else:
        bonus_by_level = extract_support_damage_bonus_by_level(html)
        if bonus_by_level is None:
            bonus_by_tier = extract_support_damage_bonus_by_tier(html)
        if bonus_by_level is None and bonus_by_tier is None and card:
            flat_pct = extract_support_flat_bonus_percent_from_card(card)
            if flat_pct:
                bonus_by_level = [flat_pct] * 40
    return stat_rows, bonus_by_level, bonus_by_tier, narrative


def process_file(
    path: Path,
    list_key: str,
    only_id: str | None,
    dry_run: bool,
    limit: int,
) -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    skills: list[dict] = data.get(list_key) or []
    ok = fail = 0
    processed = 0
    for skill in skills:
        sid = str(skill.get("id", "")).strip()
        if not sid:
            continue
        if only_id and sid != only_id:
            continue
        if limit > 0 and processed >= limit:
            break
        processed += 1
        print(f"  [{list_key}] {sid}", flush=True)
        time.sleep(REQUEST_DELAY_S)
        if list_key == "activeSkills":
            rows, damage_by_level, base_by_level, narrative = active_skill_extended_stats(sid)
            if rows is None:
                fail += 1
                continue
            skill["statRows"] = rows
            if narrative:
                skill["wikiCardNarrative"] = narrative
            else:
                skill.pop("wikiCardNarrative", None)
            if damage_by_level is not None:
                skill["damageMultiplierByLevel"] = damage_by_level
                print(f"    damageMultiplierByLevel: 20 levels OK", flush=True)
            else:
                skill.pop("damageMultiplierByLevel", None)
                print(
                    f"    damageMultiplierByLevel: (未解析到 20 行，已移除字段)",
                    flush=True,
                )
            if base_by_level is not None:
                skill["skillBaseDamageByLevel"] = base_by_level
                print(f"    skillBaseDamageByLevel: 20 levels OK", flush=True)
            else:
                skill.pop("skillBaseDamageByLevel", None)
                print(
                    f"    skillBaseDamageByLevel: (无点伤列，已移除字段)",
                    flush=True,
                )
        else:
            rows, bonus_by_level, bonus_by_tier, narrative = support_skill_extended_stats(sid)
            if rows is None:
                fail += 1
                continue
            skill["statRows"] = rows
            if narrative:
                skill["wikiCardNarrative"] = narrative
            else:
                skill.pop("wikiCardNarrative", None)
            if bonus_by_tier is not None:
                skill["supportDamageBonusByTier"] = bonus_by_tier
                skill.pop("supportDamageBonusByLevel", None)
                print(f"    supportDamageBonusByTier: T0–T2 OK", flush=True)
            elif bonus_by_level is not None:
                skill["supportDamageBonusByLevel"] = bonus_by_level
                skill.pop("supportDamageBonusByTier", None)
                print(f"    supportDamageBonusByLevel: 40 levels OK", flush=True)
            else:
                skill.pop("supportDamageBonusByLevel", None)
                skill.pop("supportDamageBonusByTier", None)
                print(
                    f"    supportDamageBonus: (无 40 级表亦无 T0–T2，已移除字段)",
                    flush=True,
                )
        ok += 1
        if not dry_run:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    if dry_run:
        print("(dry-run 未写入文件)", flush=True)
    return ok, fail


def main() -> int:
    parser = argparse.ArgumentParser(description="从 tlidb 详情页同步技能数值行到 JSON")
    parser.add_argument("--active-only", action="store_true")
    parser.add_argument("--support-only", action="store_true")
    parser.add_argument(
        "--exclusive-support-only",
        action="store_true",
        help="仅同步 nobleSupportSkillTags.json / magnificentSupportSkillTags.json，跳过主动与普通辅助",
    )
    parser.add_argument("--id", help="仅处理指定技能 id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="每个 JSON 列表最多抓取条数（0 不限制），便于试跑",
    )
    args = parser.parse_args()

    only_id: str | None = args.id.strip() if args.id else None
    exclusive_only = args.exclusive_support_only

    if args.active_only and args.support_only:
        print("不能同时指定 --active-only 与 --support-only")
        return 2
    if exclusive_only and args.active_only:
        print("不能同时指定 --active-only 与 --exclusive-support-only")
        return 2

    if exclusive_only:
        do_active = False
        do_regular_support = False
        do_exclusive_support = True
    else:
        do_active = not args.support_only
        do_regular_support = not args.active_only
        do_exclusive_support = not args.active_only

    print(f"statRows 同步: delay={REQUEST_DELAY_S}s, dry_run={args.dry_run}", flush=True)
    total_ok = total_fail = 0

    if do_active and ACTIVE_FILE.is_file():
        print(f"处理主动: {ACTIVE_FILE}", flush=True)
        o, f = process_file(
            ACTIVE_FILE, "activeSkills", only_id, args.dry_run, args.limit
        )
        total_ok += o
        total_fail += f

    if do_regular_support and SUPPORT_FILE.is_file():
        print(f"处理辅助: {SUPPORT_FILE}", flush=True)
        o, f = process_file(
            SUPPORT_FILE, "supportSkills", only_id, args.dry_run, args.limit
        )
        total_ok += o
        total_fail += f

    for label, path in (
        ("崇高专属辅助", NOBLE_SUPPORT_FILE),
        ("华贵专属辅助", MAGNIFICENT_SUPPORT_FILE),
    ):
        if do_exclusive_support and path.is_file():
            print(f"处理{label}: {path}", flush=True)
            o, f = process_file(path, "supportSkills", only_id, args.dry_run, args.limit)
            total_ok += o
            total_fail += f

    print(
        f"完成: 成功写入 {total_ok} 条，请求失败保留旧数据 {total_fail} 条",
        flush=True,
    )
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
