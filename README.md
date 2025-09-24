# Levo CLI API - Schema Upload and Versioning System

## Architecture Overview

This system implements a CLI tool and API for uploading, versioning, and managing OpenAPI schemas for applications and services.

## Components

- **Database Layer (SQLite)**: Applications, Services, and versioned Schemas
- **API Layer (FastAPI)**: Upload, validation, and retrieval endpoints
- **CLI Layer (Click)**: `levo import` and `levo test` commands
- **File Storage**: Organized by application/service with version-based naming
- **Docker Support**: Containerized deployment with automated testing

## Directory Structure
```
├── app/                # FastAPI application
├── cli/                # Click CLI commands
├── tests/              # Unit tests
├── test-inputs/        # CLI test input files
├── storage/            # Schema file storage (git ignored)
├── Dockerfile          # Docker configuration
└── docker-compose.yml  # Docker Compose setup
```

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
python main.py
```
API available at `http://localhost:8000` with docs at `http://localhost:8000/docs`

### Docker Deployment
```bash
# Build and start with Docker Compose
docker-compose up
```
API available at `http://localhost:8000` with health check at `http://localhost:8000/health`

## CLI Usage

### Import Schema
```bash
# Import to application
python cli/levo.py import --spec /path/to/openapi.json --application my-app

# Import to service
python cli/levo.py import --spec /path/to/openapi.yaml --application my-app --service my-service

# Replace existing
python cli/levo.py import --spec /path/to/openapi.json --application my-app --replace
```

### Test CLI in Docker
```bash
# Access container
docker exec -it <container_name> /bin/bash

# Run tests
bash test-inputs/test-cli-commands.sh
```

## API Endpoints

- `POST /api/v1/schemas/upload` - Upload new schema
- `GET /api/v1/schemas/latest` - Get latest schema
- `GET /api/v1/schemas/versions` - Get all versions
- `GET /health` - Container health status

## Features

**🗄️ Schema Management**
- Multi-format support for JSON and YAML OpenAPI specifications
- Automatic validation and version control with history tracking
- File integrity checks using SHA-256 checksums

**🖥️ Command Line Interface** 
- Intuitive `levo import` and `levo test` commands
- Clean output with emojis and descriptive error handling
- Flexible options for application and service management

**🌐 REST API**
- High-performance FastAPI with interactive documentation
- CORS support and built-in health monitoring
- Auto-generated Swagger/OpenAPI docs

**🐳 Docker Integration**
- Complete containerized deployment with Docker Compose
- Automated testing during build process
- Volume management and health check monitoring

**📁 File Organization**
- Hierarchical Application → Service → Schema structure  
- Smart version-based naming and path safety protection
- Automatic cleanup of duplicates and outdated files

**🧪 Quality Assurance**
- Comprehensive pytest coverage with integration testing
- Docker testing environment with CI/CD readiness
- Build fails if tests don't pass

## Testing

### Local Testing
```bash
python -m pytest
```
All tests should pass. You may see some deprecation warnings which are expected with newer Python/package versions.

### Docker Testing
Tests run automatically during Docker build - build fails if tests fail.

## Example Usage

```bash
# Start API
python main.py

# Import schema
python cli/levo.py import --spec test-inputs/sample_ecommerce_api.json --application crapi

# Test with Docker
docker-compose up
docker exec -it <container_name> /bin/bash
bash test-inputs/test-cli-commands.sh
```

## Docker Commands

```bash
# Build and run
docker-compose up

# Manual build
docker build -t levo-cli-api .

# Access container
docker exec -it <container_name> /bin/bash

# Stop containers
docker-compose down
```

## Sample Test Files

Test files in `test-inputs/` directory:
- `sample_ecommerce_api.json`
- `sample_ecommerce_api_v2.yaml`
- `payment_service_api.json`

## Tech Stack

- **FastAPI** - REST API
- **SQLAlchemy** - Database ORM
- **Click** - CLI interface
- **Docker** - Containerization
- **pytest** - Testing
