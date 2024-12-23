import os
import subprocess
import csv
import sys
import requests

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
cfcolo = "HKG,SJC,LAX"  # 示例区域，您可以根据需要修改此变量

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
            print(f"Request failed for IP {ip_address} with status code: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred for IP {ip_address}: {e}")
    
    return "Could not retrieve colo"

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

# 执行 cfst 命令，使用变量传递 cfcolo
subprocess.run(["./cfst", "-httping", "-cfcolo", cfcolo, "-tl", "200", "-tp", "443", "-sl", "5", "-dn", "20", "-p", "10"], check=True)

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
        txtfile.write(f"{ip}#{colo}\n")  # 将 IP 和 colo 信息写入文件
        print(f"IP: {ip}, Colo: {colo}")

print(f"提取的 IP 地址和 colo 信息已保存到 {output_txt}")

# Git 上传步骤
try:
    subprocess.run(["git", "add", result_file, cfip_file, log_file], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print("已将文件上传到 GitHub 仓库。")
except subprocess.CalledProcessError as e:
    print(f"Git 操作失败: {e}")
    sys.exit(1)