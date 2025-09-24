import pytest
import tempfile
import json
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, get_db
from main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_openapi_json():
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "A test API for unit testing"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/users/{id}": {
                "get": {
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"},
                        "404": {"description": "Not found"}
                    }
                }
            }
        }
    }

@pytest.fixture
def sample_openapi_yaml():
    return """
openapi: 3.0.1
info:
  title: Test API YAML
  version: 1.0.0
  description: A test API in YAML format
paths:
  /products:
    get:
      summary: Get products
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
  /products/{id}:
    get:
      summary: Get product by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
        '404':
          description: Not found
    """

class TestSchemaUpload:

    def test_upload_json_schema_application_only(self, client, sample_openapi_json):
        """Test uploading JSON schema to application level"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_openapi_json, f)
            f.flush()

            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/v1/schemas/upload",
                    files={"file": ("test_schema.json", upload_file, "application/json")},
                    data={
                        "application": "test-app",
                        "replace_existing": False
                    }
                )

        os.unlink(f.name)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["version"] == 1
        assert "test-app" in result["message"]
        assert result["schema_info"]["file_format"] == "json"

    def test_upload_yaml_schema_with_service(self, client, sample_openapi_yaml):
        """Test uploading YAML schema to application with service"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(sample_openapi_yaml)
            f.flush()

            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/v1/schemas/upload",
                    files={"file": ("test_schema.yaml", upload_file, "application/x-yaml")},
                    data={
                        "application": "test-app-2",
                        "service": "test-service",
                        "replace_existing": False
                    }
                )

        os.unlink(f.name)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["version"] == 1
        assert "test-app-2/test-service" in result["message"]
        assert result["schema_info"]["file_format"] == "yaml"

    def test_upload_invalid_schema(self, client):
        """Test uploading invalid schema file"""
        # Valid JSON but invalid OpenAPI schema (missing required fields)
        invalid_schema = {
            "invalid": "schema",
            "missing": "required OpenAPI fields",
            "info": {
                "title": "Invalid API"
            }
            # Missing "openapi" version and "paths" fields
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_schema, f)
            f.flush()

            with open(f.name, 'rb') as upload_file:
                response = client.post(
                    "/api/v1/schemas/upload",
                    files={"file": ("invalid.json", upload_file, "application/json")},
                    data={
                        "application": "test-app-invalid",
                        "replace_existing": False
                    }
                )

        os.unlink(f.name)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is False
        # Update assertion to match the actual error message format
        assert "validation failed" in result["message"].lower() or "missing" in result["message"].lower()

    def test_version_increment(self, client, sample_openapi_json):
        """Test that schema versions increment correctly"""
        # Upload first version
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_openapi_json, f)
            f.flush()

            with open(f.name, 'rb') as upload_file:
                response1 = client.post(
                    "/api/v1/schemas/upload",
                    files={"file": ("schema_v1.json", upload_file, "application/json")},
                    data={
                        "application": "version-test-app",
                        "replace_existing": False
                    }
                )

        # Upload second version
        sample_openapi_json["info"]["version"] = "2.0.0"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump(sample_openapi_json, f2)
            f2.flush()

            with open(f2.name, 'rb') as upload_file:
                response2 = client.post(
                    "/api/v1/schemas/upload",
                    files={"file": ("schema_v2.json", upload_file, "application/json")},
                    data={
                        "application": "version-test-app",
                        "replace_existing": False
                    }
                )

        os.unlink(f.name)
        os.unlink(f2.name)

        assert response1.status_code == 200
        assert response2.status_code == 200

        result1 = response1.json()
        result2 = response2.json()

        assert result1["version"] == 1
        assert result2["version"] == 2

class TestSchemaRetrieval:

    def test_get_latest_schema(self, client):
        """Test retrieving the latest schema"""
        response = client.get("/api/v1/schemas/latest?application=test-app")

        assert response.status_code == 200
        result = response.json()
        assert result["application"]["name"] == "test-app"
        assert result["schema_info"]["is_latest"] is True

    def test_get_schema_versions(self, client):
        """Test retrieving all schema versions"""
        response = client.get("/api/v1/schemas/versions?application=version-test-app")

        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 2
        assert versions[0]["version"] == 2  # Latest first
        assert versions[1]["version"] == 1

    def test_get_nonexistent_schema(self, client):
        """Test retrieving schema for non-existent application"""
        response = client.get("/api/v1/schemas/latest?application=nonexistent-app")

        assert response.status_code == 404

class TestApplicationAndServiceListing:

    def test_list_applications(self, client):
        """Test listing all applications"""
        response = client.get("/api/v1/applications")

        assert response.status_code == 200
        apps = response.json()
        app_names = [app["name"] for app in apps]

        assert "test-app" in app_names
        assert "test-app-2" in app_names
        assert "version-test-app" in app_names

    def test_list_services(self, client):
        """Test listing services for an application"""
        response = client.get("/api/v1/applications/test-app-2/services")

        assert response.status_code == 200
        services = response.json()
        assert len(services) == 1
        assert services[0]["name"] == "test-service"
