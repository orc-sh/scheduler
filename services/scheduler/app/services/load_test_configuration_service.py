"""
Service for managing webhook collections.

DEPRECATED: This service is no longer used. Use collection_service instead.
This file is kept for reference but should not be imported or used.
"""

from typing import Any, List, Optional

from sqlalchemy.orm import Session

# LoadTestConfiguration removed - replaced by Collection
# from app.models.load_test_configurations import LoadTestConfiguration


class LoadTestConfigurationService:
    """Service class for webhook collection operations"""

    def __init__(self, db: Session):
        """
        Initialize the service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_configuration(
        self,
        project_id: str,
        name: str,
    ) -> Any:  # LoadTestConfiguration removed
        """
        Create a new webhook collection.

        Args:
            project_id: ID of the project
            name: Name of the collection (can be blank)

        Returns:
            Created LoadTestConfiguration instance
        """
        # LoadTestConfiguration model removed - use Collection instead
        # This service is deprecated - use collection_service instead
        raise NotImplementedError("LoadTestConfigurationService is deprecated. Use CollectionService instead.")
        # configuration = LoadTestConfiguration(
        #     id=str(uuid.uuid4()),
        #     project_id=project_id,
        #     name=name,
        # )
        # self.db.add(configuration)
        # self.db.commit()
        # self.db.refresh(configuration)
        # return configuration

    def get_configuration(self, config_id: str) -> Optional[Any]:  # LoadTestConfiguration removed
        """
        Get a webhook collection by ID.

        Args:
            config_id: ID of the collection

        Returns:
            LoadTestConfiguration instance if found, None otherwise
        """
        raise NotImplementedError("LoadTestConfigurationService is deprecated. Use CollectionService instead.")
        # return self.db.query(LoadTestConfiguration).filter(LoadTestConfiguration.id == config_id).first()

    def get_configurations_by_project(
        self, project_id: str, skip: int = 0, limit: int = 100
    ) -> List[Any]:  # LoadTestConfiguration removed
        """
        Get all webhook collections for a project.

        Args:
            project_id: ID of the project
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of LoadTestConfiguration instances
        """
        raise NotImplementedError("LoadTestConfigurationService is deprecated. Use CollectionService instead.")
        # return (
        #     self.db.query(LoadTestConfiguration)
        #     .filter(LoadTestConfiguration.project_id == project_id)
        #     .order_by(LoadTestConfiguration.created_at.desc())
        #     .offset(skip)
        #     .limit(limit)
        #     .all()
        # )

    def update_configuration(
        self,
        config_id: str,
        name: Optional[str] = None,
    ) -> Optional[Any]:  # LoadTestConfiguration removed
        """
        Update a webhook collection.

        Args:
            config_id: ID of the collection
            name: New name

        Returns:
            Updated LoadTestConfiguration instance if found, None otherwise
        """
        configuration = self.get_configuration(config_id)
        if not configuration:
            return None

        if name is not None:
            configuration.name = name

        self.db.commit()
        self.db.refresh(configuration)
        return configuration

    def delete_configuration(self, config_id: str) -> bool:
        """
        Delete a webhook collection and all its runs.

        Args:
            config_id: ID of the collection

        Returns:
            True if deleted, False if not found
        """
        configuration = self.get_configuration(config_id)
        if not configuration:
            return False

        self.db.delete(configuration)
        self.db.commit()
        return True


def get_load_test_configuration_service(db: Session) -> LoadTestConfigurationService:
    """
    Factory function to create a LoadTestConfigurationService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        LoadTestConfigurationService instance
    """
    return LoadTestConfigurationService(db)
