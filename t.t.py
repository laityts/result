import json  # 导入 json 模块

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
                # 将字典转换为字符串
                data_str = json.dumps(data, indent=4)  # indent=4 用于美化输出
                log.write(data_str + "\n\n")
            country = data.get('country', '未知')
            return f"{country}"
        else:
            print(f"备用 API 请求失败，IP {ip_address} 状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"备用 API 请求出错，IP {ip_address}: {e}")
    
    return "CF优选"