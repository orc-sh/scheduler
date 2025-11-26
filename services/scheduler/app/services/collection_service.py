"""
Service for managing webhook collections.
"""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.collections import Collection


class CollectionService:
    """Service class for webhook collection operations"""

    def __init__(self, db: Session):
        """
        Initialize the service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_collection(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Collection:
        """
        Create a new webhook collection.

        Args:
            project_id: ID of the project
            name: Name of the collection (can be blank/None)
            description: Description of the collection

        Returns:
            Created Collection instance
        """
        collection = Collection(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=name,
            description=description,
        )
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        return collection

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """
        Get a webhook collection by ID.

        Args:
            collection_id: ID of the collection

        Returns:
            Collection instance if found, None otherwise
        """
        return self.db.query(Collection).filter(Collection.id == collection_id).first()

    def get_collections_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Collection]:
        """
        Get all webhook collections for a project.

        Args:
            project_id: ID of the project
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Collection instances
        """
        return (
            self.db.query(Collection)
            .filter(Collection.project_id == project_id)
            .order_by(Collection.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_collection(
        self,
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Collection]:
        """
        Update a webhook collection.

        Args:
            collection_id: ID of the collection
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated Collection instance if found, None otherwise
        """
        collection = self.get_collection(collection_id)
        if not collection:
            return None

        if name is not None:
            collection.name = name
        if description is not None:
            collection.description = description

        self.db.commit()
        self.db.refresh(collection)
        return collection

    def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a webhook collection and all its runs.

        Args:
            collection_id: ID of the collection

        Returns:
            True if deleted, False if not found
        """
        collection = self.get_collection(collection_id)
        if not collection:
            return False

        self.db.delete(collection)
        self.db.commit()
        return True


def get_collection_service(db: Session) -> CollectionService:
    """
    Factory function to create a CollectionService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        CollectionService instance
    """
    return CollectionService(db)
