from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List, Tuple, Dict, Any
from app.models.database import Application, Service, Schema
from app.storage.storage_service import StorageService
from app.schemas.schemas import (
    SchemaUpload, UploadResponse, SchemaResponse, SchemaInfo
)

class SchemaService:
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service

    def get_or_create_application(self, db: Session, name: str) -> Application:
        """Get existing application or create new one"""
        app = db.query(Application).filter(Application.name == name).first()
        if not app:
            app = Application(name=name)
            db.add(app)
            db.commit()
            db.refresh(app)
        return app

    def get_or_create_service(self, db: Session, name: str, application_id: int) -> Service:
        """Get existing service or create new one"""
        service = db.query(Service).filter(
            and_(Service.name == name, Service.application_id == application_id)
        ).first()
        if not service:
            service = Service(name=name, application_id=application_id)
            db.add(service)
            db.commit()
            db.refresh(service)
        return service

    def get_next_version(self, db: Session, application_id: int, service_id: Optional[int] = None) -> int:
        """Get the next version number for schema"""
        query = db.query(Schema).filter(Schema.application_id == application_id)
        if service_id:
            query = query.filter(Schema.service_id == service_id)
        else:
            query = query.filter(Schema.service_id.is_(None))

        latest_schema = query.order_by(desc(Schema.version)).first()
        return (latest_schema.version + 1) if latest_schema else 1

    def mark_previous_versions_as_old(self, db: Session, application_id: int, service_id: Optional[int] = None):
        """Mark all previous versions as not latest"""
        query = db.query(Schema).filter(
            and_(Schema.application_id == application_id, Schema.is_latest == True)
        )
        if service_id:
            query = query.filter(Schema.service_id == service_id)
        else:
            query = query.filter(Schema.service_id.is_(None))

        query.update({"is_latest": False})
        db.commit()

    async def upload_schema(
        self,
        db: Session,
        file_content: bytes,
        filename: str,
        upload_data: SchemaUpload
    ) -> UploadResponse:
        """Upload and process schema file"""
        try:
            # Parse and validate schema file
            schema_content, file_format = await self.storage.parse_schema_file(file_content, filename)
            is_valid, error_msg = await self.storage.validate_schema(schema_content)

            if not is_valid:
                return UploadResponse(
                    success=False,
                    message=f"Schema validation failed: {error_msg}"
                )

            # Get or create application and service
            application = self.get_or_create_application(db, upload_data.application)
            service = None
            if upload_data.service:
                service = self.get_or_create_service(db, upload_data.service, application.id)

            service_id = service.id if service else None

            # Handle replace existing logic
            if upload_data.replace_existing:
                self.mark_previous_versions_as_old(db, application.id, service_id)
                version = self.get_next_version(db, application.id, service_id)
            else:
                version = self.get_next_version(db, application.id, service_id)

            # Save schema file
            file_path, checksum, file_size = await self.storage.save_schema(
                schema_content,
                upload_data.application,
                upload_data.service,
                filename,
                version,
                file_format
            )

            # Save schema metadata to database
            if not upload_data.replace_existing:
                self.mark_previous_versions_as_old(db, application.id, service_id)

            schema_record = Schema(
                version=version,
                file_name=filename,
                file_path=file_path,
                file_format=file_format,
                file_size=file_size,
                checksum=checksum,
                is_latest=True,
                application_id=application.id,
                service_id=service_id
            )

            db.add(schema_record)
            db.commit()
            db.refresh(schema_record)

            schema_info = SchemaInfo.from_orm(schema_record)

            return UploadResponse(
                success=True,
                message=f"Schema uploaded successfully for {upload_data.application}" +
                       (f"/{upload_data.service}" if upload_data.service else ""),
                schema_info=schema_info,
                version=version
            )

        except Exception as e:
            return UploadResponse(
                success=False,
                message=f"Upload failed: {str(e)}"
            )

    def get_latest_schema(
        self,
        db: Session,
        application_name: str,
        service_name: Optional[str] = None
    ) -> Optional[SchemaResponse]:
        """Get the latest schema for application/service"""

        # Find application
        application = db.query(Application).filter(Application.name == application_name).first()
        if not application:
            return None

        service = None
        service_id = None

        if service_name:
            service = db.query(Service).filter(
                and_(Service.name == service_name, Service.application_id == application.id)
            ).first()
            if not service:
                return None
            service_id = service.id

        # Find latest schema
        query = db.query(Schema).filter(
            and_(
                Schema.application_id == application.id,
                Schema.is_latest == True
            )
        )

        if service_id:
            query = query.filter(Schema.service_id == service_id)
        else:
            query = query.filter(Schema.service_id.is_(None))

        schema_record = query.first()
        if not schema_record:
            return None

        return SchemaResponse(
            schema_info=SchemaInfo.from_orm(schema_record),
            application=application,
            service=service
        )

    def get_schema_versions(
        self,
        db: Session,
        application_name: str,
        service_name: Optional[str] = None
    ) -> List[SchemaInfo]:
        """Get all versions of schema for application/service"""

        # Find application
        application = db.query(Application).filter(Application.name == application_name).first()
        if not application:
            return []

        service_id = None
        if service_name:
            service = db.query(Service).filter(
                and_(Service.name == service_name, Service.application_id == application.id)
            ).first()
            if not service:
                return []
            service_id = service.id

        # Get all versions
        query = db.query(Schema).filter(Schema.application_id == application.id)

        if service_id:
            query = query.filter(Schema.service_id == service_id)
        else:
            query = query.filter(Schema.service_id.is_(None))

        schemas = query.order_by(desc(Schema.version)).all()
        return [SchemaInfo.from_orm(schema) for schema in schemas]

    async def get_schema_content(self, schema_info: SchemaInfo) -> Dict[Any, Any]:
        """Load schema content from file"""
        return await self.storage.load_schema(schema_info.file_path)
