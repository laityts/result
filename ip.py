import csv

# 输入的 CSV 文件路径
input_csv = "result.csv"
# 输出的 TXT 文件路径
output_txt = "cfip.txt"

# 初始化一个列表来存储 IP 地址
ip_addresses = []

# 读取 CSV 文件
with open(input_csv, mode="r", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # 跳过表头
    for row in reader:
        # 假设 IP 地址在每行的第一列（索引为 0）
        ip_addresses.append(row[0])

# 将提取的 IP 地址保存到 TXT 文件
with open(output_txt, mode="w", encoding="utf-8") as txtfile:
    for ip in ip_addresses:
        txtfile.write(ip + "\n")

print(f"提取的 IP 地址已保存到 {output_txt}")