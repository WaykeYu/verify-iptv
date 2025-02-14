import os
import requests
from bs4 import BeautifulSoup

def get_all_m3u_files(base_url):
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        m3u_files = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.endswith('.m3u') and 'blob' in href:
                raw_url = href.replace('/blob/', '/raw/')
                m3u_files.append(("https://github.com" + raw_url, href))
        return m3u_files
    except requests.exceptions.RequestException as e:
        print(f"獲取 .m3u 文件列表失敗: {e}")
        return []

def download_and_convert(url, original_path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        if not content.strip():
            print(f"{url} 文件內容為空")
            return

        txt_content = content.replace(".m3u", ".txt")
        new_path = original_path.replace(".m3u", ".txt")

        with open(new_path, 'w', encoding='utf-8') as file:
            file.write(txt_content)
        print(f"已將 {original_path} 轉換並保存為 {new_path}")

    except requests.exceptions.RequestException as e:
        print(f"下載或轉換文件失敗: {e}")

def main():
    base_url = "https://github.com/WaykeYu/verify-iptv"
    m3u_files = get_all_m3u_files(base_url)

    for url, original_path in m3u_files:
        download_and_convert(url, original_path)

if __name__ == "__main__":
    main()
