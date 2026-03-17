import asyncio
import json
import re
import os
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress
import aiofiles
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
import config

console = Console()


class TorchlightFullScraper:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.all_data: Dict[str, List[Dict]] = {}
        self.api_data: Dict[str, Dict] = {}
        self.errors: List[Dict] = []
        self.stats = {
            "pages_scraped": 0,
            "items_collected": 0,
            "api_calls": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    async def capture_api_responses(self, page):
        async def handle_response(response):
            url = response.url
            if '.json' in url and 'tlidb.com' in url:
                try:
                    data = await response.json()
                    self.api_data[url] = data
                    self.stats["api_calls"] += 1
                    console.print(f"[green]API Captured: {url.split('?')[0]}[/green]")
                except:
                    pass
        page.on("response", handle_response)

    async def extract_page_content(self, page, url: str) -> Dict:
        return await page.evaluate("""
            () => {
                const data = {
                    url: window.location.href,
                    title: document.title,
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
                
                document.querySelectorAll('table').forEach((table, idx) => {
                    const tableData = {
                        headers: [],
                        rows: [],
                    };
                    
                    const headerRow = table.querySelector('thead tr, tr:first-child');
                    if (headerRow) {
                        headerRow.querySelectorAll('th, td').forEach(cell => {
                            tableData.headers.push(cell.textContent.trim());
                        });
                    }
                    
                    table.querySelectorAll('tbody tr, tr:not(:first-child)').forEach(tr => {
                        const row = [];
                        tr.querySelectorAll('td, th').forEach(cell => {
                            row.push(cell.textContent.trim());
                        });
                        if (row.length > 0) {
                            tableData.rows.push(row);
                        }
                    });
                    
                    if (tableData.rows.length > 0 || tableData.headers.length > 0) {
                        data.tables.push(tableData);
                    }
                });
                
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
                
                document.querySelectorAll('img').forEach(img => {
                    if (img.src && !img.src.includes('data:')) {
                        data.images.push({
                            src: img.src,
                            alt: img.alt || '',
                        });
                    }
                });
                
                document.querySelectorAll('meta').forEach(meta => {
                    const name = meta.getAttribute('name') || meta.getAttribute('property');
                    const content = meta.getAttribute('content');
                    if (name && content) {
                        data.meta[name] = content;
                    }
                });
                
                const h1 = document.querySelector('h1');
                if (h1) data.structured_data.title = h1.textContent.trim();
                
                const h2s = [];
                document.querySelectorAll('h2').forEach(h2 => {
                    h2s.push(h2.textContent.trim());
                });
                if (h2s.length > 0) data.structured_data.sections = h2s;
                
                const stats = {};
                document.querySelectorAll('.stat, .attribute, .property').forEach(el => {
                    const label = el.querySelector('.label, .name, .key');
                    const value = el.querySelector('.value, .amount, .val');
                    if (label && value) {
                        stats[label.textContent.trim()] = value.textContent.trim();
                    }
                });
                if (Object.keys(stats).length > 0) data.structured_data.stats = stats;
                
                return data;
            }
        """)

    def _get_category_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        parts = path.split('/')
        
        if len(parts) >= 2:
            return parts[1]
        return "other"

    async def scrape_page(self, page, url: str, depth: int = 0, max_depth: int = 2) -> Optional[Dict]:
        if url in self.visited_urls:
            return None
        
        parsed = urlparse(url)
        if parsed.netloc != urlparse(config.BASE_URL).netloc:
            return None
        
        if not parsed.path.startswith(f'/{config.LANG}/'):
            return None
        
        self.visited_urls.add(url)
        
        try:
            console.print(f"[cyan]Scraping (depth {depth}): {url}[/cyan]")
            
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            
            await asyncio.sleep(1)
            
            content = await self.extract_page_content(page, url)
            
            category = self._get_category_from_url(url)
            if category not in self.all_data:
                self.all_data[category] = []
            
            self.all_data[category].append(content)
            
            self.stats["pages_scraped"] += 1
            self.stats["items_collected"] += 1
            
            if depth < max_depth:
                new_links = []
                for link in content.get('links', []):
                    href = link['href']
                    if href not in self.visited_urls:
                        new_links.append(href)
                
                new_links = list(set(new_links))[:20]
                
                for new_url in new_links:
                    if new_url not in self.visited_urls:
                        await self.scrape_page(page, new_url, depth + 1, max_depth)
            
            return content
            
        except Exception as e:
            self.stats["errors"] += 1
            error_info = {
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.errors.append(error_info)
            console.print(f"[red]Error: {url} - {e}[/red]")
            return None

    async def scrape_category(self, browser, category: str) -> List[Dict]:
        context = await browser.new_context()
        page = await context.new_page()
        
        await self.capture_api_responses(page)
        
        category_url = f"{config.BASE_URL}/{config.LANG}/{category}"
        
        try:
            console.print(f"\n[bold blue]=== Scraping Category: {category} ===[/bold blue]")
            
            await self.scrape_page(page, category_url, depth=0, max_depth=1)
            
        except Exception as e:
            console.print(f"[red]Category error {category}: {e}[/red]")
        finally:
            await context.close()
        
        return self.all_data.get(category, [])

    async def run(self, categories: List[str] = None, max_depth: int = 1):
        categories = categories or config.DATA_CATEGORIES
        self.stats["start_time"] = datetime.now().isoformat()
        
        console.print("[bold green]Starting Torchlight Full Scraper...[/bold green]")
        console.print(f"Base URL: {config.BASE_URL}")
        console.print(f"Categories: {', '.join(categories)}")
        console.print(f"Max Depth: {max_depth}")
        console.print("")
        
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for category in categories:
                await self.scrape_category(browser, category)
                
                if category in self.all_data:
                    await self._save_category_data(category)
            
            await browser.close()
        
        await self._save_api_data()
        await self._save_summary()
        
        self.stats["end_time"] = datetime.now().isoformat()
        self._print_summary()

    async def _save_category_data(self, category: str):
        if category not in self.all_data:
            return
        
        data = self.all_data[category]
        filename = f"{config.OUTPUT_DIR}/{category}.json"
        
        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        
        console.print(f"[green]Saved {len(data)} items to {filename}[/green]")

    async def _save_api_data(self):
        if not self.api_data:
            return
        
        async with aiofiles.open(f"{config.OUTPUT_DIR}/api_responses.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(self.api_data, ensure_ascii=False, indent=2))
        
        console.print(f"[green]Saved {len(self.api_data)} API responses[/green]")

    async def _save_summary(self):
        summary = {
            "stats": self.stats,
            "categories": {k: len(v) for k, v in self.all_data.items()},
            "errors": self.errors,
            "visited_urls_count": len(self.visited_urls),
        }
        
        async with aiofiles.open(f"{config.OUTPUT_DIR}/summary.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(summary, ensure_ascii=False, indent=2))

    def _print_summary(self):
        console.print("\n" + "=" * 60)
        console.print("[bold green]Scraping Complete![/bold green]")
        console.print("=" * 60)
        
        from rich.table import Table
        table = Table(title="Scraped Data Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Pages", style="green")
        
        for category, items in sorted(self.all_data.items()):
            table.add_row(category, str(len(items)))
        
        console.print(table)
        
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Total Pages: {self.stats['pages_scraped']}")
        console.print(f"  Items Collected: {self.stats['items_collected']}")
        console.print(f"  API Calls Captured: {self.stats['api_calls']}")
        console.print(f"  Errors: {self.stats['errors']}")
        console.print(f"  Duration: {self.stats['start_time']} to {self.stats['end_time']}")
        
        console.print(f"\n[bold]Output Directory:[/bold] {config.OUTPUT_DIR}/")


async def main():
    scraper = TorchlightFullScraper()
    await scraper.run(max_depth=1)


if __name__ == "__main__":
    asyncio.run(main())
