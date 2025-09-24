from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class FileFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"

# Base schemas
class ApplicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class Application(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

# Service schemas
class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ServiceCreate(ServiceBase):
    application_id: int

class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class Service(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

# Schema schemas
class SchemaBase(BaseModel):
    file_name: str
    file_format: FileFormat

class SchemaCreate(SchemaBase):
    application_id: int
    service_id: Optional[int] = None

class SchemaUpload(BaseModel):
    application: str = Field(..., min_length=1)
    service: Optional[str] = None
    replace_existing: bool = False

class SchemaInfo(SchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    file_path: str
    file_size: int
    checksum: str
    is_latest: bool
    application_id: int
    service_id: Optional[int]
    created_at: datetime

class SchemaResponse(BaseModel):
    schema_info: SchemaInfo
    application: Application
    service: Optional[Service] = None

# API Response schemas
class UploadResponse(BaseModel):
    success: bool
    message: str
    schema_info: Optional[SchemaInfo] = None
    version: Optional[int] = None

class ValidationError(BaseModel):
    field: str
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[List[ValidationError]] = None
