import os
import requests
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 下载文件的URL
url = "https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/Adult.m3u"  # 使用raw URL

# 本地保存路径
local_path = "Adult.m3u"

# 下载文件
response = requests.get(url)
if response.status_code == 200:
    with open(local_path, 'wb') as file:
        file.write(response.content)
    print(f"文件已下载到: {local_path}")
else:
    print(f"无法下载文件，状态码: {response.status_code}")
    exit()

# 解析.m3u文件
def parse_m3u(file_path):
    channels = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        channel = {}
        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF:"):
                # 解析频道信息
                info = re.search(r'#EXTINF:-1,(.*)', line)
                if info:
                    channel['name'] = info.group(1)
            elif line.startswith("http"):
                # 解析频道URL
                channel['url'] = line
                channels.append(channel)
                channel = {}  # 重置频道信息
    return channels

# 分类频道
def classify_channels(channels, category_key='name'):
    categories = {}
    for channel in channels:
        # 默认按频道名称的第一个词分类
        if category_key == 'name':
            category = channel['name'].split(' ')[0]  # 假设分类是频道名称的第一个词
        else:
            category = '未分类'  # 默认分类
        if category not in categories:
            categories[category] = []
        categories[category].append(channel)
    return categories

# 合并频道为txt文件（每个频道一行）
def merge_channels(categories, output_path):
    with open(output_path, 'w', encoding='utf-8') as file:
        for category, channels in categories.items():
            file.write(f"# {category}\n")  # 写入分类标题
            for channel in channels:
                # 每个频道一行，格式：频道名称,频道URL
                file.write(f"{channel['name']},{channel['url']}\n")
            file.write("\n")  # 分类之间留空行

# 解析并分类
channels = parse_m3u(local_path)
categories = classify_channels(channels, category_key='name')  # 按名称分类

# 合并并保存为txt文件
output_path = os.path.join(os.path.dirname(local_path), "Adult.txt")
merge_channels(categories, output_path)
print(f"频道已分类并保存到: {output_path}")
