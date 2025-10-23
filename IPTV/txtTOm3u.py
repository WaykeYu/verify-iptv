import requests
import os
import shutil
import subprocess
import logging
from datetime import datetime
from time import sleep
from typing import Dict, List, Tuple, Optional
import re
import random
import socket
from urllib.parse import urlparse

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

# 從環境變數讀取設定，提供默認值
GITHUB_REPO_DIR = os.getenv("GITHUB_WORKSPACE", "/home/runner/work/verify-iptv/verify-iptv")
SOURCE_DIR = os.path.join(GITHUB_REPO_DIR, "source")
README_FILE = os.path.join(SOURCE_DIR, "README.md")
TEMP_DIR = os.path.join(GITHUB_REPO_DIR, "temp")

# 請求設定
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
RETRY_COUNT = int(os.getenv("RETRY_COUNT", "3"))
MIN_REQUEST_DELAY = float(os.getenv("MIN_REQUEST_DELAY", "3.0"))
MAX_REQUEST_DELAY = float(os.getenv("MAX_REQUEST_DELAY", "8.0"))

# === 日誌設定 ===
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# === User-Agent 池 ===
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

class RequestManager:
    """請求管理器，處理下載和重試邏輯"""
    
    @staticmethod
    def get_random_user_agent() -> str:
        """獲取隨機 User-Agent"""
        return random.choice(USER_AGENTS)
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """獲取請求頭"""
        return {
            'User-Agent': RequestManager.get_random_user_agent(),
            'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    @staticmethod
    def create_session() -> requests.Session:
        """創建會話"""
        session = requests.Session()
        session.headers.update(RequestManager.get_headers())
        
        # 配置重試策略 - 兼容新舊版本 urllib3
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        try:
            # 嘗試新版本參數名稱
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],  # 新版本參數
                backoff_factor=1
            )
        except TypeError:
            # 回退到舊版本參數名稱
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"],  # 舊版本參數
                backoff_factor=1
            )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

def check_dns_resolution(hostname: str) -> bool:
    """檢查域名解析"""
    try:
        socket.getaddrinfo(hostname, None)
        logger.debug(f"DNS 解析成功: {hostname}")
        return True
    except socket.gaierror as e:
        logger.warning(f"DNS 解析失敗 {hostname}: {e}")
        return False

def check_port_open(hostname: str, port: int, timeout: int = 5) -> bool:
    """檢查端口是否開放"""
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        logger.debug(f"端口檢查失敗 {hostname}:{port}: {e}")
        return False

