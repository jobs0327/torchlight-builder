import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
import os
import re

async def scrape_talent_icons():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 访问勇者天赋树页面
        url = "https://tlidb.com/cn/God_of_Might"
        print(f"访问页面: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # 获取页面内容
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 创建图标保存目录
            icon_dir = "talent_icons"
            os.makedirs(icon_dir, exist_ok=True)
            
            # 查找天赋节点
            nodes = soup.find_all(['div', 'span'], class_=lambda x: x and ('node' in x.lower() or 'talent' in x.lower()))
            print(f"找到 {len(nodes)} 个可能的天赋节点")
            
            # 提取图标
            icons = []
            for i, node in enumerate(nodes):
                # 查找图标元素
                img = node.find('img')
                if img and 'src' in img.attrs:
                    img_url = img['src']
                    # 确保是完整URL
                    if not img_url.startswith('http'):
                        img_url = f"https://tlidb.com{img_url}"
                    
                    # 提取节点类型
                    node_class = node.get('class', [])
                    node_type = 'unknown'
                    if 'small' in ' '.join(node_class):
                        node_type = 'small'
                    elif 'notable' in ' '.join(node_class):
                        node_type = 'notable'
                    elif 'legendary' in ' '.join(node_class):
                        node_type = 'legendary'
                    
                    # 下载图标
                    try:
                        response = requests.get(img_url, timeout=10)
                        if response.status_code == 200:
                            # 生成文件名
                            filename = f"{node_type}_{i}.png"
                            filepath = os.path.join(icon_dir, filename)
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            icons.append({
                                'type': node_type,
                                'url': img_url,
                                'file': filename
                            })
                            print(f"下载图标: {filename}")
                    except Exception as e:
                        print(f"下载图标失败: {e}")
            
            # 保存图标信息
            with open('talent_icons.json', 'w', encoding='utf-8') as f:
                import json
                json.dump(icons, f, indent=2, ensure_ascii=False)
            
            print(f"成功下载 {len(icons)} 个天赋图标")
            
        except Exception as e:
            print(f"错误: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_talent_icons())
