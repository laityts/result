import os
import requests
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dns_update.log"),
        logging.StreamHandler()
    ]
)

# 从环境变量获取 Cloudflare API 配置信息
API_KEY = os.getenv("CLOUDFLARE_API_KEY")
EMAIL = os.getenv("CLOUDFLARE_EMAIL")
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")

# 确保从环境变量中获取到了这些信息
if not all([API_KEY, EMAIL, ZONE_ID]):
    logging.error("缺少 Cloudflare 配置信息，请确保在 GitHub Secrets 中设置了 CLOUDFLARE_API_KEY, CLOUDFLARE_EMAIL 和 CLOUDFLARE_ZONE_ID。")
    sys.exit(1)

# 域名与标记映射关系（扩展机场三字码）
LOCATION_TO_DOMAIN = {
    # 示例映射（可根据实际需求调整）
    # 美国
    "SJC": "us.616049.xyz",  # 圣何塞
    "LAX": "us.616049.xyz",  # 洛杉矶
    "SEA": "us.616049.xyz",  # 西雅图
    "JFK": "us.616049.xyz",  # 纽约 - 肯尼迪国际机场
    "ORD": "us.616049.xyz",  # 芝加哥 - 奥黑尔国际机场
    "US": "us.616049.xyz",  # 美国

    # 德国
    "FRA": "de.616049.xyz",  # 法兰克福机场
    "DE": "de.616049.xyz",  # 德国

    # 英国
    "LHR": "uk.616049.xyz",  # 伦敦
    "UK": "uk.616049.xyz",  # 英国
    
    # 日本
    "NRT": "jp.616049.xyz",  # 东京成田
    "HND": "jp.616049.xyz",  # 东京羽田
    "JP": "jp.616049.xyz",  # 日本

    # 香港
    "HKG": "hk.616049.xyz",  # 香港国际机场
    "HK": "hk.616049.xyz",  # 香港

    # 韩国
    "ICN": "kr.616049.xyz",  # 仁川国际机场
    "KR": "kr.616049.xyz",  # 韩国

    # 台湾
    "TPE": "tw.616049.xyz",  # 台北桃园机场
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
        logging.error(f"文件未找到: {file_path}")
        return []

# 删除相同前缀的所有 DNS 记录（完全匹配）
def delete_dns_records_with_prefix(prefix):
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
        headers = {
            "X-Auth-Email": EMAIL,
            "X-Auth-Key": API_KEY,
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        records = response.json().get("result", [])
        logging.info(f"找到 {len(records)} 条 DNS 记录，开始删除与 {prefix} 完全匹配的记录...")
        for record in records:
            # 提取记录名称的前缀（例如 "proxy.us.616049.xyz" 的前缀是 "proxy"）
            record_prefix = record["name"].split(".")[0]
            # 仅删除与给定前缀完全匹配的记录
            if record_prefix == prefix:
                # 打印即将删除的 DNS 记录的详细信息
                logging.info(f"即将删除记录: 名称={record['name']}, 类型={record['type']}, 内容={record['content']}, TTL={record['ttl']}, 代理={record['proxied']}")
                record_id = record["id"]
                delete_url = f"{url}/{record_id}"
                delete_response = requests.delete(delete_url, headers=headers)
                if delete_response.status_code == 200:
                    logging.info(f"已删除记录: {record['name']} -> {record['content']}")
                else:
                    logging.error(f"删除失败: {record['name']} -> {record['content']}, 错误信息: {delete_response.status_code}, {delete_response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"请求失败: {e}")
        sys.exit(1)

# 批量添加 DNS 记录
def add_dns_records_bulk(ip_data):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    headers = {
        "X-Auth-Email": EMAIL,
        "X-Auth-Key": API_KEY,
        "Content-Type": "application/json"
    }
    # 记录已经删除过哪些前缀
    deleted_prefixes = set()
    for ip, location in ip_data:
        domain = LOCATION_TO_DOMAIN.get(location)
        if domain:
            # 提取前缀（例如 "proxy.us.616049.xyz" 的前缀是 "proxy"）
            prefix = domain.split(".")[0]
            # 如果该前缀没有被删除过，则删除该前缀的所有 DNS 记录
            if prefix not in deleted_prefixes:
                delete_dns_records_with_prefix(prefix)
                deleted_prefixes.add(prefix)  # 标记该前缀已删除
            data = {
                "type": "A",
                "name": domain,
                "content": ip,
                "ttl": 1,
                "proxied": False
            }
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    logging.info(f"添加成功: {domain} -> {ip}")
                elif response.status_code == 409:
                    logging.info(f"记录已存在: {domain} -> {ip}")
                else:
                    logging.error(f"添加失败: {domain} -> {ip}, 错误信息: {response.status_code}, {response.text}")
            except requests.exceptions.RequestException as e:
                logging.error(f"请求失败: {e}")
        else:
            logging.warning(f"未找到标记 {location} 对应的域名映射，跳过。")

# 主程序
if __name__ == "__main__":
    # 添加新的 DNS 记录
    ip_data = get_ips_from_file("cfip/cfip.txt")
    if not ip_data:
        logging.error("未读取到 IP 数据，请检查 cfip.txt 文件格式是否正确。")
    else:
        add_dns_records_bulk(ip_data)