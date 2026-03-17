import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

async def scrape_talent_positions():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 访问勇者天赋树页面
        url = "https://tlidb.com/cn/God_of_Might"
        print(f"访问页面: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 等待页面完全加载
            await page.wait_for_timeout(10000)
            
            # 获取页面内容
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找所有可能的天赋节点
            nodes = soup.find_all(['div', 'span'], style=lambda x: x and ('left:' in x or 'top:' in x))
            print(f"找到 {len(nodes)} 个可能的天赋节点")
            
            # 提取节点信息
            talent_nodes = []
            for i, node in enumerate(nodes):
                # 获取节点位置
                style = node.get('style', '')
                left = None
                top = None
                
                # 提取left和top值
                if 'left:' in style:
                    left_match = style.split('left:')[1].split(';')[0].strip()
                    if left_match.endswith('px'):
                        left = int(left_match.replace('px', ''))
                
                if 'top:' in style:
                    top_match = style.split('top:')[1].split(';')[0].strip()
                    if top_match.endswith('px'):
                        top = int(top_match.replace('px', ''))
                
                # 获取节点类型
                node_class = node.get('class', [])
                node_type = 'unknown'
                if any('small' in cls.lower() for cls in node_class):
                    node_type = 'small'
                elif any('notable' in cls.lower() for cls in node_class):
                    node_type = 'notable'
                elif any('legendary' in cls.lower() for cls in node_class):
                    node_type = 'legendary'
                
                # 获取节点名称
                name = node.find(['div', 'span'], class_=lambda x: x and ('name' in x.lower() or 'title' in x.lower()))
                name_text = name.text.strip() if name else f"节点{i+1}"
                
                # 获取节点描述
                desc = node.find(['div', 'span'], class_=lambda x: x and ('desc' in x.lower() or 'description' in x.lower()))
                desc_text = desc.text.strip() if desc else ""
                
                if left is not None and top is not None:
                    talent_nodes.append({
                        'id': f'node_{i+1}',
                        'name': name_text,
                        'type': node_type,
                        'description': desc_text,
                        'position': {
                            'left': left,
                            'top': top
                        }
                    })
                    print(f"节点 {i+1}: {name_text} (类型: {node_type}, 位置: {left}, {top})")
            
            # 保存节点信息
            with open('talent_positions.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'profession': '勇者',
                    'nodes': talent_nodes,
                    'connections': []
                }, f, indent=2, ensure_ascii=False)
            
            print(f"成功提取 {len(talent_nodes)} 个天赋节点的位置信息")
            
        except Exception as e:
            print(f"错误: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_talent_positions())
