import os
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def convert_m3u_to_txt(directory):
    """
    將指定目錄下的所有 .m3u 檔案轉換為 .txt 檔案。
    
    :param directory: 要處理的目錄路徑
    """
    # 檢查目錄是否存在
    if not os.path.exists(directory):
        print(f"錯誤：目錄 '{directory}' 不存在。")
        return

    # 遍歷指定目錄下的所有檔案
    for filename in os.listdir(directory):
        # 檢查檔案是否為 .m3u 檔案
        if filename.endswith(".m3u"):
            m3u_file_path = os.path.join(directory, filename)
            txt_file_path = os.path.join(directory, filename.replace(".m3u", ".txt"))
            
            try:
                # 讀取 .m3u 檔案內容
                with open(m3u_file_path, 'r', encoding='utf-8') as m3u_file:
                    content = m3u_file.read()
                
                # 將內容寫入 .txt 檔案
                with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(content)
                
                print(f"已轉換：{m3u_file_path} -> {txt_file_path}")
            
            except Exception as e:
                print(f"處理檔案 {m3u_file_path} 時發生錯誤：{e}")

if __name__ == "__main__":
    # 指定要處理的目錄（例如 GitHub 倉庫中的 'main' 目錄）
    target_directory = "main"
    
    # 呼叫函式進行轉換
    convert_m3u_to_txt(target_directory)
