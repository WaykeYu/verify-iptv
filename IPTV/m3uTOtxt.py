import os
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup


# GitHub 仓库的 URL
repo_url = 'https://github.com/WaykeYu/verify-iptv/tree/main'
# 原始文件的基础 URL
raw_base_url = 'https://raw.githubusercontent.com/WaykeYu/verify-iptv/main/'

# 本地保存目录
local_dir = 'downloaded_files'
os.makedirs(local_dir, exist_ok=True)

def download_m3u_files(repo_url):
    response = requests.get(repo_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # 查找所有链接
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.m3u'):
                # 构造原始文件的 URL
                raw_url = urljoin(raw_base_url, href.replace('/blob/', '/'))
                download_and_convert(raw_url)
    else:
        print(f'无法访问仓库页面，状态码: {response.status_code}')

def download_and_convert(file_url):
    response = requests.get(file_url)
    if response.status_code == 200:
        # 获取文件名并替换扩展名为 .txt
        filename = os.path.basename(file_url).replace('.m3u', '.txt')
        local_path = os.path.join(local_dir, filename)
        # 将内容写入本地文件
        with open(local_path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print(f'已下载并转换: {filename}')
    else:
        print(f'无法下载文件，状态码: {response.status_code}')

if __name__ == '__main__':
    download_m3u_files(repo_url)
