import asyncio
import json
import os
from typing import Dict, List

from playwright.async_api import async_playwright
from rich.console import Console

"""
通用职业页面抓取脚本：
- 从 data/Talent.json 中读取所有职业/大天赋链接
- 只抓取本地 profession_index.json 中出现的面板 slug 对应的页面
- 每个页面单独保存为 data/<Slug>.json，结构与 The_Brave.json 一致
"""

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
TALENT_PAGE_FILE = os.path.join(DATA_DIR, "Talent.json")
PROFESSION_INDEX_FILE = os.path.join(DATA_DIR, "profession_index.json")

console = Console()


def load_talent_links() -> Dict[str, str]:
    """从 Talent.json 中构建 slug -> url 映射。"""
    path = TALENT_PAGE_FILE
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("Talent.json 内容格式不符合预期（应为非空列表）")

    links = data[0].get("links", []) or []
    slug_to_url: Dict[str, str] = {}
    for link in links:
        href = (link.get("href") or "").strip()
        if not href.startswith("https://tlidb.com/cn/"):
            continue
        slug = href.split("/")[-1]
        slug_to_url[slug] = href
    return slug_to_url


def load_profession_index() -> List[Dict]:
    path = PROFESSION_INDEX_FILE
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def extract_page_content(page) -> Dict:
    """复用 full_scraper 中的 extract_page_content 逻辑，稍作裁剪。"""
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

            document.querySelectorAll('ul, ol').forEach(list => {
                const items = [];
                list.querySelectorAll('li').forEach(li => {
                    items.push(li.textContent.trim());
                });
                if (items.length > 0) {
                    data.lists.push(items);
                }
            });

            document.querySelectorAll('a[href]').forEach(a => {
                const href = a.href;
                const text = a.textContent.trim();
                if (href && text && !href.startsWith('javascript:')) {
                    data.links.push({ href, text });
                }
            });

            return data;
        }
        """
    )


async def scrape_one(page, slug: str, url: str) -> Dict:
    console.print(f"[cyan]Scraping: {slug} -> {url}[/cyan]")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    return await extract_page_content(page)


async def main() -> None:
    slug_to_url = load_talent_links()
    professions = load_profession_index()

    # 只抓取 profession_index 中 type=panel 的 slug，对应大天赋面板
    target_entries = [p for p in professions if p.get("type") == "panel"]

    console.print(
        f"[bold green]准备抓取 {len(target_entries)} 个职业/面板页面（通用方案）[/bold green]"
    )

    os.makedirs(DATA_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for entry in target_entries:
            slug = entry["slug"]
            name = entry["name"]
            url = slug_to_url.get(slug)
            if not url:
                console.print(
                    f"[yellow]跳过 {name}（{slug}）：在 Talent.json.links 中找不到对应链接[/yellow]"
                )
                continue

            try:
                content = await scrape_one(page, slug, url)
            except Exception as e:
                console.print(f"[red]抓取 {name}（{slug}）失败：{e}[/red]")
                continue

            out_path = os.path.join(DATA_DIR, f"{slug}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([content], f, ensure_ascii=False, indent=2)

            console.print(f"[green]已保存 {name}（{slug}）到 {out_path}[/green]")

        await context.close()
        await browser.close()

    console.print("[bold green]职业/面板页面抓取完成[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())

