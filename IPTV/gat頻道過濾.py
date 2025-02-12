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









# 函数：获取视频分辨率
def get_video_resolution(video_path, timeout=0.8):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return (width, height)

# 函数：处理每一行
def process_line(line, output_file, order_list, valid_count, invalid_count, total_lines):
    parts = line.strip().split(',')
    if '#genre#' in line:
        # 如果行包含 '#genre#'，直接写入新文件
        with threading.Lock():
            output_file.write(line)
            print(f"已写入genre行：{line.strip()}")
    elif len(parts) == 2:
        channel_name, channel_url = parts
        resolution = get_video_resolution(channel_url, timeout=8)
        if resolution and resolution[1] >= 720:  # 检查分辨率是否大于等于720p
            with threading.Lock():
                output_file.write(f"{channel_name}[{resolution[1]}p],{channel_url}\n")
                order_list.append((channel_name, resolution[1], channel_url))
                valid_count[0] += 1
                print(f"Channel '{channel_name}' accepted with resolution {resolution[1]}p at URL {channel_url}.")
        else:
            invalid_count[0] += 1
    with threading.Lock():
        print(f"有效: {valid_count[0]}, 无效: {invalid_count[0]}, 总数: {total_lines}, 进度: {(valid_count[0] + invalid_count[0]) / total_lines * 100:.2f}%")

# 函数：多线程工作
def worker(task_queue, output_file, order_list, valid_count, invalid_count, total_lines):
    while True:
        try:
            line = task_queue.get(timeout=1)
            process_line(line, output_file, order_list, valid_count, invalid_count, total_lines)
        except Queue.Empty:
            break
        finally:
            task_queue.task_done()

# 主函数
def main(source_file_path, output_file_path):
    order_list = []
    valid_count = [0]
    invalid_count = [0]
    task_queue = Queue()

    # 读取源文件
    with open(source_file_path, 'r', encoding='utf-8') as source_file:
        lines = source_file.readlines()

    with open(output_file_path + '.txt', 'w', encoding='utf-8') as output_file:
        # 创建线程池
        with ThreadPoolExecutor(max_workers=64) as executor:
            # 创建并启动工作线程
            for _ in range(64):
                executor.submit(worker, task_queue, output_file, order_list, valid_count, invalid_count, len(lines))

            # 将所有行放入队列
            for line in lines:
                task_queue.put(line)

            # 等待队列中的所有任务完成
            task_queue.join()

    print(f"任务完成，有效频道数：{valid_count[0]}, 无效频道数：{invalid_count[0]}, 总频道数：{len(lines)}")

if __name__ == "__main__":
    source_file_path = 'IPTV/GAT.m3u'  # 替换为你的源文件路径
    output_file_path = 'GAT'  # 替换为你的输出文件路径,不要后缀名
    main(source_file_path, output_file_path)

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



