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


class TorchlightSPAScraper:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.all_data: Dict[str, List[Dict]] = {}
        self.all_links: Set[str] = set()
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
                    clean_url = url.split('?')[0]
                    self.api_data[clean_url] = data
                    self.stats["api_calls"] += 1
                    console.print(f"[green]API: {clean_url}[/green]")
                except:
                    pass
        page.on("response", handle_response)

    async def wait_for_content(self, page, min_content_length=100, max_wait=15000):
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) * 1000 < max_wait:
            content_length = await page.evaluate("""
                () => {
                    const body = document.body;
                    return body ? body.innerText.length : 0;
                }
            """)
            
            if content_length > min_content_length:
                return True
            
            await asyncio.sleep(0.5)
        
        return False

    async def extract_all_links(self, page) -> List[str]:
        return await page.evaluate("""
            () => {
                const links = new Set();
                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.href;
                    if (href && !href.startsWith('javascript:') && !href.includes('#')) {
                        links.add(href);
                    }
                });
                return Array.from(links);
            }
        """)

    async def extract_page_content(self, page, url: str) -> Dict:
        return await page.evaluate("""
            () => {
                const data = {
                    url: window.location.href,
                    title: document.title,
                    html: '',
                    content: '',
                    tables: [],
                    lists: [],
                    links: [],
                    images: [],
                    meta: {},
                    structured_data: {},
                };
                
                data.html = document.body.innerHTML;
                data.content = document.body.innerText;
                
                document.querySelectorAll('table').forEach((table) => {
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

    def _is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        
        if parsed.netloc != urlparse(config.BASE_URL).netloc:
            return False
        
        if not parsed.path.startswith(f'/{config.LANG}/'):
            return False
        
        skip_patterns = [
            '/i18n/',
            '.json',
            '/api/',
        ]
        
        for pattern in skip_patterns:
            if pattern in url:
                return False
        
        return True

    async def scrape_page(self, page, url: str) -> Optional[Dict]:
        if url in self.visited_urls:
            return None
        
        if not self._is_valid_url(url):
            return None
        
        self.visited_urls.add(url)
        
        try:
            console.print(f"[cyan]Scraping: {url}[/cyan]")
            
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            await self.wait_for_content(page, min_content_length=50, max_wait=20000)
            
            await asyncio.sleep(2)
            
            links = await self.extract_all_links(page)
            for link in links:
                if self._is_valid_url(link):
                    self.all_links.add(link)
            
            content = await self.extract_page_content(page, url)
            
            category = self._get_category_from_url(url)
            if category not in self.all_data:
                self.all_data[category] = []
            
            self.all_data[category].append(content)
            
            self.stats["pages_scraped"] += 1
            self.stats["items_collected"] += 1
            
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

    async def run(self, start_url: str = None, max_pages: int = 100):
        start_url = start_url or config.START_URL
        self.stats["start_time"] = datetime.now().isoformat()
        
        console.print("[bold green]Starting Torchlight SPA Scraper...[/bold green]")
        console.print(f"Base URL: {config.BASE_URL}")
        console.print(f"Start URL: {start_url}")
        console.print(f"Max Pages: {max_pages}")
        console.print("")
        
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await self.capture_api_responses(page)
            
            await self.scrape_page(page, start_url)
            
            console.print(f"\n[yellow]Found {len(self.all_links)} links to explore...[/yellow]")
            
            pages_scraped = 1
            for link in list(self.all_links):
                if pages_scraped >= max_pages:
                    console.print(f"[yellow]Reached max pages limit: {max_pages}[/yellow]")
                    break
                
                if link not in self.visited_urls:
                    await self.scrape_page(page, link)
                    pages_scraped += 1
                    
                    if pages_scraped % 10 == 0:
                        await self._save_progress()
            
            await context.close()
            await browser.close()
        
        await self._save_all_data()
        
        self.stats["end_time"] = datetime.now().isoformat()
        self._print_summary()

    async def _save_progress(self):
        console.print(f"[dim]Saving progress... ({self.stats['pages_scraped']} pages)[/dim]")
        await self._save_all_data()

    async def _save_all_data(self):
        console.print("[bold blue]Saving all data...[/bold blue]")
        
        for category, items in self.all_data.items():
            if items:
                filename = f"{config.OUTPUT_DIR}/{category}.json"
                async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(items, ensure_ascii=False, indent=2))
                console.print(f"[green]Saved {category}.json ({len(items)} items)[/green]")
        
        if self.api_data:
            async with aiofiles.open(f"{config.OUTPUT_DIR}/api_responses.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(self.api_data, ensure_ascii=False, indent=2))
            console.print(f"[green]Saved api_responses.json ({len(self.api_data)} endpoints)[/green]")
        
        async with aiofiles.open(f"{config.OUTPUT_DIR}/all_links.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(list(self.all_links), ensure_ascii=False, indent=2))
        
        summary = {
            "stats": self.stats,
            "categories": {k: len(v) for k, v in self.all_data.items()},
            "errors": self.errors,
            "visited_urls_count": len(self.visited_urls),
            "total_links_found": len(self.all_links),
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
        console.print(f"  Total Links Found: {len(self.all_links)}")
        console.print(f"  Errors: {self.stats['errors']}")
        console.print(f"  Duration: {self.stats['start_time']} to {self.stats['end_time']}")
        
        console.print(f"\n[bold]Output Directory:[/bold] {config.OUTPUT_DIR}/")


async def main():
    scraper = TorchlightSPAScraper()
    await scraper.run(max_pages=50)


if __name__ == "__main__":
    asyncio.run(main())
