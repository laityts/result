import os
import subprocess
import csv
import sys
import requests
import json
import random
from colo_emojis import colo_emojis
from sk import remove_unreachable_ips

# 检查是否已安装 requests
try:
    import requests
    print("requests 已安装")
except ImportError:
    print("requests 未安装，正在安装...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])

# 获取当前脚本的路径
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# 切换到当前脚本所在的目录
os.chdir(script_dir)

# 创建所需的目录
os.makedirs("csv", exist_ok=True)
os.makedirs("log", exist_ok=True)
os.makedirs("port", exist_ok=True)
os.makedirs("cfip", exist_ok=True)
os.makedirs("speed", exist_ok=True)

# 定义文件路径和变量
cfst_path = "cfst"
result_file = "csv/result.csv"
cfip_file = "cfip/ip.txt"
output_txt = "cfip/ip.txt"
port_txt = "port/ipport.txt"
log_file = "log/log.txt"
output_cf_txt = "speed/ip.txt"
iplog_file = "log/iplog.txt"
commit_message = "Update result.csv and ip.txt"
download_url = "https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_arm64.tar.gz"

# 定义 cfcolo 变量（目标区域）
cfcolo = "HKG,ICN,LAX,SJC,ORD,NRT,HND,FRA,SIN,LHR,TPE"

# 获取下载文件的文件名
downloaded_file = download_url.split("/")[-1]

# 删除文件的函数
def remove_file(file_path):
    """删除指定路径的文件"""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"已删除 {file_path} 文件。")

def get_colo(ip_address):
    """获取IP的colo信息并写入日志文件"""
    # 默认使用主 API
    backup_url = f'https://ipinfo.io/{ip_address}?token=fcadb7eaa35d6a'
    try:
        # 增加超时时间（连接超时 5 秒，读取超时 10 秒）
        response = requests.get(backup_url, timeout=(5, 10))
        if response.status_code == 200:
            data = response.json()
            # 将完整的响应数据写入日志文件
            with open(log_file, mode="a", encoding="utf-8") as log:
                log.write(f"完整数据来自 {ip_address}:\n")
                log.write(json.dumps(data, indent=4) + "\n\n")
            # 提取国家代码
            country = data.get('country', '未知')
            return f"{country}"
        else:
            print(f"主 API 请求失败，IP {ip_address} 状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"主 API 请求出错，IP {ip_address}: {e}")
    
    # 如果主 API 失败，尝试备用 API
    url = f'http://{ip_address}/cdn-cgi/trace'
    try:
        # 增加超时时间（连接超时 5 秒，读取超时 10 秒）
        response = requests.get(url, timeout=(5, 10))
        if response.status_code == 200:
            data = response.text
            # 将完整的响应数据写入日志文件
            with open(log_file, mode="a", encoding="utf-8") as log:
                log.write(f"完整数据来自 {ip_address}:\n")
                log.write(data + "\n\n")
            # 查找并提取colo信息
            for line in data.splitlines():
                if line.startswith('colo='):
                    return line.split('=')[1]
        else:
            print(f"备用 API 请求失败，IP {ip_address} 状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"备用 API 请求出错，IP {ip_address}: {e}")
    
    # 降低请求频率，每次请求后等待 1 秒
    time.sleep(1)
    
    return "CF优选"

# 检查 cfst 文件是否存在
if not os.path.exists(cfst_path):
    print(f"文件 {cfst_path} 不存在，正在执行安装和测试命令...")
    subprocess.run(["wget", "-N", download_url], check=True)
    if downloaded_file.endswith(".tar.gz"):
        try:
            subprocess.run(["tar", "-zxf", downloaded_file], check=True)
            print(f"已成功解压: {downloaded_file}")
        except subprocess.CalledProcessError as e:
            print(f"解压失败: {e}")
            sys.exit(1)
    elif downloaded_file.endswith(".zip"):
        try:
            subprocess.run(["unzip", downloaded_file], check=True)
            print(f"已成功解压: {downloaded_file}")
        except subprocess.CalledProcessError as e:
            print(f"解压失败: {e}")
            sys.exit(1)
    else:
        print("无法识别的压缩文件格式！")
        sys.exit(1)
    remove_file(downloaded_file)
    subprocess.run(["mv", "CloudflareST", "cfst"], check=True)
    subprocess.run(["chmod", "+x", "cfst"], check=True)

# 删除 result.csv 和 ip.txt 以及 log.txt 文件
remove_file(result_file)
remove_file(cfip_file)
remove_file(log_file)

# Cloudflare 支持的标准端口列表
cf_ports = [443, 2053, 2083, 2087, 2096, 8443]

# 随机选择 Cloudflare 的标准端口
random_port = random.choice(cf_ports)

# 执行 cfst 命令，使用变量传递 cfcolo 和随机端口
subprocess.run(["./cfst", "-o", "csv/result.csv", "-httping", "-cfcolo", cfcolo, "-tl", "150", "-tll", "20", "-tp", str(random_port), "-sl", "5", "-dn", "20"], check=True)

# 提取 IP 地址和下载速度，并保存到 ip.txt 和 ipport.txt
ip_addresses = []
download_speeds = []

with open(result_file, mode="r", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader)
    if "下载速度 (MB/s)" in header:
        speed_index = header.index("下载速度 (MB/s)")
    else:
        print("无法找到下载速度列，请检查 CSV 文件表头。")
        sys.exit(1)
    for row in reader:
        ip_addresses.append(row[0])
        download_speeds.append(row[speed_index])
        if len(ip_addresses) >= 20:
            break

# 将 IP 地址和 colo 信息写入 ip.txt
with open(output_txt, mode="w", encoding="utf-8") as txtfile:
    for ip, speed in zip(ip_addresses, download_speeds):
        colo = get_colo(ip)
        txtfile.write(f"{ip}#{colo}\n")
        print(f"IP: {ip}, Colo: {colo}")

print(f"提取的 IP 地址和 colo 信息已保存到 {output_txt}")

# 将 IP 地址、端口、colo 信息和下载速度写入 ipport.txt
with open(port_txt, mode="w", encoding="utf-8") as txtfile:
    for ip, speed in zip(ip_addresses, download_speeds):
        colo = get_colo(ip)
        emoji = colo_emojis.get(colo, "☁️")
        txtfile.write(f"{ip}:{str(random_port)}#{emoji}{colo}┃⚡{speed}(MB/s)\n")
        print(f"IP: {ip}, Port: {random_port}, Colo: {emoji}{colo}, Speed: {speed}")

print(f"提取的 IP 地址、端口、colo 信息和下载速度已保存到 {port_txt}")

remove_unreachable_ips(output_cf_txt, iplog_file)

# 筛选下载速度大于 10 MB/s 的 IP，并追加写入 ip.txt
with open(output_cf_txt, mode="a", encoding="utf-8") as cf_file:
    for ip, speed in zip(ip_addresses, download_speeds):
        if float(speed) > 10:
            colo = get_colo(ip)
            emoji = colo_emojis.get(colo, "☁️")
            cf_file.write(f"{ip}:{str(random_port)}#{emoji}{colo}┃⚡{speed}(MB/s)\n")
            print(f"符合条件的 IP: {ip}, Port: {random_port}, Colo: {emoji}{colo}, Speed: {speed}")

print(f"筛选出的 IP 地址、端口、colo 信息和下载速度已追加到 {output_cf_txt}")

# Git 上传步骤
try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print("已将文件上传到 GitHub 仓库。")
except subprocess.CalledProcessError as e:
    print(f"Git 操作失败: {e}")
    sys.exit(1)