def is_server_accessible(url: str) -> Tuple[bool, str]:
    """檢查伺服器是否可訪問"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            return False, "無效的 URL"
        
        # 檢查 DNS 解析
        if not check_dns_resolution(hostname):
            return False, "DNS 解析失敗"
        
        # 檢查端口
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        if not check_port_open(hostname, port):
            return False, "連接被拒絕（端口關閉）"
        
        return True, "伺服器可訪問"
        
    except Exception as e:
        return False, f"檢查失敗: {e}"

# === 工具函式 ===
def ensure_directories() -> None:
    """確保必要的目錄存在"""
    os.makedirs(SOURCE_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    logger.info("目錄結構已準備完成")

def is_valid_stream_url(url: str) -> bool:
    """檢查是否為有效的串流URL"""
    if not url or not isinstance(url, str):
        return False
    
    valid_patterns = [
        r'^https?://',
        r'^rtmp://',
        r'^rtsp://',
        r'^mms://',
        r'^udp://'
    ]
    
    url = url.strip()
    return any(re.match(pattern, url) for pattern in valid_patterns)

def cleanup_temp_files() -> None:
    """清理暫存檔案"""
    if os.path.exists(TEMP_DIR):
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    logger.debug(f"已清理暫存檔案: {filename}")
            except Exception as e:
                logger.warning(f"清理暫存檔案 {filename} 失敗: {e}")

def get_random_delay() -> float:
    """獲取隨機延遲時間"""
    return random.uniform(MIN_REQUEST_DELAY, MAX_REQUEST_DELAY)

def download_with_retry(url: str, filename: str, retries: int = RETRY_COUNT) -> Optional[requests.Response]:
    """帶重試機制的下載函數"""
    # 先檢查伺服器可訪問性
    is_accessible, reason = is_server_accessible(url)
    if not is_accessible:
        logger.warning(f"{filename} 伺服器不可訪問: {reason}")
        return None
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"正在下載 {filename} (嘗試 {attempt}/{retries}) ...")
            
            session = RequestManager.create_session()
            
            # 隨機延遲，避免請求過於頻繁
            if attempt > 1:
                delay = get_random_delay() * attempt
                logger.info(f"等待 {delay:.2f} 秒後重試...")
                sleep(delay)
            
            response = session.get(
                url, 
                timeout=REQUEST_TIMEOUT,
                stream=True
            )
            response.raise_for_status()
            
            # 檢查內容類型
            content_type = response.headers.get('content-type', '').lower()
            if 'html' in content_type and 'text' not in content_type:
                logger.warning(f"{filename} 可能返回了 HTML 頁面而非文本內容")
            
            return response

        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                logger.warning(f"{filename} 連接被拒絕 (嘗試 {attempt}/{retries}) - 伺服器可能已關閉")
                if attempt == retries:  # 最後一次嘗試
                    logger.error(f"{filename} 伺服器持續拒絕連接，可能已關閉或阻擋 IP")
                sleep(10)  # 長時間等待
            elif "Name or service not known" in error_msg:
                logger.error(f"{filename} DNS 解析失敗 (嘗試 {attempt}/{retries})")
                return None  # DNS 問題無法通過重試解決
            else:
                logger.warning(f"{filename} 連接錯誤 (嘗試 {attempt}/{retries}): {e}")
                
        except requests.exceptions.Timeout as e:
            logger.warning(f"{filename} 請求超時 (嘗試 {attempt}/{retries}): {e}")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"{filename} 觸發速率限制 (429)，等待後重試...")
                sleep(30)
            elif e.response.status_code == 403:
                logger.warning(f"{filename} 訪問被拒絕 (403)，可能是 IP 被阻擋")
                sleep(20)
            elif e.response.status_code == 404:
                logger.error(f"{filename} 文件不存在 (404)")
                return None  # 404 錯誤無法通過重試解決
            else:
                logger.warning(f"{filename} HTTP 錯誤 {e.response.status_code} (嘗試 {attempt}/{retries}): {e}")
                
        except requests.RequestException as e:
            logger.warning(f"{filename} 請求失敗 (嘗試 {attempt}/{retries}): {e}")
            
        except Exception as e:
            logger.error(f"{filename} 下載時發生意外錯誤 (嘗試 {attempt}/{retries}): {e}")
    
    logger.error(f"{filename} 下載多次仍失敗，跳過。")
    return None

def download_and_convert_to_m3u(url: str, filename: str, retries: int = RETRY_COUNT) -> Tuple[bool, int]:
    """
    下載來源並轉換成 M3U 格式
    
    Returns:
        Tuple[bool, int]: (是否成功, 處理的串流數量)
    """
    temp_filepath = os.path.join(TEMP_DIR, filename)
    
    response = download_with_retry(url, filename, retries)
    if response is None:
        return False, 0
    
    try:
        # 檢測編碼
        if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
            response.encoding = response.apparent_encoding or 'utf-8'
        
        content = response.text
        lines_processed = 0
        is_already_m3u = False
        
        # 分析內容格式
        content_preview = content[:1000].lower()
        if '#extm3u' in content_preview:
            is_already_m3u = True
            logger.info(f"{filename} 檢測為 M3U 格式")
        
        # 寫入檔案
        with open(temp_filepath, "w", encoding="utf-8") as file:
            if not is_already_m3u:
                file.write("#EXTM3U\n")
            
            for line_num, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                
                # 處理 M3U 格式
                if is_already_m3u:
                    file.write(line + '\n')
                    if line.startswith('#EXTINF'):
                        lines_processed += 1
                    continue
                
                # 處理其他格式
                processed = False
                
                # 格式1: 名稱,URL
                if ',' in line and not line.startswith('#'):
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        name, stream_url = parts
                        name = name.strip()
                        stream_url = stream_url.strip()
                        
                        if is_valid_stream_url(stream_url):
                            file.write(f"#EXTINF:-1,{name}\n{stream_url}\n")
                            lines_processed += 1
                            processed = True
                
                # 格式2: 其他分隔符
                if not processed:
                    for separator in ['|', '\t', '    ']:
                        if separator in line and not line.startswith('#'):
                            parts = line.split(separator, 1)
                            if len(parts) == 2:
                                name, stream_url = parts
                                name = name.strip()
                                stream_url = stream_url.strip()
                                
                                if is_valid_stream_url(stream_url):
                                    file.write(f"#EXTINF:-1,{name}\n{stream_url}\n")
                                    lines_processed += 1
                                    processed = True
                                    break

        logger.info(f"{filename} 處理完成，有效串流: {lines_processed} 個")
        return True, lines_processed
        
    except UnicodeDecodeError as e:
        logger.error(f"{filename} 編碼解碼錯誤: {e}")
        return False, 0
    except Exception as e:
        logger.error(f"{filename} 處理內容時發生錯誤: {e}")
        return False, 0

def move_to_source_dir(filename: str) -> bool:
    """移動檔案到 source 目錄"""
    try:
        temp_filepath = os.path.join(TEMP_DIR, filename)
        dst_path = os.path.join(SOURCE_DIR, filename)
        
        if not os.path.exists(temp_filepath):
            logger.error(f"暫存檔案不存在: {temp_filepath}")
            return False
        
        if os.path.exists(dst_path):
            os.remove(dst_path)
        
        shutil.move(temp_filepath, dst_path)
        logger.info(f"{filename} 已移動到 {SOURCE_DIR}")
        return True
    except Exception as e:
        logger.error(f"移動檔案 {filename} 失敗: {e}")
        return False

def validate_m3u_file(filepath: str) -> bool:
    """驗證 M3U 檔案格式"""
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return False
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            return False
            
        lines = content.splitlines()
        if not any(line.startswith('#EXTM3U') for line in lines[:3]):
            logger.warning(f"{os.path.basename(filepath)} 缺少 #EXTM3U 標頭")
            return False
            
        extinf_count = sum(1 for line in lines if line.startswith('#EXTINF'))
        if extinf_count == 0:
            logger.warning(f"{os.path.basename(filepath)} 沒有找到任何頻道條目")
            return False
            
        return True
    except Exception as e:
        logger.error(f"驗證檔案 {filepath} 時發生錯誤: {e}")
        return False

def update_readme(success_files: List[str], failed_files: List[str], error_details: Dict[str, str]) -> None:
    """更新 README.md"""
    try:
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        with open(README_FILE, "w", encoding="utf-8") as file:
            file.write("# IPTV 源文件更新記錄\n\n")
            file.write(f"最後更新時間: `{update_time}`\n\n")
            
            file.write("## 文件列表\n\n")
            
            if success_files:
                file.write("### ✅ 成功更新的文件\n")
                for fname in sorted(success_files):
                    file.write(f"- `{fname}`\n")
                file.write("\n")
            
            if failed_files:
                file.write("### ❌ 更新失敗的文件\n")
                for fname in sorted(failed_files):
                    error_msg = error_details.get(fname, "未知錯誤")
                    file.write(f"- `{fname}` - {error_msg}\n")
                file.write("\n")
            
            file.write("## 統計信息\n\n")
            file.write(f"- 總來源數: {len(SOURCES)}\n")
            file.write(f"- 成功更新: {len(success_files)}\n")
            file.write(f"- 更新失敗: {len(failed_files)}\n")
            file.write(f"- 成功率: {len(success_files)/len(SOURCES)*100:.1f}%\n\n")
            
            file.write("## 說明\n\n")
            file.write("失敗原因可能包括：伺服器關閉、連接被拒絕、DNS 解析失敗等。\n")
        
        logger.info("README.md 已更新")
    except Exception as e:
        logger.error(f"更新 README.md 失敗: {e}")
        raise

def git_commit_and_push() -> bool:
    """提交並推送到 GitHub"""
    try:
        logger.info("準備提交並推送變更...")
        
        if not os.path.exists(GITHUB_REPO_DIR):
            logger.error(f"GitHub 倉庫目錄不存在: {GITHUB_REPO_DIR}")
            return False
            
        os.chdir(GITHUB_REPO_DIR)

        subprocess.run([
            "git", "config", "user.name", 
            os.getenv("GIT_USER_NAME", "github-actions[bot]")
        ], check=True, capture_output=True)
        
        subprocess.run([
            "git", "config", "user.email",
            os.getenv("GIT_USER_EMAIL", "github-actions[bot]@users.noreply.github.com")
        ], check=True, capture_output=True)

        subprocess.run(["git", "add", "source/", "source/README.md"], 
                      check=True, capture_output=True)

        status_result = subprocess.run(
            ["git", "status", "--porcelain"], 
            capture_output=True, text=True, check=True
        )
        
        if not status_result.stdout.strip():
            logger.info("無變更需要提交")
            return True

        commit_message = f"自動更新 IPTV 源文件 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        subprocess.run([
            "git", "commit", "-m", commit_message
        ], check=True, capture_output=True)
        
        push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push_result.returncode == 0:
            logger.info("推送完成")
            return True
        else:
            logger.error(f"推送失敗: {push_result.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Git 操作失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"Git 操作發生意外錯誤: {e}")
        return False

def cleanup_old_files(current_files: List[str]) -> None:
    """清理不在當前來源列表中的舊檔案"""
    try:
        if not os.path.exists(SOURCE_DIR):
            return
            
        current_file_set = set(current_files) | {"README.md"}
        
        for filename in os.listdir(SOURCE_DIR):
            if filename not in current_file_set:
                file_path = os.path.join(SOURCE_DIR, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"已清理舊檔案: {filename}")
                except Exception as e:
                    logger.warning(f"清理舊檔案 {filename} 失敗: {e}")
    except Exception as e:
        logger.error(f"清理舊檔案時發生錯誤: {e}")

def main() -> None:
    """主執行函數"""
    start_time = datetime.now()
    logger.info("=== IPTV 源文件更新任務開始 ===")
    
    try:
        ensure_directories()
        cleanup_temp_files()
        
        success_files = []
        failed_files = []
        error_details = {}
        total_streams = 0
        
        logger.info(f"開始處理 {len(SOURCES)} 個來源...")
        
        for idx, (filename, url) in enumerate(SOURCES.items(), 1):
            logger.info(f"[{idx}/{len(SOURCES)}] 處理 {filename}")
            
            # 預先檢查伺服器狀態
            is_accessible, reason = is_server_accessible(url)
            if not is_accessible:
                logger.warning(f"{filename} 跳過：{reason}")
                failed_files.append(filename)
                error_details[filename] = reason
                continue
            
            success, stream_count = download_and_convert_to_m3u(url, filename)
            
            if success:
                if move_to_source_dir(filename):
                    file_path = os.path.join(SOURCE_DIR, filename)
                    if validate_m3u_file(file_path):
                        success_files.append(filename)
                        total_streams += stream_count
                        logger.info(f"✅ {filename} 處理成功 ({stream_count} 個串流)")
                    else:
                        failed_files.append(filename)
                        error_details[filename] = "檔案驗證失敗"
                        try:
                            os.remove(file_path)
                        except:
                            pass
                else:
                    failed_files.append(filename)
                    error_details[filename] = "檔案移動失敗"
            else:
                failed_files.append(filename)
                error_details[filename] = "下載或轉換失敗"
            
            if idx < len(SOURCES):
                delay = get_random_delay()
                logger.info(f"等待 {delay:.2f} 秒後處理下一個...")
                sleep(delay)
        
        cleanup_old_files(success_files)
        
        success_rate = len(success_files) / len(SOURCES) * 100 if SOURCES else 0
        logger.info(f"處理完成: 成功 {len(success_files)}/{len(SOURCES)} ({success_rate:.1f}%)")
        logger.info(f"總共處理串流數: {total_streams}")
        
        if success_files:
            update_readme(success_files, failed_files, error_details)
            
            if git_commit_and_push():
                logger.info("✅ GitHub 提交成功")
            else:
                logger.warning("⚠️ GitHub 提交失敗，但檔案已更新")
        else:
            logger.error("❌ 沒有任何文件成功處理，跳過提交")
            return
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"任務執行完成，總用時: {execution_time:.2f} 秒")
        
    except KeyboardInterrupt:
        logger.info("任務被用戶中斷")
    except Exception as e:
        logger.error(f"任務執行失敗: {e}")
        raise
    finally:
        cleanup_temp_files()
        logger.info("=== 任務結束 ===")

if __name__ == "__main__":
    main()
