# src/notion_push.py
import os
from typing import Dict, List
from notion_client import Client
from .config import NOTION_TOKEN, NOTION_DB_ID

def push_to_notion(entry: Dict) -> str:
    """
    entry 结构：
    {
      "title": str,
      "category": str,
      "content": str,
      "date": "YYYY-MM-DD"
    }
    """
    assert NOTION_TOKEN and NOTION_DB_ID, "缺少 NOTION_TOKEN / NOTION_DB_ID"
    client = Client(auth=NOTION_TOKEN)

    # 获取数据库结构，自动适配属性类型
    db = client.databases.retrieve(NOTION_DB_ID)

    def get_prop_type(prop_name: str):
        return db.get('properties', {}).get(prop_name, {}).get('type')

    props = {}

    # 名称属性，必须存在且为title类型
    if '名称' in db.get('properties', {}) and get_prop_type('名称') == 'title':
        props['名称'] = {"title": [{"text": {"content": entry.get("title", "(无标题)")}}]}

    # 分类属性，存在且类型为select时使用，否则跳过
    if '分类' in db.get('properties', {}) and get_prop_type('分类') == 'select':
        props['分类'] = {"select": {"name": entry.get("category", "")}}

    # 日期属性，存在且类型为date时使用，否则跳过
    if '日期' in db.get('properties', {}) and get_prop_type('日期') == 'date':
        props['日期'] = {"date": {"start": entry.get("date", "")}}

    # 文本或内容属性，优先文本，若无则内容
    content_prop_name = None
    content_prop_type = None
    if '文本' in db.get('properties', {}):
        content_prop_name = '文本'
        content_prop_type = get_prop_type('文本')
    elif '内容' in db.get('properties', {}):
        content_prop_name = '内容'
        content_prop_type = get_prop_type('内容')

    if content_prop_name:
        if content_prop_type == 'rich_text':
            props[content_prop_name] = {"rich_text": [{"text": {"content": entry.get("content", "")}}]}
        elif content_prop_type == 'url':
            # url类型直接传字符串，如果为空传空字符串
            props[content_prop_name] = {"url": entry.get("content", "") or None}
        else:
            # 其他类型默认rich_text，放到文本属性中
            props['文本'] = {"rich_text": [{"text": {"content": entry.get("content", "")}}]}
    else:
        # 如果都不存在，则默认加一个文本属性名为"文本"
        props['文本'] = {"rich_text": [{"text": {"content": entry.get("content", "")}}]}

    page = client.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties=props
    )
    return page["id"]