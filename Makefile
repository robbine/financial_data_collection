# Financial Data Collector Makefile
# Provides convenient commands for Docker operations

.PHONY: help build up down restart logs clean dev prod test lint format

# Default target
help:
	@echo "Financial Data Collector - Available Commands:"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs"
	@echo "  make clean          - Clean up containers and volumes"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make dev            - Start development environment"
	@echo "  make prod           - Start production environment"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linting"
	@echo "  make format         - Format code"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  make prometheus      - Open Prometheus"
	@echo "  make grafana         - Open Grafana"
	@echo "  make pgadmin         - Open pgAdmin"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  make db-shell       - Connect to PostgreSQL"
	@echo "  make db-backup      - Backup database"
	@echo "  make db-restore     - Restore database"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make setup          - Initial setup"
	@echo "  make update         - Update dependencies"
	@echo "  make security       - Security scan"

# Docker commands
build:
	@echo "🔨 Building Docker images..."
	docker-compose build

up:
	@echo "🚀 Starting services..."
	docker-compose up -d

down:
	@echo "🛑 Stopping services..."
	docker-compose down

restart:
	@echo "🔄 Restarting services..."
	docker-compose restart

logs:
	@echo "📋 Viewing logs..."
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Environment-specific commands
dev:
	@echo "🔧 Starting development environment..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

prod:
	@echo "🏭 Starting production environment..."
	docker-compose up -d

# Development commands
test:
	@echo "🧪 Running tests..."
	docker compose -f docker-compose.dev.yml exec financial-data-collector-dev pytest tests/ -v

lint:
	@echo "🔍 Running linting..."
	docker compose -f docker-compose.dev.yml exec financial-data-collector-dev flake8 src/
	docker compose -f docker-compose.dev.yml exec financial-data-collector-dev mypy src/

format:
	@echo "✨ Formatting code..."
	docker compose -f docker-compose.dev.yml exec financial-data-collector-dev black src/
	docker compose -f docker-compose.dev.yml exec financial-data-collector-dev isort src/

# Crawl4AI commands
install-crawl4ai:
	@echo "🕷️  Installing Crawl4AI..."
	./scripts/install-crawl4ai.sh

test-crawl4ai:
	@echo "🧪 Testing Crawl4AI..."
	python examples/crawl4ai_demo.py

crawl4ai-setup:
	@echo "⚙️  Setting up Crawl4AI..."
	python -m crawl4ai.setup

# WebCrawler integration tests
test-webcrawler:
	@echo "🧪 Testing WebCrawler integration..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev python tests/test_webcrawler.py

test-webcrawler-simple:
	@echo "🧪 Running simple WebCrawler test..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev python tests/test_webcrawler.py --simple

test-webcrawler-verbose:
	@echo "🧪 Running verbose WebCrawler test..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev python tests/test_webcrawler.py --verbose

# Message Queue tests
test-message-queue:
	@echo "🧪 Testing Message Queue integration..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev python examples/message_queue_demo.py

# Start message queue services
start-mq:
	@echo "🚀 Starting message queue services..."
	docker compose -f docker-compose.dev.yml up -d redis celery-worker celery-beat

stop-mq:
	@echo "🛑 Stopping message queue services..."
	docker compose -f docker-compose.dev.yml stop redis celery-worker celery-beat

# Monitor message queue
monitor-mq:
	@echo "📊 Message Queue Status:"
	@echo "Redis Commander: http://localhost:8081"
	@echo "Task API: http://localhost:8000/api/tasks/"
	@echo "Crawler API: http://localhost:8000/api/crawler/"
	@echo ""
	@echo "Worker logs:"
	docker compose -f docker-compose.dev.yml logs celery-worker --tail=20

# Scale workers
scale-workers:
	@echo "📈 Scaling workers to $(WORKERS) instances..."
	docker compose -f docker-compose.dev.yml up -d --scale celery-worker=$(WORKERS)

# Test suites
test-all:
	@echo "🧪 Running all test suites..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/ -v

test-unit:
	@echo "🧪 Running unit tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_message_queue.py -v

test-api:
	@echo "🧪 Running API integration tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_api_integration.py -v

test-e2e:
	@echo "🧪 Running end-to-end tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_e2e_message_queue.py -v -m integration

test-performance:
	@echo "🧪 Running performance tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_performance.py -v -s

# Test with coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/ --cov=src --cov-report=html --cov-report=term

# Test specific components
test-crawler:
	@echo "🧪 Testing crawler components..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_webcrawler.py -v

test-enhanced-crawler:
	@echo "🧪 Testing Enhanced WebCrawler..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_enhanced_webcrawler.py -v

test-enhanced-crawler-simple:
	@echo "🧪 Running simple Enhanced WebCrawler test..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_enhanced_webcrawler.py::TestEnhancedWebCrawler -v

test-enhanced-crawler-advanced:
	@echo "🧪 Testing Enhanced WebCrawler advanced features..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_enhanced_webcrawler.py::TestEnhancedWebCrawlerAdvancedFeatures -v

test-enhanced-crawler-integration:
	@echo "🧪 Testing Enhanced WebCrawler integration..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_enhanced_webcrawler.py::TestEnhancedWebCrawlerIntegration -v

test-enhanced-crawler-no-proxy:
	@echo "🧪 Testing Enhanced WebCrawler without proxy services..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_enhanced_webcrawler.py::TestEnhancedWebCrawlerNoProxy -v

test-tasks:
	@echo "🧪 Testing task management..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_message_queue.py::TestTaskManager -v

test-celery:
	@echo "🧪 Testing Celery tasks..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_message_queue.py::TestCeleryTasks -v

# Load testing
test-load:
	@echo "🧪 Running load tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_performance.py::TestLoadPerformance -v -s

