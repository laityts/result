import os
import subprocess
import csv
import sys
import requests
import random  # 导入 random 模块用于生成随机端口

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

# 定义文件路径和变量
cfst_path = "cfst"
result_file = "result.csv"
cfip_file = "cfip.txt"
output_txt = "cfip.txt"
log_file = "log.txt"  # 新增日志文件
commit_message = "Update result.csv and cfip.txt"
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

# 获取IP的colo信息，并将完整数据写入日志文件
def get_colo(ip_address):
    """获取IP的colo信息并写入日志文件"""
    # 主 API
    url = f'http://{ip_address}/cdn-cgi/trace'
    
    try:
        # 发送 GET 请求
        response = requests.get(url)
        
        # 如果请求成功
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
            print(f"主 API 请求失败，IP {ip_address} 状态码: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"主 API 请求出错，IP {ip_address}: {e}")
    
    # 如果主 API 失败，尝试备用 API
    backup_url = f'https://ipinfo.io/{ip_address}/json'
    try:
        response = requests.get(backup_url)
        if response.status_code == 200:
            data = response.json()
            # 将完整的响应数据写入日志文件
            with open(log_file, mode="a", encoding="utf-8") as log:
                log.write(f"完整数据来自 {ip_address}:\n")
                log.write(data + "\n\n")
            country = data.get('country', '未知')
            return f"{country}"
        else:
            print(f"备用 API 请求失败，IP {ip_address} 状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"备用 API 请求出错，IP {ip_address}: {e}")
    
    return "CF优选"

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

# 删除 result.csv 和 cfip.txt 以及 log.txt 文件
remove_file(result_file)
remove_file(cfip_file)
remove_file(log_file)

# Cloudflare 支持的标准端口列表
cf_ports = [
    80, 8080, 8880, 2052, 2082, 2086, 2095, # HTTP 标准端口
    443, 2053, 2083, 2087, 2096, 8443,  # HTTPS 标准端口
]

# 随机选择 Cloudflare 的标准端口
random_port = random.choice(cf_ports)

# 执行 cfst 命令，使用变量传递 cfcolo 和随机端口
subprocess.run(["./cfst", "-httping", "-cfcolo", cfcolo, "-tl", "200", "-tll", "20", "-tp", str(random_port), "-sl", "5", "-dn", "20"], check=True)

# 提取 IP 地址并保存到 cfip.txt
ip_addresses = []
with open(result_file, mode="r", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # 跳过表头
    for row in reader:
        # 假设 IP 地址在每行的第一列（索引为 0）
        ip_addresses.append(row[0])

# 将 IP 地址和 colo 信息写入 cfip.txt
with open(output_txt, mode="w", encoding="utf-8") as txtfile:
    for ip in ip_addresses:
        colo = get_colo(ip)  # 获取当前 IP 的 colo 信息
        txtfile.write(f"{ip}:{str(random_port)}#{colo}\n")  # 将 IP 和 colo 信息写入文件
        print(f"IP: {ip}, Colo: {colo}")

print(f"提取的 IP 地址和 colo 信息已保存到 {output_txt}")

# Git 上传步骤
try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print("已将文件上传到 GitHub 仓库。")
except subprocess.CalledProcessError as e:
    print(f"Git 操作失败: {e}")
    sys.exit(1)