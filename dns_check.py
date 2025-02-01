import requests
import socket
import logging
import os
import subprocess
import time
import sys
from dotenv import load_dotenv

# 创建 logs 目录（如果不存在）
logs_dir = 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# 删除旧的日志文件（如果存在）
log_file = os.path.join('logs', 'dns_check.log')
if os.path.exists(log_file):
    os.remove(log_file)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),  # 日志文件处理器
        logging.StreamHandler()  # 控制台日志处理器
    ]
)
logger = logging.getLogger()

# 现在可以安全地使用 logger
logger.info("已删除旧的日志文件: dns_check.log")

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量获取 Cloudflare API 配置信息
API_KEY = os.getenv("CLOUDFLARE_API_KEY")
EMAIL = os.getenv("CLOUDFLARE_EMAIL")
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 确保从环境变量中获取到了这些信息
if not all([API_KEY, EMAIL, ZONE_ID, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    logger.error("缺少必要的配置信息，请确保在 GitHub Secrets 中设置了 CLOUDFLARE_API_KEY, CLOUDFLARE_EMAIL, CLOUDFLARE_ZONE_ID, TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID。")
    sys.exit(1)

# Cloudflare API 基础 URL
base_url = f'https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records'

# 定义请求头
headers = {
    'X-Auth-Email': EMAIL,
    'X-Auth-Key': API_KEY,
    'Content-Type': 'application/json'
}

# 定义Ping检测函数（使用系统ping命令）
def ping_ip(ip, retries=3):
    for attempt in range(retries):
        try:
            # 调用系统ping命令
            result = subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            if result.returncode == 0:
                return True
            else:
                logger.warning(f"Ping 失败: {ip} (尝试 {attempt + 1}/{retries}): {result.stderr.decode().strip()}")
        except subprocess.TimeoutExpired:
            logger.warning(f"Ping 超时: {ip} (尝试 {attempt + 1}/{retries})")
        except Exception as e:
            logger.warning(f"Ping 失败: {ip} (尝试 {attempt + 1}/{retries}): {e}")
        time.sleep(1)  # 每次重试间隔1秒
    return False

# 定义TCP检测函数
def tcp_check(ip, port=443, retries=3):  # 默认端口改为443
    for attempt in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return True
            else:
                logger.warning(f"TCP 检测失败: {ip}:{port} (尝试 {attempt + 1}/{retries})")
        except Exception as e:
            logger.warning(f"TCP 检测失败: {ip}:{port} (尝试 {attempt + 1}/{retries}): {e}")
        time.sleep(1)  # 每次重试间隔1秒
    return False

# 获取DNS记录
def get_dns_records():
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        return response.json()['result']
    except Exception as e:
        logger.error(f"获取DNS记录失败: {e}")
        return []

# 删除DNS记录
def delete_dns_record(record_id):
    try:
        delete_url = f'{base_url}/{record_id}'
        response = requests.delete(delete_url, headers=headers)
        response.raise_for_status()
        logger.info(f"已删除DNS记录: {record_id}")
    except Exception as e:
        logger.error(f"删除DNS记录失败: {record_id}: {e}")

# 发送消息到 Telegram（不使用代理）
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info("消息已发送到 Telegram")
    except Exception as e:
        logger.error(f"发送消息到 Telegram 失败: {e}")

# 遍历DNS记录并检测
dns_records = get_dns_records()
for record in dns_records:
    if record['type'] in ['A', 'AAAA']:  # 只处理A和AAAA记录
        ip = record['content']
        record_id = record['id']
        record_name = record['name']

        logger.info(f"正在检查 {record_name} ({ip})...")

        # 进行Ping检测
        if not ping_ip(ip):
            logger.error(f"Ping 失败: {ip}. 正在删除记录 {record_name}...")
            delete_dns_record(record_id)
            #send_telegram_message(f"🚨 DNS 记录删除通知 🚨\n\n记录名称: {record_name}\nIP 地址: {ip}\n原因: Ping 失败")
            continue

        # 进行TCP检测（默认检测443端口）
        if not tcp_check(ip):
            logger.error(f"TCP 检测失败: {ip}. 正在删除记录 {record_name}...")
            delete_dns_record(record_id)
            #send_telegram_message(f"🚨 DNS 记录删除通知 🚨\n\n记录名称: {record_name}\nIP 地址: {ip}\n原因: TCP 检测失败")

logger.info("DNS记录检查与清理完成。")
#send_telegram_message("✅ DNS 记录检查与清理完成。")