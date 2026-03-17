import asyncio
import json
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

async def scrape_talent_tree():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 访问勇者天赋树页面
        url = "https://tlidb.com/cn/God_of_Might"
        console.print(f"[blue]访问页面: {url}[/blue]")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            console.print(f"[yellow]页面加载警告: {e}[/yellow]")
        
        # 提取天赋树数据
        talent_data = await page.evaluate("""
            () => {
                const data = {
                    profession: '勇者',
                    nodes: [],
                    connections: []
                };
                
                // 尝试多种选择器查找天赋节点
                const selectors = [
                    '.profession-tree .node',
                    '.talent-tree .node',
                    '[class*="tree"] [class*="node"]',
                    '.node',
                    '[class*="talent"]'
                ];
                
                let nodes = [];
                for (const selector of selectors) {
                    try {
                        nodes = document.querySelectorAll(selector);
                        if (nodes.length > 0) {
                            console.log('找到节点，使用选择器:', selector, '数量:', nodes.length);
                            break;
                        }
                    } catch(e) {}
                }
                
                if (nodes.length === 0) {
                    // 如果没有找到节点，尝试获取页面HTML结构
                    const treeSection = document.querySelector('#ProfessionTree') || 
                                       document.querySelector('[id*="Profession"]') ||
                                       document.body;
                    return { 
                        error: '未找到天赋节点', 
                        html: treeSection ? treeSection.innerHTML.substring(0, 3000) : '无HTML',
                        selectors: selectors
                    };
                }
                
                nodes.forEach((node, index) => {
                    try {
                        const rect = node.getBoundingClientRect();
                        
                        // 获取节点信息
                        const nameEl = node.querySelector('[class*="name"], .name, h3, h4, span, title');
                        const name = nameEl ? nameEl.textContent.trim() : node.getAttribute('title') || '';
                        
                        const descEl = node.querySelector('[class*="desc"], .description, p');
                        const description = descEl ? descEl.textContent.trim() : '';
                        
                        // 判断节点类型
                        let type = 'small';
                        const className = node.className || '';
                        if (typeof className === 'string') {
                            if (className.includes('legendary') || className.includes('large')) {
                                type = 'legendary';
                            } else if (className.includes('notable') || className.includes('medium')) {
                                type = 'notable';
                            }
                        }
                        
                        // 获取半径或大小
                        const r = node.getAttribute('r') || node.style.width || '20';
                        
                        data.nodes.push({
                            id: `node_${index}`,
                            name: name,
                            type: type,
                            description: description,
                            x: Math.round(rect.left),
                            y: Math.round(rect.top),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            radius: r
                        });
                    } catch(e) {
                        console.log('处理节点时出错:', e);
                    }
                });
                
                return data;
            }
        """)
        
        await browser.close()
        
        if 'error' in talent_data:
            console.print(f"[red]错误: {talent_data['error']}[/red]")
            console.print(f"[yellow]HTML片段: {talent_data.get('html', '无')[:500]}[/yellow]")
            return None
            
        console.print(f"[green]成功提取 {len(talent_data['nodes'])} 个天赋节点[/green]")
        
        # 打印节点信息
        for node in talent_data['nodes'][:10]:
            console.print(f"  - {node['name']}: ({node['x']}, {node['y']}) {node['type']}")
        
        # 保存数据
        with open('/Users/huangqian/Desktop/project/torchlight/talent_positions.json', 'w', encoding='utf-8') as f:
            json.dump(talent_data, f, ensure_ascii=False, indent=2)
        
        console.print("[green]数据已保存到 talent_positions.json[/green]")
        
        return talent_data

if __name__ == "__main__":
    asyncio.run(scrape_talent_tree())
