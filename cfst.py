import os
import subprocess
import csv

# 定义文件路径
cfst_path = "cfst"
tar_file = "CloudflareST_linux_arm64.tar.gz"
result_file = "result.csv"
cfip_file = "cfip.txt"
output_txt = "cfip.txt"

# 检查 cfst 文件是否存在
if not os.path.exists(cfst_path):
    print(f"文件 {cfst_path} 不存在，正在执行安装和测试命令...")

    # 下载 CloudflareST
    subprocess.run(["wget", "-N", "https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_arm64.tar.gz"], check=True)
    
    # 解压缩 tar 文件
    subprocess.run(["tar", "-zxf", tar_file], check=True)
    
    # 删除下载的 tar 文件
    os.remove(tar_file)
    print(f"已删除 {tar_file} 文件。")
    
    # 重命名解压后的文件
    subprocess.run(["mv", "CloudflareST", "cfst"], check=True)
    
    # 设置 cfst 文件为可执行
    subprocess.run(["chmod", "+x", "cfst"], check=True)

# 删除 result.csv 和 cfip.txt 文件
if os.path.exists(result_file):
    os.remove(result_file)
    print(f"已删除 {result_file} 文件。")
if os.path.exists(cfip_file):
    os.remove(cfip_file)
    print(f"已删除 {cfip_file} 文件。")

# 执行 cfst 命令
subprocess.run(["./cfst", "-httping", "-tl", "120", "-cfcolo", "HKG", "-sl", "5"], check=True)

# 提取 IP 地址并保存到 cfip.txt
ip_addresses = []
with open(result_file, mode="r", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # 跳过表头
    for row in reader:
        # 假设 IP 地址在每行的第一列（索引为 0）
        ip_addresses.append(row[0])

with open(output_txt, mode="w", encoding="utf-8") as txtfile:
    for ip in ip_addresses:
        txtfile.write(ip + "\n")

print(f"提取的 IP 地址已保存到 {output_txt}")