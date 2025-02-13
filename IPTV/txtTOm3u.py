import requests
import os
import subprocess
import logging
from datetime import datetime

# 設定變數
TW_URL = "https://raw.githubusercontent.com/WaykeYu/MyTV_tw/refs/heads/main/TW_allsource"
UBTV_URL = "https://raw.githubusercontent.com/WaykeYu/MyTV_tw/refs/heads/main/UBTV"
TW_FILENAME = "TW_allsource.txt"
UBTV_FILENAME = "UBTV.txt"
GITHUB_REPO_DIR = "/home/runner/work/verify-iptv/verify-iptv"  # GitHub Actions 的工作目錄
SOURCE_DIR = os.path.join(GITHUB_REPO_DIR, "source")  # 文件存儲到 source 目錄
README_FILE = os.path.join(SOURCE_DIR, "README.md")  # README 文件路徑

# 配置日誌
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger(__name__)

# 下載檔案
def download_file(url: str, filename: str) -> None:
    logger.info(f"正在下載 {url} ...")
    try:
        response = requests.get(url)
        response.raise_for_status()  # 檢查 HTTP 狀態碼
        with open(filename, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"{filename} 下載完成！")
    except requests.exceptions.RequestException as e:
        logger.error(f"下載 {filename} 失敗: {e}")
        exit(1)

# 將文件移動到 GitHub 倉庫的 source 目錄
def move_to_source_dir(filename: str) -> None:
    try:
        # 確保 source 目錄存在
        if not os.path.exists(SOURCE_DIR):
            os.makedirs(SOURCE_DIR)
        # 移動文件
        os.rename(filename, os.path.join(SOURCE_DIR, filename))
        logger.info(f"文件已移動到 {SOURCE_DIR}")
    except Exception as e:
        logger.error(f"移動文件失敗: {e}")
        exit(1)

# 更新 README.md 文件
def update_readme() -> None:
    try:
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(README_FILE, "w", encoding="utf-8") as file:
            file.write(f"# 源文件更新記錄\n\n")
            file.write(f"最後更新時間: `{update_time}`\n\n")
            file.write(f"## 文件列表\n")
            file.write(f"- `{TW_FILENAME}`\n")
            file.write(f"- `{UBTV_FILENAME}`\n")
        logger.info(f"README.md 已更新！")
    except Exception as e:
        logger.error(f"更新 README.md 失敗: {e}")
        exit(1)

# Git 操作
def git_commit_and_push() -> None:
    logger.info("提交並推送變更到 GitHub...")
    try:
        # 進入 GitHub 倉庫目錄
        os.chdir(GITHUB_REPO_DIR)

        # Git 設定
        subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)

        # Git 提交與推送
        subprocess.run(["git", "add", "source"], check=True)
        subprocess.run(["git", "commit", "-m", "自動更新源文件及 README"], check=True)
        subprocess.run(["git", "push"], check=True)
        logger.info("推送完成！")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git 操作失敗: {e}")
        exit(1)

# 執行流程
def main() -> None:
    try:
        # 下載文件
        download_file(TW_URL, TW_FILENAME)
        download_file(UBTV_URL, UBTV_FILENAME)

        # 將文件移動到 source 目錄
        move_to_source_dir(TW_FILENAME)
        move_to_source_dir(UBTV_FILENAME)

        # 更新 README.md
        update_readme()

        # Git 操作
        git_commit_and_push()
    except Exception as e:
        logger.error(f"腳本執行失敗: {e}")
        exit(1)

if __name__ == "__main__":
    main()
