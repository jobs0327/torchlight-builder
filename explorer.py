import asyncio
import json
import re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress
import config

console = Console()


class SiteExplorer:
    def __init__(self):
        self.visited_urls = set()
        self.all_links = set()
        self.api_requests = []
        self.page_data = {}

    async def capture_api_requests(self, page):
        async def handle_request(request):
            url = request.url
            if any(ext in url.lower() for ext in [".json", "/api/", "/data/"]):
                self.api_requests.append({
                    "url": url,
                    "method": request.method,
                    "resource_type": request.resource_type,
                })
                console.print(f"[cyan]API Request: {url}[/cyan]")
        page.on("request", handle_request)

    async def extract_page_links(self, page):
        links = await page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    links.push({
                        href: a.href,
                        text: a.textContent.trim(),
                    });
                });
                return links;
            }
        """)
        return links

    async def extract_page_content(self, page):
        content = await page.evaluate("""
            () => {
                const result = {
                    title: document.title,
                    url: window.location.href,
                    headings: [],
                    tables: [],
                    lists: [],
                    text_content: '',
                };
                
                document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
                    result.headings.push({
                        level: h.tagName,
                        text: h.textContent.trim(),
                    });
                });
                
                document.querySelectorAll('table').forEach((table, idx) => {
                    const rows = [];
                    table.querySelectorAll('tr').forEach(tr => {
                        const cells = [];
                        tr.querySelectorAll('td, th').forEach(cell => {
                            cells.push(cell.textContent.trim());
                        });
                        if (cells.length > 0) rows.push(cells);
                    });
                    if (rows.length > 0) result.tables.push(rows);
                });
                
                document.querySelectorAll('ul, ol').forEach(list => {
                    const items = [];
                    list.querySelectorAll('li').forEach(li => {
                        items.push(li.textContent.trim());
                    });
                    if (items.length > 0) result.lists.push(items);
                });
                
                const mainContent = document.querySelector('main, .content, .main, #content, #main');
                if (mainContent) {
                    result.text_content = mainContent.innerText;
                } else {
                    result.text_content = document.body.innerText;
                }
                
                return result;
            }
        """)
        return content

    async def explore_page(self, page, url, depth=0, max_depth=2):
        if url in self.visited_urls:
            return
        if depth > max_depth:
            return
        
        parsed = urlparse(url)
        if parsed.netloc != urlparse(config.BASE_URL).netloc:
            return
        
        self.visited_urls.add(url)
        console.print(f"[green]Exploring: {url} (depth: {depth})[/green]")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=config.TIMEOUT)
            await asyncio.sleep(config.REQUEST_DELAY)
            
            content = await self.extract_page_content(page)
            self.page_data[url] = content
            
            links = await self.extract_page_links(page)
            
            for link in links:
                href = link["href"]
                if href and href.startswith(config.BASE_URL):
                    self.all_links.add(href)
                    
                    if href not in self.visited_urls and depth < max_depth:
                        await self.explore_page(page, href, depth + 1, max_depth)
                        
        except Exception as e:
            console.print(f"[red]Error exploring {url}: {e}[/red]")

    async def run(self, start_url=None, max_depth=2):
        start_url = start_url or config.START_URL
        
        console.print("[bold blue]Starting site exploration...[/bold blue]")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await self.capture_api_requests(page)
            
            await self.explore_page(page, start_url, depth=0, max_depth=max_depth)
            
            await browser.close()
        
        return {
            "visited_urls": list(self.visited_urls),
            "all_links": list(self.all_links),
            "api_requests": self.api_requests,
            "page_data": self.page_data,
        }


async def main():
    explorer = SiteExplorer()
    result = await explorer.run(max_depth=1)
    
    console.print(f"\n[bold]Exploration Results:[/bold]")
    console.print(f"  Visited URLs: {len(result['visited_urls'])}")
    console.print(f"  Total Links Found: {len(result['all_links'])}")
    console.print(f"  API Requests Captured: {len(result['api_requests'])}")
    
    if result['api_requests']:
        console.print("\n[bold yellow]API Requests Found:[/bold yellow]")
        for req in result['api_requests']:
            console.print(f"  - {req['method']} {req['url']}")
    
    import aiofiles
    import os
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    async with aiofiles.open(f"{config.OUTPUT_DIR}/site_structure.json", "w", encoding="utf-8") as f:
        await f.write(json.dumps(result, ensure_ascii=False, indent=2))
    
    console.print(f"\n[green]Results saved to {config.OUTPUT_DIR}/site_structure.json[/green]")


if __name__ == "__main__":
    asyncio.run(main())
