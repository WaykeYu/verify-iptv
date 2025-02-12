import requests
import os
import subprocess

# 設定變數
TW_URL = "https://raw.githubusercontent.com/WaykeYu/MyTV_tw/refs/heads/main/TW_allsource"
UBTV_URL = "https://raw.githubusercontent.com/WaykeYu/MyTV_tw/refs/heads/main/UBTV"
TW_FILENAME = "TW_allsource.txt"
UBTV_FILENAME = "UBTV.txt"
MERGED_FILENAME = "TW_allsource.m3u"

# 下載檔案
def download_file(url, filename):
    print(f"正在下載 {url} ...")
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"{filename} 下載完成！")
    else:
        print(f"下載 {filename} 失敗，HTTP 狀態碼: {response.status_code}")
        exit(1)

# 轉換為 M3U 格式
def convert_to_m3u(input_files, output_file):
    print("正在轉換為 M3U 格式...")
    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write("#EXTM3U\n")
        for input_file in input_files:
            with open(input_file, "r", encoding="utf-8") as infile:
                for line in infile:
                    parts = line.strip().split(",")
                    if len(parts) == 2:
                        name, url = parts
                        outfile.write(f"#EXTINF:-1,{name}\n{url}\n")
    print(f"轉換完成，已儲存為 {output_file}")

# Git 操作
def git_commit_and_push():
    print("提交並推送變更到 GitHub...")

    # Git 設定
    subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"])
    subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])

    # Git 提交與推送
    subprocess.run(["git", "add", MERGED_FILENAME])
    subprocess.run(["git", "commit", "-m", "自動更新 M3U 檔案"], check=True)
    subprocess.run(["git", "push"], check=True)

    print("推送完成！")

# 執行流程
def main():
    download_file(TW_URL, TW_FILENAME)
    download_file(UBTV_URL, UBTV_FILENAME)
    convert_to_m3u([TW_FILENAME, UBTV_FILENAME], MERGED_FILENAME)
    git_commit_and_push()

if __name__ == "__main__":
    main()
