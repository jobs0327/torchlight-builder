import asyncio
import json
import re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
import aiofiles
import os
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
import config

console = Console()


class TorchlightScraper:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.data: Dict[str, List[Dict]] = {}
        self.errors: List[Dict] = []
        self.stats = {
            "pages_scraped": 0,
            "items_collected": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    def _get_category_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return path_parts[1]
        return "other"

    async def _wait_for_content(self, page, timeout=10000):
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=timeout)
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except:
            pass

    async def _extract_hero_data(self, page) -> Dict:
        return await page.evaluate("""
            () => {
                const data = {
                    name: '',
                    title: '',
                    god_type: '',
                    description: '',
                    traits: [],
                    skills: [],
                    talents: [],
                    stats: {},
                    url: window.location.href,
                };
                
                const h1 = document.querySelector('h1');
                if (h1) data.name = h1.textContent.trim();
                
                const titleEl = document.querySelector('.hero-title, .title, h2');
                if (titleEl) data.title = titleEl.textContent.trim();
                
                const descEl = document.querySelector('.description, .hero-desc, p');
                if (descEl) data.description = descEl.textContent.trim();
                
                document.querySelectorAll('.trait, .hero-trait').forEach(el => {
                    data.traits.push(el.textContent.trim());
                });
                
                document.querySelectorAll('.skill-item, .skill').forEach(el => {
                    const skill = {
                        name: el.querySelector('.skill-name, h3, h4')?.textContent.trim() || '',
                        description: el.querySelector('.skill-desc, p')?.textContent.trim() || '',
                    };
                    if (skill.name) data.skills.push(skill);
                });
                
                document.querySelectorAll('table').forEach(table => {
                    table.querySelectorAll('tr').forEach(tr => {
                        const cells = tr.querySelectorAll('td, th');
                        if (cells.length >= 2) {
                            const key = cells[0].textContent.trim();
                            const value = cells[1].textContent.trim();
                            if (key && value) {
                                data.stats[key] = value;
                            }
                        }
                    });
                });
                
                return data;
            }
        """)

    async def _extract_item_data(self, page) -> Dict:
        return await page.evaluate("""
            () => {
                const data = {
                    name: '',
                    type: '',
                    rarity: '',
                    description: '',
                    stats: {},
                    affixes: [],
                    drop_sources: [],
                    url: window.location.href,
                };
                
                const h1 = document.querySelector('h1');
                if (h1) data.name = h1.textContent.trim();
                
                const typeEl = document.querySelector('.item-type, .type');
                if (typeEl) data.type = typeEl.textContent.trim();
                
                const rarityEl = document.querySelector('.rarity, .item-rarity');
                if (rarityEl) data.rarity = rarityEl.textContent.trim();
                
                const descEl = document.querySelector('.description, .item-desc');
                if (descEl) data.description = descEl.textContent.trim();
                
                document.querySelectorAll('.affix, .item-affix').forEach(el => {
                    data.affixes.push(el.textContent.trim());
                });
                
                document.querySelectorAll('.drop-source, .source').forEach(el => {
                    data.drop_sources.push(el.textContent.trim());
                });
                
                document.querySelectorAll('table').forEach(table => {
                    table.querySelectorAll('tr').forEach(tr => {
                        const cells = tr.querySelectorAll('td, th');
                        if (cells.length >= 2) {
                            const key = cells[0].textContent.trim();
                            const value = cells[1].textContent.trim();
                            if (key && value) {
                                data.stats[key] = value;
                            }
                        }
                    });
                });
                
                return data;
            }
        """)

    async def _extract_skill_data(self, page) -> Dict:
        return await page.evaluate("""
            () => {
                const data = {
                    name: '',
                    type: '',
                    description: '',
                    tags: [],
                    level_data: [],
                    url: window.location.href,
                };
                
                const h1 = document.querySelector('h1');
                if (h1) data.name = h1.textContent.trim();
                
                const typeEl = document.querySelector('.skill-type, .type');
                if (typeEl) data.type = typeEl.textContent.trim();
                
                const descEl = document.querySelector('.description, .skill-desc');
                if (descEl) data.description = descEl.textContent.trim();
                
                document.querySelectorAll('.tag, .skill-tag').forEach(el => {
                    data.tags.push(el.textContent.trim());
                });
                
                document.querySelectorAll('table').forEach(table => {
                    const headers = [];
                    const rows = [];
                    table.querySelectorAll('th').forEach(th => {
                        headers.push(th.textContent.trim());
                    });
                    table.querySelectorAll('tr').forEach(tr => {
                        const cells = [];
                        tr.querySelectorAll('td').forEach(td => {
                            cells.push(td.textContent.trim());
                        });
                        if (cells.length > 0) rows.push(cells);
                    });
                    if (rows.length > 0) {
                        data.level_data.push({ headers, rows });
                    }
                });
                
                return data;
            }
        """)

    async def _extract_generic_data(self, page) -> Dict:
        return await page.evaluate("""
            () => {
                const data = {
                    title: document.title,
                    url: window.location.href,
                    headings: [],
                    content: '',
                    tables: [],
                    lists: [],
                    images: [],
                };
                
                document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
                    data.headings.push({
                        level: h.tagName,
                        text: h.textContent.trim(),
                    });
                });
                
                const mainContent = document.querySelector('main, .content, .main, article, #content');
                if (mainContent) {
                    data.content = mainContent.innerText;
                } else {
                    data.content = document.body.innerText;
                }
                
                document.querySelectorAll('table').forEach(table => {
                    const tableData = [];
                    table.querySelectorAll('tr').forEach(tr => {
                        const row = [];
                        tr.querySelectorAll('td, th').forEach(cell => {
                            row.push(cell.textContent.trim());
                        });
                        if (row.length > 0) tableData.push(row);
                    });
                    if (tableData.length > 0) data.tables.push(tableData);
                });
                
                document.querySelectorAll('ul, ol').forEach(list => {
                    const items = [];
                    list.querySelectorAll('li').forEach(li => {
                        items.push(li.textContent.trim());
                    });
                    if (items.length > 0) data.lists.push(items);
                });
                
                document.querySelectorAll('img').forEach(img => {
                    if (img.src && !img.src.includes('data:')) {
                        data.images.push({
                            src: img.src,
                            alt: img.alt || '',
                        });
                    }
                });
                
                return data;
            }
        """)

    async def _extract_page_data(self, page, url: str) -> Dict:
        category = self._get_category_from_url(url)
        
        if "hero" in category or "heroes" in url:
            return await self._extract_hero_data(page)
        elif "gear" in category or "item" in url:
            return await self._extract_item_data(page)
        elif "skill" in category:
            return await self._extract_skill_data(page)
        else:
            return await self._extract_generic_data(page)

    async def _get_all_links(self, page, base_url: str) -> List[str]:
        links = await page.evaluate("""
            () => {
                const links = new Set();
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.href;
                    if (href && !href.includes('#') && !href.includes('javascript:')) {
                        links.add(href);
                    }
                });
                return Array.from(links);
            }
        """)
        
        filtered_links = []
        for link in links:
            parsed = urlparse(link)
            base_parsed = urlparse(base_url)
            if parsed.netloc == base_parsed.netloc:
                filtered_links.append(link)
        
        return filtered_links

    async def scrape_page(self, page, url: str) -> Optional[Dict]:
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            console.print(f"[cyan]Scraping: {url}[/cyan]")
            
            await page.goto(url, wait_until="domcontentloaded", timeout=config.TIMEOUT)
            await self._wait_for_content(page)
            await asyncio.sleep(config.REQUEST_DELAY)
            
            data = await self._extract_page_data(page, url)
            
            self.stats["pages_scraped"] += 1
            self.stats["items_collected"] += 1
            
            return data
            
        except Exception as e:
            self.stats["errors"] += 1
            error_info = {
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.errors.append(error_info)
            console.print(f"[red]Error scraping {url}: {e}[/red]")
            return None

    async def scrape_category(self, browser, category: str, progress, task_id):
        context = await browser.new_context()
        page = await context.new_page()
        
        category_url = f"{config.BASE_URL}/{config.LANG}/{category}"
        category_data = []
        
        try:
            console.print(f"[bold blue]Starting category: {category}[/bold blue]")
            
            await page.goto(category_url, wait_until="domcontentloaded", timeout=config.TIMEOUT)
            await self._wait_for_content(page)
            await asyncio.sleep(config.REQUEST_DELAY)
            
            links = await self._get_all_links(page, category_url)
            
            category_links = [l for l in links if f"/{category}/" in l or l == category_url]
            category_links = list(set(category_links))
            
            console.print(f"  Found {len(category_links)} links in {category}")
            
            for i, link in enumerate(category_links):
                data = await self.scrape_page(page, link)
                if data:
                    category_data.append(data)
                
                progress.update(task_id, advance=1)
                
        except Exception as e:
            console.print(f"[red]Error in category {category}: {e}[/red]")
        finally:
            await context.close()
        
        return category_data

    async def run(self, categories: List[str] = None):
        categories = categories or config.DATA_CATEGORIES
        self.stats["start_time"] = datetime.now().isoformat()
        
        console.print("[bold green]Starting Torchlight Scraper...[/bold green]")
        console.print(f"Base URL: {config.BASE_URL}")
        console.print(f"Categories: {', '.join(categories)}")
        console.print("")
        
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                main_task = progress.add_task("[cyan]Overall Progress", total=len(categories) * 50)
                
                for category in categories:
                    category_data = await self.scrape_category(browser, category, progress, main_task)
                    self.data[category] = category_data
                    
                    await self._save_category_data(category, category_data)
            
            await browser.close()
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        await self._save_summary()
        
        self._print_summary()

    async def _save_category_data(self, category: str, data: List[Dict]):
        filename = f"{config.OUTPUT_DIR}/{category}.json"
        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        console.print(f"[green]Saved {len(data)} items to {filename}[/green]")

    async def _save_summary(self):
        summary = {
            "stats": self.stats,
            "errors": self.errors,
            "categories": {k: len(v) for k, v in self.data.items()},
        }
        
        async with aiofiles.open(f"{config.OUTPUT_DIR}/summary.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(summary, ensure_ascii=False, indent=2))

    def _print_summary(self):
        console.print("\n" + "=" * 50)
        console.print("[bold green]Scraping Complete![/bold green]")
        console.print("=" * 50)
        
        table = Table(title="Scraping Results")
        table.add_column("Category", style="cyan")
        table.add_column("Items", style="green")
        
        for category, items in self.data.items():
            table.add_row(category, str(len(items)))
        
        console.print(table)
        
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Pages Scraped: {self.stats['pages_scraped']}")
        console.print(f"  Items Collected: {self.stats['items_collected']}")
        console.print(f"  Errors: {self.stats['errors']}")
        console.print(f"  Start Time: {self.stats['start_time']}")
        console.print(f"  End Time: {self.stats['end_time']}")
        
        if self.errors:
            console.print(f"\n[yellow]Warning: {len(self.errors)} errors occurred during scraping[/yellow]")


async def main():
    scraper = TorchlightScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
