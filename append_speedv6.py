import csv

# 读取 CSV 文件
with open('resultv6.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    next(csv_reader)  # 跳过标题行
    ip_speed = {rows[0]: rows[5] for rows in csv_reader}  # 提取 IP 和下载速度

# 读取 cfip.txt 文件并在每个 IP 的最后追加下载速度（使用 + 分隔）
with open('cfipv6.txt', 'r') as cfip_file:
    lines = cfip_file.readlines()

with open('cfipv6.txt', 'w') as cfip_file:
    for line in lines:
        ip = line.strip().split('#')[0]  # 提取 IP 地址（去掉 # 后面的内容）
        if ip in ip_speed:
            cfip_file.write(f"{line.strip()} | {ip_speed[ip]}\n")  # 在最后追加下载速度（使用 + 分隔）
        else:
            cfip_file.write(line)  # 如果 IP 不在 CSV 中，保留原行