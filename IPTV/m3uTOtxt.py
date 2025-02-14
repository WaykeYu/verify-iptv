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
                file_name = os.path.basename(href)
                m3u_files.append(("https://github.com" + raw_url, file_name))
        return m3u_files
    except requests.exceptions.RequestException as e:
        print(f"獲取 .m3u 文件列表失敗: {e}")
        return []

def download_and_convert(url, file_name):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        if not content.strip():
            print(f"{url} 文件內容為空")
            return

        txt_path = file_name.replace(".m3u", ".txt")

        with open(txt_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"已將 {file_name} 轉換並保存為 {txt_path}")

    except requests.exceptions.RequestException as e:
        print(f"下載或轉換文件失敗: {e}")

def main():
    base_url = "https://github.com/WaykeYu/verify-iptv"
    m3u_files = get_all_m3u_files(base_url)

    for url, file_name in m3u_files:
        download_and_convert(url, file_name)

if __name__ == "__main__":
    main()