test-stress:
	@echo "🧪 Running stress tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_performance.py::TestStressPerformance -v -s

# Test with specific markers
test-integration:
	@echo "🧪 Running integration tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/ -m integration -v

test-slow:
	@echo "🧪 Running slow tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/ -m slow -v

# Test debugging
test-debug:
	@echo "🐛 Running tests in debug mode..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/ -v -s --tb=long

test-failed:
	@echo "🔄 Running only failed tests..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/ --lf -v

# Test reports
test-report:
	@echo "📊 Generating test report..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/ --html=reports/test_report.html --self-contained-html

# Clean test artifacts
clean-tests:
	@echo "🧹 Cleaning test artifacts..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev rm -rf .pytest_cache htmlcov reports


# Enhanced crawler commands
test-enhanced-crawler:
	@echo "🚀 Testing Enhanced Crawler..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_enhanced_webcrawler.py -v

test-advanced-crawler:
	@echo "🧪 Testing Advanced Crawler Components..."
	docker compose -f docker-compose.dev.yml run --rm financial-data-collector-dev pytest tests/test_advanced_crawler_simple.py -v

demo-enhanced:
	@echo "🎯 Running Enhanced Crawler Demo..."
	python examples/enhanced_crawler_demo.py

setup-proxies:
	@echo "🔄 Setting up proxy configuration..."
	@echo "Please configure proxies in config/enhanced_crawler.yaml"

setup-captcha:
	@echo "🔐 Setting up captcha solving..."
	@echo "Please configure captcha API keys in .env file"

# Volcano Engine LLM commands
test-volc-llm:
	@echo "🌋 Testing Volcano Engine LLM..."
	python examples/volc_llm_demo.py

demo-volc-llm:
	@echo "🎯 Running Volcano Engine LLM Demo..."
	python examples/volc_llm_demo.py

setup-volc-llm:
	@echo "🌋 Setting up Volcano Engine LLM..."
	@echo "Please configure VOLC_API_KEY and VOLC_BASE_URL in .env file"
	@echo "Example:"
	@echo "  VOLC_API_KEY=your_volc_api_key_here"
	@echo "  VOLC_BASE_URL=https://ark.cn-beijing.volces.com/api/v3"

# Custom model commands
test-custom-model:
	@echo "🎯 Testing Custom Model..."
	python examples/custom_model_demo.py

demo-custom-model:
	@echo "🚀 Running Custom Model Demo..."
	python examples/custom_model_demo.py

setup-custom-model:
	@echo "🎯 Setting up Custom Model..."
	@echo "Your custom model: ep-20250725215501-7zrfm"
	@echo "Please configure in .env file:"
	@echo "  VOLC_API_KEY=your_volc_api_key_here"
	@echo "  VOLC_BASE_URL=your_volc_base_url_here"
	@echo "  VOLC_MODEL=ep-20250725215501-7zrfm"

# Monitoring commands
prometheus:
	@echo "📊 Opening Prometheus..."
	@echo "URL: http://localhost:9090"
	@command -v open >/dev/null 2>&1 && open http://localhost:9090 || echo "Please open http://localhost:9090 in your browser"

grafana:
	@echo "📊 Opening Grafana..."
	@echo "URL: http://localhost:3000 (admin/admin)"
	@command -v open >/dev/null 2>&1 && open http://localhost:3000 || echo "Please open http://localhost:3000 in your browser"

pgadmin:
	@echo "🗄️  Opening pgAdmin..."
	@echo "URL: http://localhost:5050 (admin@fdc.local/admin)"
	@command -v open >/dev/null 2>&1 && open http://localhost:5050 || echo "Please open http://localhost:5050 in your browser"

# Database commands
db-shell:
	@echo "🗄️  Connecting to PostgreSQL..."
	docker-compose exec postgres psql -U fdc_user -d fdc_db

db-backup:
	@echo "💾 Backing up database..."
	docker-compose exec postgres pg_dump -U fdc_user fdc_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	@echo "📥 Restoring database..."
	@read -p "Enter backup file path: " file; \
	docker-compose exec -T postgres psql -U fdc_user -d fdc_db < $$file

# Maintenance commands
setup:
	@echo "🚀 Running initial setup..."
	./scripts/docker-setup.sh

update:
	@echo "📦 Updating dependencies..."
	docker-compose build --no-cache
	docker-compose pull

security:
	@echo "🔒 Running security scan..."
	docker run --rm -v $(PWD):/app securecodewarrior/docker-security-scan:latest /app

# Service-specific commands
app-logs:
	@echo "📱 Viewing application logs..."
	docker-compose logs -f financial-data-collector

db-logs:
	@echo "🗄️  Viewing database logs..."
	docker-compose logs -f postgres

redis-logs:
	@echo "🔴 Viewing Redis logs..."
	docker-compose logs -f redis

# Health checks
health:
	@echo "🏥 Checking service health..."
	@echo "Application: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || echo 'DOWN')"
	@echo "PostgreSQL: $$(docker-compose exec -T postgres pg_isready -U fdc_user -d fdc_db > /dev/null 2>&1 && echo 'UP' || echo 'DOWN')"
	@echo "Redis: $$(docker-compose exec -T redis redis-cli ping > /dev/null 2>&1 && echo 'UP' || echo 'DOWN')"
	@echo "Prometheus: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:9090 || echo 'DOWN')"
	@echo "Grafana: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo 'DOWN')"

# Status command
status:
	@echo "📊 Service Status:"
	docker-compose ps

# Quick start for development
quick-start:
	@echo "⚡ Quick start for development..."
	make setup
	make dev
	@echo "🎉 Development environment is ready!"
	@echo "Application: http://localhost:8000"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
