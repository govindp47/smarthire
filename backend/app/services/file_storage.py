"""
File storage service: local file system and S3.
"""
import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import uuid4

import aiofiles
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


class FileStorageService:
    """
    Handle file storage (local or S3).
    
    For development: Uses local file system
    For production: Uses AWS S3
    """
    
    def __init__(self):
        """Initialize file storage service."""
        self.use_s3 = bool(settings.AWS_BUCKET_NAME and settings.AWS_ACCESS_KEY_ID)
        self.local_storage_path = Path("uploads/resumes")
        
        # Create local storage directory if it doesn't exist
        if not self.use_s3:
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
    
    async def save_file(
        self, 
        file: UploadFile, 
        job_id: str,
        allowed_extensions: Optional[list] = None
    ) -> dict:
        """
        Save uploaded file to storage.
        
        Args:
            file: Uploaded file
            job_id: Job ID for organizing files
            allowed_extensions: List of allowed file extensions
            
        Returns:
            Dictionary with file_path, file_name, file_size, file_type
            
        Raises:
            HTTPException: If file validation fails
        """
        # Validate file
        if allowed_extensions is None:
            allowed_extensions = settings.allowed_extensions_list
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type .{file_extension} not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        # Reset file pointer to beginning (important!)
        await file.seek(0)
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {max_mb}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Generate unique filename
        unique_id = uuid4().hex[:8]
        safe_filename = f"{unique_id}_{Path(file.filename).name}"
        
        if self.use_s3:
            # Save to S3
            file_path = await self._save_to_s3(content, job_id, safe_filename)
        else:
            # Save to local file system
            file_path = await self._save_to_local(content, job_id, safe_filename)
        
        return {
            "file_path": file_path,
            "file_name": file.filename,
            "file_size": file_size,
            "file_type": file_extension
        }
    
    async def _save_to_local(self, content: bytes, job_id: str, filename: str) -> str:
        """
        Save file to local file system.
        
        Args:
            content: File content
            job_id: Job ID for organizing files
            filename: Filename
            
        Returns:
            File path
        """
        # Create job-specific directory
        job_dir = self.local_storage_path / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Full file path
        file_path = job_dir / filename
        
        # Write file in binary mode (important for PDFs!)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Return relative path
        return str(file_path)
    
    async def _save_to_s3(self, content: bytes, job_id: str, filename: str) -> str:
        """
        Save file to AWS S3.
        
        Args:
            content: File content
            job_id: Job ID for organizing files
            filename: Filename
            
        Returns:
            S3 path (key)
        """
        import boto3
        from botocore.exceptions import ClientError
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # S3 key (path)
        s3_key = f"resumes/{job_id}/{filename}"
        
        try:
            # Upload file
            s3_client.put_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=s3_key,
                Body=content,
                ContentType=self._get_content_type(filename)
            )
            
            return s3_key
        
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {str(e)}"
            )
    
    async def get_file(self, file_path: str) -> bytes:
        """
        Retrieve file content.
        
        Args:
            file_path: Path to file (local or S3 key)
            
        Returns:
            File content as bytes
        """
        if self.use_s3:
            return await self._get_from_s3(file_path)
        else:
            return await self._get_from_local(file_path)
    
    async def _get_from_local(self, file_path: str) -> bytes:
        """Get file from local storage."""
        path = Path(file_path)
        
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        async with aiofiles.open(path, 'rb') as f:
            return await f.read()
    
    async def _get_from_s3(self, s3_key: str) -> bytes:
        """Get file from S3."""
        import boto3
        from botocore.exceptions import ClientError
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        try:
            response = s3_client.get_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=s3_key
            )
            return response['Body'].read()
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve file from S3: {str(e)}"
            )
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if successful
        """
        if self.use_s3:
            return await self._delete_from_s3(file_path)
        else:
            return await self._delete_from_local(file_path)
    
    async def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local storage."""
        path = Path(file_path)
        
        if path.exists():
            path.unlink()
            return True
        return False
    
    async def _delete_from_s3(self, s3_key: str) -> bool:
        """Delete file from S3."""
        import boto3
        from botocore.exceptions import ClientError
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        try:
            s3_client.delete_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=s3_key
            )
            return True
        except ClientError:
            return False
    
    @staticmethod
    def _get_content_type(filename: str) -> str:
        """Get content type based on file extension."""
        extension = Path(filename).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
        }
        return content_types.get(extension, 'application/octet-stream')


# Global instance
file_storage = FileStorageService()