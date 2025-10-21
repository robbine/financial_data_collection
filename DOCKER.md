# Docker 部署指南

本文档详细说明如何使用Docker部署和运行Financial Data Collector系统。

## 🚀 快速开始

### 1. 环境准备
确保已安装以下软件：
- Docker (20.10+)
- Docker Compose (2.0+)

### 2. 克隆项目
```bash
git clone <repository-url>
cd financial_data_collection
```

### 3. 配置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑环境变量文件
nano .env
```

### 4. 运行初始设置
```bash
# 使用Makefile (推荐)
make setup

# 或直接运行脚本
./scripts/docker-setup.sh
```

### 5. 启动服务
```bash
# 启动所有服务
make up

# 或使用docker-compose
docker-compose up -d
```

## 📊 服务架构

### 核心服务
- **financial-data-collector**: 主应用程序
- **postgres**: PostgreSQL数据库
- **redis**: Redis缓存
- **nginx**: 反向代理

### 可选服务
- **mongodb**: 文档数据库
- **elasticsearch**: 搜索引擎
- **kibana**: 数据可视化
- **prometheus**: 监控系统
- **grafana**: 监控仪表板

### 开发工具
- **jupyter**: Jupyter Notebook
- **pgadmin**: PostgreSQL管理界面
- **redis-commander**: Redis管理界面

## 🔧 环境配置

### 开发环境
```bash
# 启动开发环境
make dev

# 或使用docker-compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 生产环境
```bash
# 启动生产环境
make prod

# 或使用docker-compose
docker-compose up -d
```

## 📋 常用命令

### 基本操作
```bash
# 查看服务状态
make status
docker-compose ps

# 查看日志
make logs
docker-compose logs -f

# 重启服务
make restart
docker-compose restart

# 停止服务
make down
docker-compose down
```

### 开发操作
```bash
# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint

# 查看应用日志
make app-logs
```

### 数据库操作
```bash
# 连接数据库
make db-shell

# 备份数据库
make db-backup

# 恢复数据库
make db-restore
```

### 监控操作
```bash
# 打开监控界面
make prometheus
make grafana
make pgadmin

# 检查服务健康状态
make health
```

## 🌐 服务访问

### 主要服务
| 服务 | 地址 | 用户名/密码 | 说明 |
|------|------|-------------|------|
| 应用 | http://localhost:8000 | - | 主应用程序 |
| API文档 | http://localhost:8000/docs | - | Swagger文档 |
| 健康检查 | http://localhost:8000/health | - | 健康状态 |

### 监控服务
| 服务 | 地址 | 用户名/密码 | 说明 |
|------|------|-------------|------|
| Grafana | http://localhost:3000 | admin/admin | 监控仪表板 |
| Prometheus | http://localhost:9090 | - | 指标收集 |
| pgAdmin | http://localhost:5050 | admin@fdc.local/admin | 数据库管理 |

### 开发工具
| 服务 | 地址 | 用户名/密码 | 说明 |
|------|------|-------------|------|
| Jupyter | http://localhost:8888 | token: dev_token_123 | 数据分析 |
| Redis Commander | http://localhost:8081 | - | Redis管理 |

## 🔧 配置说明

### 环境变量
主要环境变量配置在 `.env` 文件中：

```bash
# 数据库配置
DATABASE_URL=postgresql://fdc_user:fdc_password@postgres:5432/fdc_db
REDIS_URL=redis://redis:6379/0

# API密钥
API_KEY=your_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key

# 安全配置
ENCRYPTION_KEY=your_32_character_encryption_key_here
```

### 配置文件
- `config/development.yaml`: 开发环境配置
- `config/production.yaml`: 生产环境配置
- `docker-compose.yml`: 生产环境Docker配置
- `docker-compose.dev.yml`: 开发环境Docker配置

## 🐛 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :8000

# 修改端口配置
# 编辑 docker-compose.yml 中的 ports 配置
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready -U fdc_user -d fdc_db

# 查看数据库日志
docker-compose logs postgres
```

#### 3. 应用启动失败
```bash
# 查看应用日志
docker-compose logs financial-data-collector

# 检查配置文件
docker-compose exec financial-data-collector cat /app/config/production.yaml
```

#### 4. 内存不足
```bash
# 检查Docker资源使用
docker stats

# 清理未使用的资源
make clean
docker system prune -f
```

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs financial-data-collector
docker-compose logs postgres
docker-compose logs redis

# 实时查看日志
docker-compose logs -f
```

## 🔒 安全配置

### 生产环境安全
1. **更改默认密码**
   ```bash
   # 编辑 .env 文件
   POSTGRES_PASSWORD=your_secure_password
   REDIS_PASSWORD=your_secure_password
   ```

2. **配置SSL证书**
   ```bash
   # 将SSL证书放置在 nginx/ssl/ 目录
   nginx/ssl/cert.pem
   nginx/ssl/key.pem
   ```

3. **限制网络访问**
   ```yaml
   # 在 docker-compose.yml 中配置网络
   networks:
     fdc-network:
       driver: bridge
       internal: true  # 内部网络
   ```

### 防火墙配置
```bash
# 只开放必要端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 5432/tcp  # 数据库端口不对外开放
```

## 📈 性能优化

### 资源限制
```yaml
# 在 docker-compose.yml 中配置资源限制
services:
  financial-data-collector:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### 数据库优化
```yaml
# PostgreSQL 配置优化
postgres:
  environment:
    - POSTGRES_SHARED_BUFFERS=256MB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
    - POSTGRES_MAINTENANCE_WORK_MEM=64MB
```

## 🔄 备份和恢复

### 数据库备份
```bash
# 自动备份
make db-backup

# 手动备份
docker-compose exec postgres pg_dump -U fdc_user fdc_db > backup.sql
```

### 数据恢复
```bash
# 恢复数据库
make db-restore

# 手动恢复
docker-compose exec -T postgres psql -U fdc_user -d fdc_db < backup.sql
```

### 完整备份
```bash
# 备份所有数据
tar -czf fdc-backup-$(date +%Y%m%d).tar.gz data/ logs/ config/
```

## 🚀 部署到生产环境

### 1. 准备生产环境
```bash
# 配置生产环境变量
cp env.example .env.production
# 编辑 .env.production 文件

# 配置SSL证书
# 将证书放置在 nginx/ssl/ 目录
```

### 2. 启动生产服务
```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml --env-file .env.production up -d
```

### 3. 配置监控
```bash
# 访问监控界面
# Grafana: http://your-domain:3000
# Prometheus: http://your-domain:9090
```

### 4. 设置自动启动
```bash
# 配置systemd服务
sudo systemctl enable docker
sudo systemctl start docker
```

## 📚 更多资源

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [PostgreSQL Docker镜像](https://hub.docker.com/_/postgres)
- [Redis Docker镜像](https://hub.docker.com/_/redis)
- [Grafana Docker镜像](https://hub.docker.com/r/grafana/grafana)
