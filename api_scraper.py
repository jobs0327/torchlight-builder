import asyncio
import json
import re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
import aiofiles
import aiohttp
import os
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
import config

console = Console()


class TorchlightAPIScraper:
    def __init__(self):
        self.i18n_data: Dict = {}
        self.autocomplete_data: Dict = {}
        self.all_items: Dict[str, List[Dict]] = {}
        self.stats = {
            "api_calls": 0,
            "items_collected": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    async def fetch_json(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        try:
            console.print(f"[cyan]Fetching: {url}[/cyan]")
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    data = await response.json()
                    self.stats["api_calls"] += 1
                    return data
                else:
                    console.print(f"[red]HTTP {response.status} for {url}[/red]")
                    return None
        except Exception as e:
            console.print(f"[red]Error fetching {url}: {e}[/red]")
            self.stats["errors"] += 1
            return None

    async def fetch_i18n_data(self, session: aiohttp.ClientSession):
        console.print("[bold blue]Fetching i18n data...[/bold blue]")
        
        i18n_url = f"{config.BASE_URL}/i18n/{config.LANG}.json"
        autocomplete_url = f"{config.BASE_URL}/i18n/autocomplete_{config.LANG}.json"
        
        self.i18n_data = await self.fetch_json(session, i18n_url) or {}
        self.autocomplete_data = await self.fetch_json(session, autocomplete_url) or {}
        
        console.print(f"  i18n keys: {len(self.i18n_data)}")
        console.print(f"  autocomplete keys: {len(self.autocomplete_data)}")

    async def discover_page_structure(self, session: aiohttp.ClientSession) -> Dict[str, List[str]]:
        console.print("[bold blue]Discovering page structure...[/bold blue]")
        
        structure = {}
        
        if self.i18n_data:
            for key, value in self.i18n_data.items():
                if isinstance(value, str) and '/' in key:
                    parts = key.split('/')
                    if len(parts) >= 2:
                        category = parts[0]
                        if category not in structure:
                            structure[category] = []
                        if len(parts) >= 3:
                            item_id = parts[1] if len(parts) > 2 else None
                            if item_id and item_id not in structure[category]:
                                structure[category].append(item_id)
        
        for category, items in structure.items():
            console.print(f"  {category}: {len(items)} items")
        
        return structure

    async def scrape_with_browser(self):
        console.print("[bold blue]Using browser to discover content structure...[/bold blue]")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            api_data = {}
            
            async def handle_response(response):
                url = response.url
                if '.json' in url and 'tlidb.com' in url:
                    try:
                        data = await response.json()
                        api_data[url] = data
                        console.print(f"[green]Captured API: {url}[/green]")
                    except:
                        pass
            
            page.on("response", handle_response)
            
            try:
                console.print("Loading main page...")
                await page.goto(config.START_URL, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)
                
                console.print("Exploring heroes section...")
                await page.goto(f"{config.BASE_URL}/{config.LANG}/heroes", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)
                
                console.print("Exploring gear section...")
                await page.goto(f"{config.BASE_URL}/{config.LANG}/gear", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)
                
                console.print("Exploring skills section...")
                await page.goto(f"{config.BASE_URL}/{config.LANG}/skills", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)
                
            except Exception as e:
                console.print(f"[yellow]Browser navigation warning: {e}[/yellow]")
            
            await browser.close()
            
            return api_data

    async def extract_items_from_i18n(self) -> Dict[str, List[Dict]]:
        console.print("[bold blue]Extracting items from i18n data...[/bold blue]")
        
        items = {}
        
        if not self.i18n_data:
            return items
        
        categories = {
            'heroes': [],
            'gear': [],
            'skills': [],
            'talents': [],
            'items': [],
            'monsters': [],
            'quests': [],
            'seasons': [],
        }
        
        current_item = None
        current_category = None
        
        for key, value in sorted(self.i18n_data.items()):
            parts = key.split('/')
            
            if len(parts) >= 2:
                category = parts[0]
                item_id = parts[1] if len(parts) > 1 else None
                field = parts[2] if len(parts) > 2 else None
                
                if category not in categories:
                    categories[category] = []
                
                if item_id:
                    existing = next((i for i in categories[category] if i.get('id') == item_id), None)
                    
                    if not existing:
                        existing = {'id': item_id}
                        categories[category].append(existing)
                    
                    if field:
                        existing[field] = value
                    elif len(parts) == 2:
                        existing['name'] = value
        
        for category, cat_items in categories.items():
            if cat_items:
                items[category] = cat_items
                console.print(f"  {category}: {len(cat_items)} items")
        
        return items

    async def run(self):
        self.stats["start_time"] = datetime.now().isoformat()
        
        console.print("[bold green]Starting Torchlight API Scraper...[/bold green]")
        console.print(f"Base URL: {config.BASE_URL}")
        console.print("")
        
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            await self.fetch_i18n_data(session)
            
            self.all_items = await self.extract_items_from_i18n()
            
            browser_data = await self.scrape_with_browser()
            
            for url, data in browser_data.items():
                filename = url.split('/')[-1].replace('.json', '').replace('?', '_')
                filepath = f"{config.OUTPUT_DIR}/api_{filename}.json"
                async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(data, ensure_ascii=False, indent=2))
                console.print(f"[green]Saved: {filepath}[/green]")
        
        await self._save_all_data()
        
        self.stats["end_time"] = datetime.now().isoformat()
        self._print_summary()

    async def _save_all_data(self):
        console.print("[bold blue]Saving all data...[/bold blue]")
        
        async with aiofiles.open(f"{config.OUTPUT_DIR}/i18n_full.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(self.i18n_data, ensure_ascii=False, indent=2))
        console.print(f"[green]Saved i18n_full.json ({len(self.i18n_data)} keys)[/green]")
        
        async with aiofiles.open(f"{config.OUTPUT_DIR}/autocomplete.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(self.autocomplete_data, ensure_ascii=False, indent=2))
        console.print(f"[green]Saved autocomplete.json[/green]")
        
        for category, items in self.all_items.items():
            if items:
                filename = f"{config.OUTPUT_DIR}/{category}.json"
                async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(items, ensure_ascii=False, indent=2))
                console.print(f"[green]Saved {category}.json ({len(items)} items)[/green]")
        
        summary = {
            "stats": self.stats,
            "categories": {k: len(v) for k, v in self.all_items.items()},
            "i18n_keys": len(self.i18n_data),
        }
        async with aiofiles.open(f"{config.OUTPUT_DIR}/summary.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(summary, ensure_ascii=False, indent=2))

    def _print_summary(self):
        console.print("\n" + "=" * 50)
        console.print("[bold green]Scraping Complete![/bold green]")
        console.print("=" * 50)
        
        table = Table(title="Extracted Data")
        table.add_column("Category", style="cyan")
        table.add_column("Items", style="green")
        
        for category, items in self.all_items.items():
            table.add_row(category, str(len(items)))
        
        console.print(table)
        
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  API Calls: {self.stats['api_calls']}")
        console.print(f"  i18n Keys: {len(self.i18n_data)}")
        console.print(f"  Errors: {self.stats['errors']}")
        console.print(f"  Duration: {self.stats['start_time']} to {self.stats['end_time']}")
        
        console.print(f"\n[bold]Output Files:[/bold]")
        console.print(f"  Directory: {config.OUTPUT_DIR}/")


async def main():
    scraper = TorchlightAPIScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
