import os
import requests
import re

# 下載文件的URL
url = "https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/Adult.m3u"  # 使用raw URL

# 本地保存路径
local_path = "Adult.m3u"

# 下載文件
def download_file(url, local_path):
    """下載並保存 .m3u 文件到本地"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # 确保响应成功
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"文件已下載到: {local_path}")
    except requests.exceptions.RequestException as e:
        print(f"下載文件失敗: {e}")
        exit()

# 解析 .m3u 文件
def parse_m3u(file_path):
    """解析 .m3u 文件並提取頻道名稱和URL"""
    channels = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        channel = {}
        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF:"):
                # 解析頻道信息
                info = re.search(r'#EXTINF:-1,(.*)', line)
                if info:
                    channel['name'] = info.group(1)
            elif line.startswith("http"):
                # 解析頻道URL
                channel['url'] = line
                # 防止重複添加頻道
                if 'name' in channel and 'url' in channel:
                    channels.append(channel)
                    channel = {}  # 重置頻道信息
    return channels

# 按頻道名稱分類
def classify_channels(channels, category_key='name'):
    """根據頻道名稱的首個詞分類頻道"""
    categories = {}
    for channel in channels:
        # 按照頻道名稱的第一个词分类
        if category_key == 'name':
            category = channel['name'].split(' ')[0]  # 假设分类是频道名称的第一个词
        else:
            category = '未分類'  # 默認分類為未分類
        if category not in categories:
            categories[category] = []
        categories[category].append(channel)
    return categories

# 儲存分類後的頻道資訊
def save_channels_by_category(categories):
    """將分類後的頻道保存為不同的文件"""
    for category, channels in categories.items():
        filename = f"{category}.txt"
        with open(filename, 'w', encoding='utf-8') as file:
            for channel in channels:
                file.write(f"{channel['name']} - {channel['url']}\n")
        print(f"{filename} 已儲存，共 {len(channels)} 頻道")

# 主程式
def main():
    # 下載 .m3u 文件
    if not os.path.exists(local_path):
        download_file(url, local_path)
    
    # 解析 .m3u 文件
    channels = parse_m3u(local_path)
    print(f"共解析到 {len(channels)} 個頻道")

    # 按照名稱分類頻道
    categories = classify_channels(channels)

    # 儲存每個分類的頻道資訊
    save_channels_by_category(categories)

# 執行主程式
if __name__ == "__main__":
    main()
