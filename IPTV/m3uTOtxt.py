import os
import requests
from collections import defaultdict

# GitHub文件URL
url = "https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/gat.m3u"

# 下载文件
response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"Failed to download file: {response.status_code}")

# 解析.m3u文件内容
lines = response.text.splitlines()
channels = defaultdict(list)
current_group = None

for line in lines:
    if line.startswith("#EXTINF"):
        # 提取频道名称和分组
        parts = line.split(",")
        if len(parts) > 1:
            channel_name = parts[1].strip()
            # 假设分组信息在#EXTINF行的某个属性中，例如group-title="分组名称"
            if 'group-title="' in line:
                current_group = line.split('group-title="')[1].split('"')[0]
            else:
                current_group = "未分类"
    elif line.startswith("http"):
        # 这是频道URL
        if current_group:
            channels[current_group].append((channel_name, line))

# 保存分类后的频道信息为.txt文件
output_path = os.path.join(os.path.dirname(__file__), "gat.txt")
with open(output_path, "w", encoding="utf-8") as f:
    for group, channel_list in channels.items():
        f.write(f"=== {group} ===\n")
        for name, url in channel_list:
            f.write(f"{name}: {url}\n")
        f.write("\n")

print(f"文件已保存到: {output_path}")
