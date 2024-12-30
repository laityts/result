import os
import subprocess
import csv
import sys
import requests
import json  # 导入 json 模块
import random  # 导入 random 模块用于生成随机端口
from colo_emojis import colo_emojis

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
os.makedirs("cf", exist_ok=True)

# 定义文件路径和变量
cfst_path = "cfst"
result_file = "csv/resultfd.csv"
cfip_file = "cfip/cfipfd.txt"
output_txt = "cfip/cfipfd.txt"
port_txt = "port/cfipfdport.txt"
log_file = "log/logfd.txt"  # 新增日志文件
output_cf_txt = "cf/cffd.txt"# 定义下载速度优选文件路径
commit_message = "Update result.csv and cfipfd.txt"
download_url = "https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_arm64.tar.gz"  # 使用变量存储下载 URL

# 定义 cfcolo 变量（目标区域）
cfcolo = "HKG,SJC,LAX,SIN,ICN,NRT"  # 示例区域，您可以根据需要修改此变量

# 获取下载文件的文件名
downloaded_file = download_url.split("/")[-1]

# 删除文件的函数
def remove_file(file_path):
    """删除指定路径的文件"""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"已删除 {file_path} 文件。")

# 获取 IP 的 colo 信息，并将完整数据写入日志文件
def get_colo(ip_address):
    """获取 IP 的 colo 信息并写入日志文件"""
    api_url = f"https://proxyip.edtunnel.best/api?ip={ip_address}&host=speed.cloudflare.com&port=443&tls=true"
    
    try:
        # 发送 GET 请求
        response = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        
        # 如果请求成功
        if response.status_code == 200:
            data = response.json()
            # 将完整的响应数据写入日志文件
            with open(log_file, mode="a", encoding="utf-8") as log:
                log.write(f"完整数据来自 {ip_address}:\n")
                log.write(str(data) + "\n\n")
            
            # 返回 colo 信息
            return data.get("colo", "Proxy")
        else:
            print(f"API 请求失败，IP {ip_address}，状态码: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"IP {ip_address} 的请求发生错误: {e}")
    
    return "Proxy"

# 检查 cfst 文件是否存在
if not os.path.exists(cfst_path):
    print(f"文件 {cfst_path} 不存在，正在执行安装和测试命令...")

    # 使用变量下载 CloudflareST
    subprocess.run(["wget", "-N", download_url], check=True)

    # 判断下载文件的后缀并解压
    if downloaded_file.endswith(".tar.gz"):
        # 解压 tar.gz 文件
        try:
            subprocess.run(["tar", "-zxf", downloaded_file], check=True)
            print(f"已成功解压: {downloaded_file}")
        except subprocess.CalledProcessError as e:
            print(f"解压失败: {e}")
            sys.exit(1)
    elif downloaded_file.endswith(".zip"):
        # 解压 zip 文件
        try:
            subprocess.run(["unzip", downloaded_file], check=True)
            print(f"已成功解压: {downloaded_file}")
        except subprocess.CalledProcessError as e:
            print(f"解压失败: {e}")
            sys.exit(1)
    else:
        print("无法识别的压缩文件格式！")
        sys.exit(1)

    # 删除下载的压缩文件
    remove_file(downloaded_file)
    
    # 重命名解压后的文件
    subprocess.run(["mv", "CloudflareST", "cfst"], check=True)
    
    # 设置 cfst 文件为可执行
    subprocess.run(["chmod", "+x", "cfst"], check=True)

# 删除 resultfd.csv 和 cfipfd.txt 以及 logfd.txt 文件
remove_file(result_file)
remove_file(cfip_file)
remove_file(log_file)

# Cloudflare 支持的标准端口列表
cf_ports = [
    443, 2053, 2083, 2087, 2096, 8443,  # HTTPS 标准端口
]

# 随机选择 Cloudflare 的标准端口
random_port = random.choice(cf_ports)

# 执行 cfst 命令，使用变量传递 cfcolo
subprocess.run(["./cfst", "-f", "proxy.txt", "-o", "csv/resultfd.csv", "-httping", "-tl", "300", "-tll", "20", "-tp", "443", "-dn", "20"], check=True)

# 提取 IP 地址和下载速度，并保存到 cfipfd.txt 和 cfipfdport.txt
ip_addresses = []
download_speeds = []

with open(result_file, mode="r", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader)  # 读取表头
    # 确认下载速度所在的列
    if "下载速度 (MB/s)" in header:  # 假设表头中有 "下载速度 (MB/s)"
        speed_index = header.index("下载速度 (MB/s)")
    else:
        print("无法找到下载速度列，请检查 CSV 文件表头。")
        sys.exit(1)
    
    # 提取 IP 地址和下载速度
    for row in reader:
        ip_addresses.append(row[0])  # 假设 IP 地址在第一列
        download_speeds.append(row[speed_index])  # 使用 speed_index 获取下载速度
        # 如果已经提取了 20 个 IP，则停止提取
        if len(ip_addresses) >= 20:
            break

# 将 IP 地址和 colo 信息写入 cfipfd.txt
with open(output_txt, mode="w", encoding="utf-8") as txtfile:
    for ip, speed in zip(ip_addresses, download_speeds):
        colo = get_colo(ip)  # 获取当前 IP 的 colo 信息
        txtfile.write(f"{ip}#{colo}\n")  # 将 IP 和 colo 信息写入文件
        print(f"IP: {ip}, Colo: {colo}")

print(f"提取的 IP 地址和 colo 信息已保存到 {output_txt}")

# 将 IP 地址、端口、colo 信息和下载速度写入 cfipfdport.txt
with open(port_txt, mode="w", encoding="utf-8") as txtfile:
    for ip, speed in zip(ip_addresses, download_speeds):
        colo = get_colo(ip)  # 获取当前 IP 的 colo 信息
        emoji = colo_emojis.get(colo, "☁️")  # 获取对应的表情符号，默认为 ☁️
        txtfile.write(f"{ip}:{str(random_port)}#{emoji}{colo}┃⚡{speed}(MB/s)\n")  # 将 IP、端口、colo 信息和下载速度写入文件
        print(f"IP: {ip}, Port: {random_port}, Colo: {emoji}{colo}, Speed: {speed}")

print(f"提取的 IP 地址、端口、colo 信息和下载速度已保存到 {port_txt}")

# Git 上传步骤
try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print("已将文件上传到 GitHub 仓库。")
except subprocess.CalledProcessError as e:
    print(f"Git 操作失败: {e}")
    sys.exit(1)