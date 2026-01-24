# HTTP Proxy Server

一个简单但功能强大的Python HTTP代理服务器，支持所有HTTP方法和HTTPS隧道。

## 功能特性

- 支持所有HTTP方法：GET, POST, PUT, DELETE, HEAD, OPTIONS, TRACE, CONNECT
- HTTPS隧道支持（CONNECT方法）
- 配置文件支持（JSON格式）
- 多线程处理并发连接
- 错误处理和超时机制
- 详细的日志输出

## 快速开始

### 1. 配置

编辑 `config.json` 文件来设置代理服务器的host和port：

```json
{
  "host": "0.0.0.0",
  "port": 8888
}
```

### 2. 运行代理服务器

```bash
python main.py
```

代理服务器将在配置的host和port上启动。

### 3. 配置客户端

将你的浏览器、应用程序或其他HTTP客户端配置为使用代理：

- **Host**: 127.0.0.1 (或服务器IP)
- **Port**: 8888 (或配置文件中的端口)

#### 浏览器配置示例：
- Chrome: 设置 > 系统 > 打开代理设置 > LAN设置 > 使用代理服务器
- Firefox: 设置 > 网络设置 > 设置手动代理配置

### 4. 测试

运行测试脚本验证代理功能：

```bash
python test_proxy.py
```

## 支持的请求类型

代理服务器可以处理以下类型的请求：

- **HTTP方法**: GET, POST, PUT, DELETE, HEAD, OPTIONS, TRACE
- **HTTPS**: 通过CONNECT方法建立隧道
- **自定义端口**: 支持非标准端口（如8080, 3000等）

## 架构

```
客户端 -> HTTP代理 (main.py) -> 目标服务器
    ^                           ^
    |                           |
    CONNECT隧道              直接转发
  (HTTPS)                    (HTTP)
```

## 开发

### 代码结构
- `main.py`: 主代理服务器实现
- `config.json`: 配置文件
- `test_proxy.py`: 功能测试脚本
- `AGENTS.md`: 开发指南和编码规范

### 扩展功能

你可以修改代码来添加更多功能：
- 请求过滤和修改
- 缓存机制
- 认证系统
- 日志记录到文件
- 性能监控

## 注意事项

- 这个代理服务器主要用于开发和测试目的
- 生产环境使用时请考虑安全性和性能优化
- 默认配置监听所有网络接口（0.0.0.0），生产环境请限制为特定接口

## 许可证

本项目仅用于学习和测试目的。
