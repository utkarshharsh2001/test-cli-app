from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.database import get_db
from app.services.schema_service import SchemaService
from app.storage.storage_service import StorageService
from app.schemas.schemas import (
    SchemaUpload, UploadResponse, SchemaResponse, SchemaInfo, ErrorResponse
)

# Initialize services
storage_service = StorageService()
schema_service = SchemaService(storage_service)

router = APIRouter(prefix="/api/v1", tags=["schemas"])

@router.post("/schemas/upload", response_model=UploadResponse)
async def upload_schema(
    file: UploadFile = File(...),
    application: str = Form(...),
    service: Optional[str] = Form(None),
    replace_existing: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Upload OpenAPI schema file"""

    # Validate file type
    if not file.filename.lower().endswith(('.json', '.yaml', '.yml')):
        return UploadResponse(
            success=False,
            message="Only JSON and YAML files are supported"
        )

    # Read file content
    try:
        content = await file.read()
        if len(content) == 0:
            return UploadResponse(
                success=False,
                message="File is empty"
            )
    except Exception as e:
        return UploadResponse(
            success=False,
            message=f"Error reading file: {str(e)}"
        )

    # Create upload data
    upload_data = SchemaUpload(
        application=application,
        service=service,
        replace_existing=replace_existing
    )

    # Process upload
    result = await schema_service.upload_schema(db, content, file.filename, upload_data)
    return result

@router.get("/schemas/latest", response_model=SchemaResponse)
async def get_latest_schema(
    application: str,
    service: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get the latest schema for an application/service"""

    result = schema_service.get_latest_schema(db, application, service)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No schema found for application '{application}'" +
                   (f" and service '{service}'" if service else "")
        )

    return result

@router.get("/schemas/versions", response_model=List[SchemaInfo])
async def get_schema_versions(
    application: str,
    service: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all versions of schema for an application/service"""

    versions = schema_service.get_schema_versions(db, application, service)
    if not versions:
        raise HTTPException(
            status_code=404,
            detail=f"No schemas found for application '{application}'" +
                   (f" and service '{service}'" if service else "")
        )

    return versions

@router.get("/schemas/{schema_id}/content")
async def get_schema_content(
    schema_id: int,
    db: Session = Depends(get_db)
):
    """Get the content of a specific schema version"""

    from app.models.database import Schema
    schema_record = db.query(Schema).filter(Schema.id == schema_id).first()

    if not schema_record:
        raise HTTPException(status_code=404, detail="Schema not found")

    try:
        schema_info = SchemaInfo.model_validate(schema_record)
        content = await schema_service.get_schema_content(schema_info)
        return {
            "schema_info": schema_info,
            "content": content
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading schema content: {str(e)}"
        )

@router.get("/applications")
async def list_applications(db: Session = Depends(get_db)):
    """List all applications"""
    from app.models.database import Application
    applications = db.query(Application).all()
    return [{"id": app.id, "name": app.name, "description": app.description} for app in applications]

@router.get("/applications/{application_name}/services")
async def list_services(application_name: str, db: Session = Depends(get_db)):
    """List all services for an application"""
    from app.models.database import Application, Service

    application = db.query(Application).filter(Application.name == application_name).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    services = db.query(Service).filter(Service.application_id == application.id).all()
    return [{"id": svc.id, "name": svc.name, "description": svc.description} for svc in services]
