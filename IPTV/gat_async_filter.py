import aiohttp
import asyncio
import os
import logging
from tqdm import tqdm
import requests  # 添加 requests 模組用於下載 M3U 檔案

# 設置日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("gat_channel_filter_async.log"), logging.StreamHandler()],
)

# 配置文件
CONFIG = {
    "m3u_url": "https://raw.githubusercontent.com/WaykeYu/IPTV1/refs/heads/main/GAT.m3u",
    "save_path": "./GAT.m3u",  # 本地保存路徑
    "request_timeout": 3,  # 請求超時時間（秒）
    "max_concurrent_requests": 50,  # 最大並行請求數
}

# 下載 M3U 檔案
def download_m3u_file(url, save_path):
    try:
        logging.info(f"開始下載 M3U 檔案: {url}")
        response = requests.get(url)
        response.raise_for_status()  # 檢查 HTTP 錯誤
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 確保目錄存在
        with open(save_path, "wb") as file:
            file.write(response.content)
        logging.info(f"檔案已成功下載並保存到 {save_path}")
    except requests.exceptions.RequestException as e:
        logging.error(f"無法下載檔案: {e}")
        raise

# 去除重複頻道並排序
def remove_duplicates_and_sort(input_file):
    logging.info("開始去除重複頻道並排序...")
    channels = {}
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF:"):  # 頻道資訊行
            channel_info = lines[i].strip()
            channel_url = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if channel_url not in channels:  # 使用 URL 作為唯一標識
                channels[channel_url] = channel_info
            i += 2
        else:
            i += 1

    # 根據頻道名稱排序
    sorted_channels = sorted(channels.items(), key=lambda x: x[1])

    # 寫回原檔案
    with open(input_file, "w", encoding="utf-8") as file:
        for url, info in sorted_channels:
            file.write(info + "\n")
            file.write(url + "\n")

    logging.info(f"已去除重複頻道並排序，結果保存到 {input_file}")

# 檢查頻道有效性（異步版本）
async def check_channel_validity(session, channel_info, channel_url):
    try:
        async with session.head(channel_url, timeout=aiohttp.ClientTimeout(total=CONFIG["request_timeout"])) as response:
            return channel_info, channel_url, response.status == 200
    except Exception as e:
        logging.debug(f"頻道檢查失敗: {channel_info} - {e}")
        return channel_info, channel_url, False

# 過濾無效頻道（異步版本）
async def filter_invalid_channels_async(input_file):
    logging.info("開始檢查頻道有效性...")
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    valid_lines = []
    semaphore = asyncio.Semaphore(CONFIG["max_concurrent_requests"])  # 限制並行請求數

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(0, len(lines), 2):
            if i + 1 >= len(lines):
                break
            channel_info = lines[i].strip()
            channel_url = lines[i + 1].strip()
            task = asyncio.create_task(
                check_channel_validity(session, channel_info, channel_url)
            )
            tasks.append(task)

        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="檢查頻道有效性"):
            channel_info, channel_url, is_valid = await future
            if is_valid:
                valid_lines.append(channel_info + "\n")
                valid_lines.append(channel_url + "\n")
                logging.info(f"有效頻道: {channel_info}")
            else:
                logging.warning(f"無效頻道: {channel_info}")

    # 寫回原檔案
    with open(input_file, "w", encoding="utf-8") as file:
        file.writelines(valid_lines)

    logging.info("無效頻道已移除，檔案已更新。")

# 主程式
async def main():
    try:
        # 1. 下載檔案
        download_m3u_file(CONFIG["m3u_url"], CONFIG["save_path"])

        # 2. 去除重複頻道並排序
        remove_duplicates_and_sort(CONFIG["save_path"])

        # 3. 檢查頻道有效性並移除無效頻道
        await filter_invalid_channels_async(CONFIG["save_path"])

        logging.info("所有操作已完成！")
    except Exception as e:
        logging.error(f"程式執行失敗: {e}")

if __name__ == "__main__":
    asyncio.run(main())
