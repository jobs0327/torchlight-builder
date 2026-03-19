import asyncio
import json
import os
import re
from typing import Dict, List

from playwright.async_api import async_playwright
from rich.console import Console

"""
抓取英雄特性页面：
- 读取 data/Hero.json（英雄列表页），抽取每个英雄特性 slug
- 逐个抓取 https://tlidb.com/cn/<slug>
- 保存为 data/<slug>.json（结构与 The_Brave.json 一致：[{ url,title,html,content,links,images,... }])
"""

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
HERO_INDEX_FILE = os.path.join(DATA_DIR, "Hero.json")

console = Console()


def load_hero_slugs() -> List[str]:
    with open(HERO_INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("Hero.json 内容格式不符合预期（应为非空列表）")

    # 避免使用 page.links（包含导航/站内所有链接），直接从 html 抽取「英雄 /25」列表里的 href
    html = (data[0].get("html") or "").strip()
    # hero 卡片：<a href="Anger"><img ... class="size128" ...></a>...
    slugs = []
    for m in re.finditer(r'<a href="([^"]+)"><img[^>]+class="size128"[^>]*>', html):
        slug = (m.group(1) or "").strip()
        if not slug:
            continue
        # 排除锚点/带查询
        slug = slug.split("#", 1)[0].split("?", 1)[0].strip()
        if not slug:
            continue
        slugs.append(slug)

    # 去重 + 稳定顺序
    seen = set()
    out: List[str] = []
    for s in slugs:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


async def extract_page_content(page) -> Dict:
    # 复用 full_scraper 的提取结构（包含 images）
    return await page.evaluate(
        """
        () => {
            const data = {
                url: window.location.href,
                title: document.title,
                html: document.documentElement.outerHTML,
                content: '',
                tables: [],
                lists: [],
                links: [],
                images: [],
                meta: {},
                structured_data: {},
            };

            const mainSelectors = [
                'main', '.main-content', '.content', 'article',
                '#content', '#main', '.wiki-content', '.page-content',
                '[role="main"]', '.container'
            ];

            let mainContent = null;
            for (const selector of mainSelectors) {
                mainContent = document.querySelector(selector);
                if (mainContent) break;
            }

            if (mainContent) {
                data.content = mainContent.innerText;
            } else {
                data.content = document.body.innerText;
            }

            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href;
                const text = a.textContent.trim();
                if (href && text && !href.startsWith('javascript:')) {
                    data.links.push({ href, text });
                }
            });

            document.querySelectorAll('img').forEach(img => {
                const src = img.src || img.getAttribute('src');
                const alt = img.alt || img.getAttribute('alt') || '';
                if (src) data.images.push({ src, alt });
            });

            return data;
        }
        """
    )


async def scrape_one(page, slug: str) -> Dict:
    url = f"https://tlidb.com/cn/{slug}"
    console.print(f"[cyan]Scraping: {slug} -> {url}[/cyan]")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    return await extract_page_content(page)


async def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    slugs = load_hero_slugs()

    console.print(f"[bold green]准备抓取 {len(slugs)} 个英雄特性页面[/bold green]")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for slug in slugs:
            out_path = os.path.join(DATA_DIR, f"{slug}.json")
            if os.path.exists(out_path):
                continue
            try:
                content = await scrape_one(page, slug)
            except Exception as e:
                console.print(f"[red]抓取 {slug} 失败：{e}[/red]")
                continue
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([content], f, ensure_ascii=False, indent=2)
            console.print(f"[green]已保存 {slug} 到 {out_path}[/green]")

        await context.close()
        await browser.close()

    console.print("[bold green]英雄特性页面抓取完成[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())

