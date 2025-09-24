# Levo CLI API - Schema Upload and Versioning System

## Architecture Overview

This system implements a CLI tool and API for uploading, versioning, and managing OpenAPI schemas for applications and services.

## Components

### 1. Database Layer (SQLite)
- **Applications**: Parent entities
- **Services**: Child entities under applications  
- **Schemas**: Versioned OpenAPI specs linked to applications/services
- **Schema Files**: File metadata and storage paths

### 2. API Layer (FastAPI)
- Upload schema endpoints
- Schema validation
- Version management
- Retrieval endpoints

### 3. CLI Layer (Click)
- `levo import` command
- `levo test` command
- Schema validation before upload

### 4. File Storage
- Organized by application/service
- Supports JSON and YAML formats
- Version-based file naming

## Data Flow

1. **Import Flow**:
   ```
   CLI → Validate Schema → API Upload → Database + File Storage
   ```

2. **Test Flow**:
   ```
   CLI → API Fetch Latest Schema → Execute Tests
   ```

## Directory Structure
```
├── app/
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── api/            # FastAPI endpoints
│   ├── services/       # Business logic
│   └── storage/        # File storage handler
├── cli/                # Click CLI commands
├── tests/              # Unit tests
├── storage/            # Schema file storage
└── database.db        # SQLite database
```

## Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Run the FastAPI server
python main.py
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

### 3. CLI Usage

#### Import Schema
```bash
# Import schema to application level
python levo_cli.py import --spec /path/to/openapi.json --application my-app

# Import schema to service level
python levo_cli.py import --spec /path/to/openapi.yaml --application my-app --service my-service

# Replace existing schema
python levo_cli.py import --spec /path/to/openapi.json --application my-app --replace
```

#### Test Application/Service
```bash
# Test application
python levo_cli.py test --application my-app

# Test service
python levo_cli.py test --application my-app --service my-service
```

#### List Schemas
```bash
# List all applications
python levo_cli.py list-schemas

# List schema versions for specific application
python levo_cli.py list-schemas --application my-app
```

## API Endpoints

### Schema Management
- `POST /api/v1/schemas/upload` - Upload new schema
- `GET /api/v1/schemas/latest` - Get latest schema
- `GET /api/v1/schemas/versions` - Get all versions
- `GET /api/v1/schemas/{id}/content` - Get schema content

### Application/Service Management
- `GET /api/v1/applications` - List applications
- `GET /api/v1/applications/{name}/services` - List services

## Features

✅ **Schema Upload & Validation**
- Supports JSON and YAML OpenAPI specs
- Validates schema format before upload
- Automatic file type detection

✅ **Versioning System**
- Automatic version incrementing
- Maintains schema history
- Replace existing functionality

✅ **Database Integration**
- SQLite database for metadata
- Application/Service hierarchy
- Schema versioning tracking

✅ **File Storage**
- Organized directory structure
- SHA-256 checksums for integrity
- Version-based file naming

✅ **CLI Interface**
- `levo import` command
- `levo test` command  
- User-friendly output with emojis

✅ **REST API**
- FastAPI with automatic docs
- Comprehensive error handling
- CORS support

✅ **Unit Tests**
- Comprehensive test coverage
- Application and service testing
- Schema validation testing

## Testing

Run the unit tests:

```bash
pytest tests/ -v
```

## Example Usage

1. **Start the API server:**
   ```bash
   python main.py
   ```

2. **Import a schema:**
   ```bash
   python levo_cli.py import --spec examples/openapi.json --application crapi
   ```

3. **Test the application:**
   ```bash
   python levo_cli.py test --application crapi
   ```

4. **View all applications:**
   ```bash
   python levo_cli.py list-schemas
   ```

## Sample OpenAPI Schemas

You can test with these public schemas:
- https://github.com/levoai/demo-apps/blob/main/crAPI/api-specs/openapi.json
- https://github.com/levoai/demo-apps/blob/main/MalSchema/app/openapi.yaml

## System Design Details

### Database Schema
- **Applications** table: stores application metadata
- **Services** table: stores service metadata (linked to applications)
- **Schemas** table: stores schema metadata with versioning info

### File Organization
```
storage/
├── application1/
│   ├── schema_v1.json
│   ├── schema_v2.yaml
│   └── service1/
│       ├── service_schema_v1.json
│       └── service_schema_v2.yaml
└── application2/
    └── schema_v1.json
```

### Error Handling
- Comprehensive validation at API and CLI levels
- User-friendly error messages
- Proper HTTP status codes

### Security Considerations
- File type validation
- Schema content validation
- Path traversal protection
- Input sanitization

## Development

The system is built with:
- **FastAPI** for the REST API
- **SQLAlchemy** for database ORM
- **Click** for CLI interface
- **Pydantic** for data validation
- **pytest** for testing

## Future Enhancements

- Advanced testing capabilities
- Schema comparison between versions
- API documentation generation
- Authentication and authorization
- Schema migration tools
