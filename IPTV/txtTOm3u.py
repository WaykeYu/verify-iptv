import requests
import os
import shutil
import subprocess
import logging
from datetime import datetime
from time import sleep

# === 設定 ===
SOURCES = {
    "TW_allsource.m3u": "https://raw.githubusercontent.com/WaykeYu/MyTV_tw/refs/heads/main/TW_allsource",
    "UBTV.m3u": "https://raw.githubusercontent.com/WaykeYu/MyTV_tw/refs/heads/main/UBTV",
    "TV7708.m3u": "https://raw.githubusercontent.com/ji3g4ao3sm3/tv/refs/heads/main/7708.txt",
    "TW_only.m3u": "https://raw.githubusercontent.com/WaykeYu/MyTV_tw/refs/heads/main/Source/TW_only.txt",
    "listx.m3u": "https://github.com/gaotianliuyun/gao/raw/master/listx.txt",
    "PEHy.m3u": "https://qu.ax/PEHy.txt",
    "XstR.m3u": "https://qu.ax/XstR.txt",
    "w36yqk.m3u": "https://files.catbox.moe/w36yqk.txt",
    "18+.m3u": "https://d.kstore.space/download/5447/18/18禁.txt",
    "2o0yqn.m3u": "https://files.catbox.moe/2o0yqn.txt",
    "408z13.m3u": "https://files.catbox.moe/408zl3.txt",
    "最好的18+.m3u": "https://cyuan.netlify.app/tvbox/lives/18+/18%F0%9F%88%B2%EF%B8%8F.txt",
    "国区老传媒.m3u": "https://raw.githubusercontent.com/qirenzhidao/tvbox18/main/json/adult_2.txt",
    "me.m3u": "https://github.com/xfcjp/xfcjp.github.io/raw/master/me.txt"
}

GITHUB_REPO_DIR = "/home/runner/work/verify-iptv/verify-iptv"
SOURCE_DIR = os.path.join(GITHUB_REPO_DIR, "source")
README_FILE = os.path.join(SOURCE_DIR, "README.md")

# === 日誌設定 ===
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger(__name__)

# === 工具函式 ===
def download_and_convert_to_m3u(url: str, filename: str, retries: int = 3) -> bool:
    """下載來源並轉換成 M3U 格式"""
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"正在下載 {url} (嘗試 {attempt}/{retries}) ...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # 寫入 M3U
            with open(filename, "w", encoding="utf-8") as file:
                file.write("#EXTM3U\n")
                for line in response.text.splitlines():
                    parts = line.strip().split(",")
                    if len(parts) == 2:
                        name, stream_url = parts
                        file.write(f"#EXTINF:-1,{name}\n{stream_url}\n")

            logger.info(f"{filename} 下載並轉換完成。")
            return True

        except requests.RequestException as e:
            logger.warning(f"{filename} 下載失敗: {e}")
            sleep(2)
    logger.error(f"{filename} 下載多次仍失敗，跳過。")
    return False


def move_to_source_dir(filename: str) -> None:
    """移動檔案到 source 目錄"""
    os.makedirs(SOURCE_DIR, exist_ok=True)
    dst_path = os.path.join(SOURCE_DIR, filename)
    shutil.move(filename, dst_path)
    logger.info(f"{filename} 已移動到 {SOURCE_DIR}")


def update_readme() -> None:
    """更新 README.md"""
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(README_FILE, "w", encoding="utf-8") as file:
        file.write("# 源文件更新記錄\n\n")
        file.write(f"最後更新時間: `{update_time}`\n\n")
        file.write("## 文件列表\n")
        for fname in SOURCES.keys():
            file.write(f"- `{fname}`\n")
    logger.info("README.md 已更新。")


def git_commit_and_push() -> None:
    """提交並推送到 GitHub"""
    logger.info("準備提交並推送變更...")
    os.chdir(GITHUB_REPO_DIR)

    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=False)
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=False)

    subprocess.run(["git", "add", "source"], check=True)

    # 檢查是否有變更
    diff_result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if diff_result.returncode == 0:
        logger.info("無變更，略過提交。")
        return

    subprocess.run(["git", "commit", "-m", "自動更新源文件及 README"], check=True)
    subprocess.run(["git", "push"], check=True)
    logger.info("推送完成。")


def main() -> None:
    success_count = 0
    for filename, url in SOURCES.items():
        if download_and_convert_to_m3u(url, filename):
            move_to_source_dir(filename)
            success_count += 1

    if success_count == 0:
        logger.error("所有來源皆下載失敗，結束任務。")
        return

    update_readme()
    git_commit_and_push()
    logger.info("任務全部完成 ✅")


if __name__ == "__main__":
    main()
