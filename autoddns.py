import os
import requests

# 从环境变量获取 Cloudflare API 配置信息
API_KEY = os.getenv("CLOUDFLARE_API_KEY")
EMAIL = os.getenv("CLOUDFLARE_EMAIL")
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")

# 确保从环境变量中获取到了这些信息
if not all([API_KEY, EMAIL, ZONE_ID]):
    print("缺少 Cloudflare 配置信息，请确保在 GitHub Secrets 中设置了 CLOUDFLARE_API_KEY, CLOUDFLARE_EMAIL 和 CLOUDFLARE_ZONE_ID。")
    exit(1)

# 域名与标记映射关系（扩展机场三字码）
LOCATION_TO_DOMAIN = {
    # 示例映射（可根据实际需求调整）
    # 美国
    "SJC": "us.616049.xyz",  # 圣何塞
    "LAX": "us.616049.xyz",  # 洛杉矶
    "SEA": "us.616049.xyz",  # 西雅图
    "JFK": "us.616049.xyz",  # 纽约 - 肯尼迪国际机场
    "ORD": "us.616049.xyz",  # 芝加哥 - 奥黑尔国际机场
    "DFW": "us.616049.xyz",  # 达拉斯 - 沃斯堡国际机场
    "MIA": "us.616049.xyz",  # 迈阿密国际机场
    "ATL": "us.616049.xyz",  # 亚特兰大国际机场
    "US": "us.616049.xyz",  # 美国

    # 德国
    "TXL": "de.616049.xyz",  # 柏林泰格尔机场
    "SXF": "de.616049.xyz",  # 柏林舍内费尔德机场
    "BER": "de.616049.xyz",  # 柏林勃兰登堡机场
    "MUC": "de.616049.xyz",  # 慕尼黑机场
    "FRA": "de.616049.xyz",  # 法兰克福机场
    "HAM": "de.616049.xyz",  # 汉堡机场
    "CGN": "de.616049.xyz",  # 科隆/波恩机场
    "STR": "de.616049.xyz",  # 斯图加特机场
    "DUS": "de.616049.xyz",  # 杜塞尔多夫机场
    "LEJ": "de.616049.xyz",  # 莱比锡/哈雷机场
    "NUE": "de.616049.xyz",  # 纽伦堡机场
    "HAJ": "de.616049.xyz",  # 汉诺威机场
    "BRE": "de.616049.xyz",  # 不来梅机场
    "DRS": "de.616049.xyz",  # 德累斯顿机场
    "DE": "de.616049.xyz",  # 德国
    
    # 日本
    "NRT": "jp.616049.xyz",  # 东京成田
    "HND": "jp.616049.xyz",  # 东京羽田
    "KIX": "jp.616049.xyz",  # 大阪关西国际机场
    "CTS": "jp.616049.xyz",  # 札幌新千岁机场
    "FUK": "jp.616049.xyz",  # 福冈机场
    "NGO": "jp.616049.xyz",  # 名古屋中部国际机场
    "OKA": "jp.616049.xyz",  # 冲绳那霸机场
    "JP": "jp.616049.xyz",  # 日本

    # 香港
    "HKG": "hk.616049.xyz",  # 香港国际机场
    "HK": "hk.616049.xyz",  # 香港

    # 韩国
    "ICN": "kr.616049.xyz",  # 仁川国际机场
    "PUS": "kr.616049.xyz",  # 釜山金海机场
    "GMP": "kr.616049.xyz",  # 首尔金浦机场
    "CJU": "kr.616049.xyz",  # 济州机场
    "TAE": "kr.616049.xyz",  # 大邱机场
    "KR": "kr.616049.xyz",  # 韩国

    # 台湾
    "TPE": "tw.616049.xyz",  # 台北桃园机场
    "TSA": "tw.616049.xyz",  # 台北松山机场
    "KHH": "tw.616049.xyz",  # 高雄国际机场
    "RMQ": "tw.616049.xyz",  # 台中清泉岗机场
    "TW": "tw.616049.xyz",  # 台湾

    # 新加坡
    "SIN": "sg.616049.xyz",   # 樟宜机场
    "SG": "sg.616049.xyz",  # 新加坡
    
    # CF优选
    "CF优选": "cf.616049.xyz"  # CF优选
}

# 从 cfip.txt 文件中读取前十个 IP 和标记
def get_ips_from_file(file_path, limit=10):
    ip_data = []
    try:
        with open(file_path, "r") as file:
            for line in file:
                if "#" in line:
                    ip, location = line.strip().split("#")
                    ip_data.append((ip.strip(), location.strip()))
                if len(ip_data) >= limit:
                    break
        return ip_data
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
        return []

# 检查是否已有相同记录
def check_existing_record(domain, ip):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    headers = {
        "X-Auth-Email": EMAIL,
        "X-Auth-Key": API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json().get("result", [])
        return any(record["name"] == domain and record["content"] == ip for record in records)
    print(f"检查记录失败: {response.status_code}, {response.text}")
    return False

# 添加新的 DNS 记录
def add_dns_record(domain, ip):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    data = {
        "type": "A",
        "name": domain,
        "content": ip,
        "ttl": 1,
        "proxied": False
    }
    headers = {
        "X-Auth-Email": EMAIL,
        "X-Auth-Key": API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"添加成功: {domain} -> {ip}")
    elif response.status_code == 409:
        print(f"记录已存在: {domain} -> {ip}")
    else:
        print(f"添加失败: {domain} -> {ip}, 错误信息: {response.status_code}, {response.text}")

# 主程序
if __name__ == "__main__":
    ip_data = get_ips_from_file("cfip.txt")
    if not ip_data:
        print("未读取到 IP 数据，请检查 cfip.txt 文件格式是否正确。")
    else:
        for ip, location in ip_data:
            domain = LOCATION_TO_DOMAIN.get(location)
            if domain:
                print(f"为域名 {domain} 添加 IP: {ip}")
                if not check_existing_record(domain, ip):
                    add_dns_record(domain, ip)
                else:
                    print(f"记录已存在，跳过: {domain} -> {ip}")
            else:
                print(f"未找到标记 {location} 对应的域名映射，跳过。")