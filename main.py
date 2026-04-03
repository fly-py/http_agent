# http_proxy.py - HTTP代理服务器
import socket
import threading
import json
import datetime
import os

class HTTPProxy:
    def __init__(self, config_file='config.json'):
        # 加载配置文件
        config_path = config_file
        
        # 打印当前工作目录和配置文件路径，便于调试
        print(f"当前工作目录: {os.getcwd()}")
        print(f"尝试加载配置文件: {config_path}")
        print(f"配置文件是否存在: {os.path.exists(config_path)}")
        
        self.blocked_domains = []  # 存储被禁止访问的域名
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"成功加载配置文件，内容: {json.dumps(config, indent=2)}")
            
            self.host = config.get('host', '0.0.0.0')
            self.port = config.get('port', 8888)
            self.log_file = config.get('log_file', False)
            
            # 加载被禁止的网站列表
            self.blocked_domains = config.get('block', [])
            print(f"原始block数据: {self.blocked_domains}")
            
            if isinstance(self.blocked_domains, list):
                # 标准化域名：去除空白字符，转换为小写
                self.blocked_domains = [domain.strip().lower() for domain in self.blocked_domains if domain.strip()]
            else:
                self.blocked_domains = []
                
        except FileNotFoundError:
            print(f"配置文件 {config_path} 不存在")
            # 创建默认配置文件
            default_config = {
                "host": "0.0.0.0",
                "port": 8888,
                "log_file": False,
                "block": ["example.com"]  # 添加一个示例
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            print(f"创建默认配置文件: {config_file}")
            
            # 重新加载配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.host = config.get('host', '0.0.0.0')
            self.port = config.get('port', 8888)
            self.log_file = config.get('log_file', False)
            self.blocked_domains = config.get('block', [])
            if isinstance(self.blocked_domains, list):
                self.blocked_domains = [domain.strip().lower() for domain in self.blocked_domains if domain.strip()]
            else:
                self.blocked_domains = []
                
        except json.JSONDecodeError as e:
            print(f"警告: 配置文件格式错误 {config_file}: {e}")
            print("使用默认配置: host=0.0.0.0, port=8888, log_file=False, block=[]")
            self.host = '0.0.0.0'
            self.port = 8888
            self.log_file = False
            self.blocked_domains = []

        self.running = True
        self.log_lock = threading.Lock()
        
        print(f"\n{'='*50}")
        print(f"代理服务器配置:")
        print(f"  主机: {self.host}")
        print(f"  端口: {self.port}")
        print(f"  日志文件: {self.log_file}")
        print(f"  拦截域名列表: {self.blocked_domains}")
        print(f"{'='*50}\n")
        
    def parse_request(self, data):
        """解析HTTP请求"""
        try:
            lines = data.decode('utf-8').split('\r\n')
            if lines:
                parts = lines[0].split(' ')
                if len(parts) >= 2:
                    method = parts[0]
                    url = parts[1]
                    return method, url
        except:
            pass
        return None, None
    
    def extract_host_from_request(self, data):
        """从HTTP请求中提取目标主机"""
        try:
            lines = data.decode('utf-8', errors='ignore').split('\r\n')
            for line in lines:
                if line.lower().startswith('host:'):
                    host_part = line.split(':', 1)[1].strip()
                    # 去除端口号
                    host = host_part.split(':')[0]
                    print(f"[DEBUG] 从HTTP请求提取到主机: {host}")
                    return host.lower()
        except Exception as e:
            print(f"[DEBUG] 提取主机失败: {e}")
        return None
    
    def extract_host_from_connect(self, url):
        """从CONNECT请求中提取目标主机"""
        try:
            host_port = url.split(':')
            host = host_port[0]
            print(f"[DEBUG] 从CONNECT请求提取到主机: {host}")
            return host.lower()
        except:
            pass
        return None
    
    def is_blocked(self, host):
        """检查域名是否被禁止访问"""
        if not host or not self.blocked_domains:
            return False
        
        host = host.lower()
        for blocked in self.blocked_domains:
            # 精确匹配或子域名匹配
            if host == blocked or host.endswith('.' + blocked):
                print(f"[DEBUG] 域名 {host} 匹配拦截规则: {blocked}")
                return True
        return False
    
    def send_forbidden_response(self, client_socket, host):
        """发送403禁止访问响应"""
        body = f"""<html>
<head><title>403 Forbidden</title></head>
<body>
<h1>403 Forbidden</h1>
<p>Access to <b>{host}</b> is forbidden by proxy policy.</p>
<hr>
<small>HTTP Proxy Server</small>
</body>
</html>"""
        
        response = f"""HTTP/1.1 403 Forbidden
Content-Type: text/html; charset=utf-8
Content-Length: {len(body)}
Connection: close

{body}"""
        
        try:
            client_socket.send(response.encode('utf-8'))
            print(f"[拦截] 向客户端发送403响应，阻止访问: {host}")
        except Exception as e:
            print(f"发送403响应失败: {e}")
    
    def log_to_file(self, message):
        """将日志写入文件"""
        if self.log_file:
            with self.log_lock:
                with open('proxy.log', 'a', encoding='utf-8') as log_file:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_file.write(f"[{timestamp}] {message}\n")
    
    def log(self, message):
        """统一日志处理"""
        print(message)
        self.log_to_file(message)
        
    def handle_client(self, client_socket, client_addr):
        self.log(f"\n{'='*50}")
        self.log(f"处理来自 {client_addr} 的新连接")

        try:
            request_data = client_socket.recv(8192)  # 增加缓冲区大小
            if not request_data:
                return

            # 打印原始请求的前200个字符用于调试
            try:
                request_preview = request_data[:200].decode('utf-8', errors='ignore')
                print(f"[DEBUG] 收到请求: {request_preview[:100]}...")
            except:
                pass

            method, url = self.parse_request(request_data)
            print(f"[DEBUG] 方法: {method}, URL: {url}")

            if method == 'CONNECT' and url:
                # HTTPS连接 - 检查是否被禁止
                remote_host = self.extract_host_from_connect(url)
                
                print(f"[DEBUG] CONNECT请求目标主机: {remote_host}")
                
                if self.is_blocked(remote_host):
                    self.log(f"阻止HTTPS访问被禁止的网站: {remote_host}")
                    self.send_forbidden_response(client_socket, remote_host)
                    return
                
                try:
                    host_port = url.split(':')
                    remote_host = host_port[0]
                    remote_port = int(host_port[1]) if len(host_port) > 1 else 443

                    self.log(f"建立HTTPS隧道到 {remote_host}:{remote_port}")

                    # 连接到远程服务器
                    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote_socket.settimeout(30)  # 设置超时
                    remote_socket.connect((remote_host, remote_port))

                    # 发送连接建立响应
                    client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')

                    # 开始双向转发
                    self.tunnel(client_socket, remote_socket)

                except Exception as e:
                    self.log(f"HTTPS隧道建立失败: {e}")
                    try:
                        client_socket.send(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
                    except:
                        pass
                    return

            elif method and url:
                # 处理所有其他HTTP方法 (GET, POST, PUT, DELETE, HEAD, OPTIONS, TRACE等)
                # 提取目标主机
                target_host = self.extract_host_from_request(request_data)
                
                print(f"[DEBUG] HTTP请求目标主机: {target_host}")
                
                # 检查是否被禁止访问
                if target_host and self.is_blocked(target_host):
                    self.log(f"阻止HTTP访问被禁止的网站: {target_host}")
                    self.send_forbidden_response(client_socket, target_host)
                    return
                
                try:
                    lines = request_data.decode('utf-8', errors='ignore').split('\r\n')
                    host_line = [l for l in lines if l.lower().startswith('host:')]

                    if host_line:
                        host_part = host_line[0].split(': ', 1)[1]
                        host = host_part.split(':')[0]
                        remote_port = 80

                        # 检查是否有端口指定
                        if ':' in host_part:
                            try:
                                remote_port = int(host_part.split(':')[1])
                            except ValueError:
                                remote_port = 80

                        self.log(f"转发{method}请求到 {host}:{remote_port}")

                        # 连接到目标服务器
                        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        remote_socket.settimeout(30)  # 设置超时
                        remote_socket.connect((host, remote_port))
                        remote_socket.sendall(request_data)

                        # 转发响应
                        while True:
                            response = remote_socket.recv(8192)
                            if not response:
                                break
                            client_socket.send(response)

                        remote_socket.close()
                    else:
                        self.log("无效的HTTP请求: 缺少Host头")
                        client_socket.send(b'HTTP/1.1 400 Bad Request\r\n\r\n')

                except Exception as e:
                    self.log(f"HTTP请求处理失败: {e}")
                    try:
                        client_socket.send(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
                    except:
                        pass
            else:
                # 处理非HTTP请求或无效请求
                self.log(f"收到无效请求或不支持的协议: method={method}, url={url}")
                try:
                    # 尝试发送HTTP错误响应
                    client_socket.send(b'HTTP/1.1 400 Bad Request\r\n\r\n')
                except:
                    pass

        except Exception as e:
            self.log(f"客户端处理错误: {e}")
        finally:
            try:
                client_socket.close()
                self.log(f"连接 {client_addr} 已关闭")
                self.log(f"{'='*50}\n")
            except Exception as e:
                self.log(f"关闭连接 {client_addr} 时出错: {e}")
                self.log(f"{'='*50}\n")
    
    def tunnel(self, client, server):
        """建立双向隧道"""
        def forward(source, dest):
            try:
                while True:
                    # 设置转发超时，避免连接一直占用
                    source.settimeout(300)  # 5分钟超时
                    data = source.recv(4096)
                    if not data:
                        break
                    dest.sendall(data)
            except Exception as e:
                # 只记录错误，不中断程序
                self.log(f"隧道转发错误: {e}")
                pass
        
        threads = [
            threading.Thread(target=forward, args=(client, server)),
            threading.Thread(target=forward, args=(server, client))
        ]
        
        for t in threads:
            t.daemon = True
            t.start()
        
        threads[0].join()
    
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        
        self.log(f"HTTP代理服务器启动在 {self.host}:{self.port}")
        
        try:
            while self.running:
                client, addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            self.log("\n正在关闭服务器...")
        finally:
            server.close()

if __name__ == "__main__":
    proxy = HTTPProxy()
    proxy.start()
