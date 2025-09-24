import os
import json
import yaml
import hashlib
import aiofiles
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from jsonschema import validate, ValidationError as JsonSchemaValidationError

class StorageService:
    def __init__(self, base_storage_path: str = "./storage"):
        self.base_path = Path(base_storage_path)
        self.base_path.mkdir(exist_ok=True)

    def _get_storage_path(self, application: str, service: Optional[str] = None) -> Path:
        """Generate storage path for application/service"""
        if service:
            return self.base_path / application / service
        return self.base_path / application

    def _generate_filename(self, original_name: str, version: int, file_format: str) -> str:
        """Generate versioned filename"""
        name_without_ext = Path(original_name).stem
        return f"{name_without_ext}_v{version}.{file_format}"

    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA-256 checksum of content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def _validate_openapi_schema(self, content: Dict[Any, Any]) -> Tuple[bool, Optional[str]]:
        """Validate if content is a valid OpenAPI schema"""
        try:
            # Check for required OpenAPI fields
            if "openapi" not in content and "swagger" not in content:
                return False, "Missing 'openapi' or 'swagger' field"

            if "info" not in content:
                return False, "Missing 'info' field"

            if "paths" not in content:
                return False, "Missing 'paths' field"

            # Basic version check
            if "openapi" in content:
                version = content["openapi"]
                if not version.startswith(("3.", "2.")):
                    return False, f"Unsupported OpenAPI version: {version}"

            return True, None
        except Exception as e:
            return False, f"Schema validation error: {str(e)}"

    async def parse_schema_file(self, file_content: bytes, filename: str) -> Tuple[Dict[Any, Any], str]:
        """Parse JSON or YAML schema file"""
        try:
            content_str = file_content.decode('utf-8')
            file_ext = Path(filename).suffix.lower()

            if file_ext == '.json':
                content = json.loads(content_str)
                return content, 'json'
            elif file_ext in ['.yaml', '.yml']:
                content = yaml.safe_load(content_str)
                return content, 'yaml'
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except UnicodeDecodeError:
            raise ValueError("File must be UTF-8 encoded")

    async def validate_schema(self, content: Dict[Any, Any]) -> Tuple[bool, Optional[str]]:
        """Validate OpenAPI schema content"""
        return self._validate_openapi_schema(content)

    async def save_schema(
        self,
        content: Dict[Any, Any],
        application: str,
        service: Optional[str],
        filename: str,
        version: int,
        file_format: str
    ) -> Tuple[str, str, int]:
        """Save schema file and return path, checksum, and size"""

        # Create directory structure
        storage_path = self._get_storage_path(application, service)
        storage_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with version
        versioned_filename = self._generate_filename(filename, version, file_format)
        file_path = storage_path / versioned_filename

        # Convert content to string based on format
        if file_format == 'json':
            content_str = json.dumps(content, indent=2)
        else:  # yaml
            content_str = yaml.dump(content, default_flow_style=False)

        # Calculate checksum and size
        checksum = self._calculate_checksum(content_str)
        file_size = len(content_str.encode())

        # Save file
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content_str)

        return str(file_path), checksum, file_size

    async def load_schema(self, file_path: str) -> Dict[Any, Any]:
        """Load schema from file path"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content_str = await f.read()

            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.json':
                return json.loads(content_str)
            else:  # yaml
                return yaml.safe_load(content_str)

        except FileNotFoundError:
            raise ValueError(f"Schema file not found: {file_path}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Error parsing schema file: {str(e)}")

    def delete_schema_file(self, file_path: str) -> bool:
        """Delete schema file"""
        try:
            Path(file_path).unlink()
            return True
        except FileNotFoundError:
            return False
