import requests
from tqdm import tqdm
import cv2
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import time


#  获取远程港澳台直播源文件
# 下載檔案的 URL
import os
url = "https://raw.githubusercontent.com/WaykeYu/IPTV1/refs/heads/main/GAT.m3u"

# 本地保存的路徑
save_path = "https://github.com/WaykeYu/verify-iptv/tree/main/IPTV/GAT.m3u"

# 確保目錄存在
os.makedirs(os.path.dirname(save_path), exist_ok=True)

# 下載檔案
response = requests.get(url)

# 檢查請求是否成功
if response.status_code == 200:
    # 將內容寫入檔案
    with open(save_path, 'wb') as file:
        file.write(response.content)
    print(f"檔案已成功下載並保存到 {save_path}")
else:
    print(f"無法下載檔案，HTTP 狀態碼: {response.status_code}")

#去除重覆頻道並排序
# 讀取 M3U 檔案
input_file = "GAT.m3u"
output_file = "GAT.m3u"

# 用於存儲頻道資訊的字典（避免重複）
channels = {}

# 讀取檔案內容
with open(input_file, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 解析 M3U 檔案
i = 0
while i < len(lines):
    if lines[i].startswith("#EXTINF:"):  # 頻道資訊行
        channel_info = lines[i].strip()
        channel_url = lines[i + 1].strip() if i + 1 < len(lines) else ""
        
        # 使用 URL 作為唯一標識（避免重複）
        if channel_url not in channels:
            channels[channel_url] = channel_info
        i += 2
    else:
        i += 1

# 將頻道資訊轉換為列表並排序
sorted_channels = sorted(channels.items(), key=lambda x: x[1])  # 根據頻道名稱排序

# 寫回檔案
with open(output_file, 'w', encoding='utf-8') as file:
    for url, info in sorted_channels:
        file.write(info + "\n")
        file.write(url + "\n")

print(f"已去除重複頻道並排序，結果保存到 {output_file}")

#確認GAT.m3u內容所有頻道的有效性,並去除無效頻道後覆蓋原檔案
import requests
import os

# 下載檔案的 URL
url = "https://raw.githubusercontent.com/WaykeYu/IPTV1/refs/heads/main/GAT.m3u"

# 本地保存的路徑
save_path = "GAT.m3u"

# 下載檔案
response = requests.get(url)

# 檢查請求是否成功
if response.status_code != 200:
    print(f"無法下載檔案，HTTP 狀態碼: {response.status_code}")
    exit()

# 將內容寫入臨時檔案
with open(save_path, 'wb') as file:
    file.write(response.content)

print(f"檔案已成功下載並保存到 {save_path}")

# 讀取 M3U 檔案內容
with open(save_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 過濾無效頻道
valid_lines = []
for i in range(0, len(lines), 2):  # M3U 檔案格式：每兩行一組（頻道資訊 + URL）
    if i + 1 >= len(lines):
        break

    channel_info = lines[i].strip()
    channel_url = lines[i + 1].strip()

    # 檢查 URL 是否有效
    try:
        response = requests.get(channel_url, timeout=5)  # 設置超時時間為 5 秒
        if response.status_code == 200:
            valid_lines.append(channel_info + "\n")
            valid_lines.append(channel_url + "\n")
            print(f"有效頻道: {channel_info}")
        else:
            print(f"無效頻道 (HTTP {response.status_code}): {channel_info}")
    except requests.exceptions.RequestException as e:
        print(f"無效頻道 (請求失敗): {channel_info} - {e}")

# 將有效頻道寫回原檔案
with open(save_path, 'w', encoding='utf-8') as file:
    file.writelines(valid_lines)

print("無效頻道已移除，檔案已更新。")



