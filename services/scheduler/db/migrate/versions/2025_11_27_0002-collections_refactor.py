"""collections_refactor

Revision ID: collections_refactor
Revises: move_params_to_runs
Create Date: 2025-11-27 00:02:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "collections_refactor"
down_revision: Union[str, None] = "move_params_to_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    connection = op.get_bind()

    # Step 1: Create collections table (if it doesn't exist)
    if "collections" not in inspector.get_table_names():
        op.create_table(
            "collections",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(), server_default=text("CURRENT_TIMESTAMP")),
            sa.Column(
                "updated_at", sa.TIMESTAMP(), server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            ),
            sa.Index("idx_collections_project_id", "project_id"),
            sa.Index("idx_collections_created_at", "created_at"),
        )

    # Step 2: Migrate data from load_test_configurations to collections (only if not already migrated)
    if "load_test_configurations" in inspector.get_table_names() and "collections" in inspector.get_table_names():
        # Check if data already exists in collections
        existing_collections = connection.execute(text("SELECT COUNT(*) as count FROM collections")).scalar()

        # Only migrate if collections table is empty
        if existing_collections == 0:
            configs = connection.execute(
                text(
                    """
                    SELECT id, project_id, name, created_at, updated_at
                    FROM load_test_configurations
                """
                )
            )

            for row in configs:
                # Use INSERT IGNORE to avoid duplicates if migration is run multiple times
                connection.execute(
                    text(
                        """
                        INSERT IGNORE INTO collections (id, project_id, name, description, created_at, updated_at)
                        VALUES (:id, :project_id, :name, NULL, :created_at, :updated_at)
                    """
                    ),
                    {
                        "id": row[0],
                        "project_id": row[1],
                        "name": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                    },
                )

    # Step 3: Add collection_id to webhooks table
    if "webhooks" in inspector.get_table_names():
        existing_webhook_columns = [col["name"] for col in inspector.get_columns("webhooks")]

        # First, drop any foreign key constraints on load_test_configuration_id if the column still exists
        if "load_test_configuration_id" in existing_webhook_columns:
            # Get all foreign keys on webhooks table
            webhook_fks = inspector.get_foreign_keys("webhooks")
            for fk in webhook_fks:
                if "load_test_configuration_id" in fk.get("constrained_columns", []):
                    constraint_name = fk.get("name")
                    if constraint_name:
                        try:
                            op.drop_constraint(constraint_name, "webhooks", type_="foreignkey")
                        except Exception:
                            pass

            # Also try common constraint names
            constraint_names = [
                "webhooks_ibfk_2",
                "fk_webhooks_load_test_config",
                "fk_webhooks_load_test_configuration_id",
            ]
            for constraint_name in constraint_names:
                try:
                    op.drop_constraint(constraint_name, "webhooks", type_="foreignkey")
                except Exception:
                    pass

        if "collection_id" not in existing_webhook_columns:
            op.add_column("webhooks", sa.Column("collection_id", sa.String(36), nullable=True))

            # Create foreign key (if it doesn't exist)
            try:
                op.create_foreign_key(
                    "fk_webhooks_collection_id",
                    "webhooks",
                    "collections",
                    ["collection_id"],
                    ["id"],
                    ondelete="CASCADE",
                )
            except Exception:
                pass  # Foreign key might already exist

            # Create index (if it doesn't exist)
            try:
                op.create_index("idx_webhooks_collection_id", "webhooks", ["collection_id"])
            except Exception:
                pass  # Index might already exist

            # Migrate data: copy load_test_configuration_id to collection_id
            if "load_test_configuration_id" in existing_webhook_columns:
                connection.execute(
                    text(
                        """
                        UPDATE webhooks
                        SET collection_id = load_test_configuration_id
                        WHERE load_test_configuration_id IS NOT NULL
                    """
                    )
                )

            # Drop old foreign key, index, and column
            if "load_test_configuration_id" in existing_webhook_columns:
                # First, get all foreign key constraints on this column
                fk_constraints = inspector.get_foreign_keys("webhooks")
                for fk in fk_constraints:
                    if "load_test_configuration_id" in fk.get("constrained_columns", []):
                        constraint_name = fk.get("name")
                        if constraint_name:
                            try:
                                op.drop_constraint(constraint_name, "webhooks", type_="foreignkey")
                            except Exception:
                                pass

                # Also try common constraint names in case inspector didn't find them
                constraint_names = [
                    "webhooks_ibfk_2",
                    "fk_webhooks_load_test_config",
                    "fk_webhooks_load_test_configuration_id",
                ]
                for constraint_name in constraint_names:
                    try:
                        op.drop_constraint(constraint_name, "webhooks", type_="foreignkey")
                    except Exception:
                        pass

                # Drop index
                try:
                    op.drop_index("idx_webhooks_load_test_config_id", "webhooks")
                except Exception:
                    pass

                # Drop column (now that foreign key is removed)
                op.drop_column("webhooks", "load_test_configuration_id")

    # Step 4: Add collection_id to load_test_runs table
    if "load_test_runs" in inspector.get_table_names():
        existing_run_columns = [col["name"] for col in inspector.get_columns("load_test_runs")]

        # Always ensure collection_id exists
        if "collection_id" not in existing_run_columns:
            op.add_column("load_test_runs", sa.Column("collection_id", sa.String(36), nullable=True))

        # Migrate data: copy load_test_configuration_id to collection_id (if old column exists and new column is NULL)
        if "load_test_configuration_id" in existing_run_columns:
            connection.execute(
                text(
                    """
                    UPDATE load_test_runs
                    SET collection_id = load_test_configuration_id
                    WHERE load_test_configuration_id IS NOT NULL AND (collection_id IS NULL OR collection_id = '')
                """
                )
            )

        # Ensure no NULL values before making NOT NULL
        # If there are any NULLs, we can't proceed (data integrity issue)
        null_count = connection.execute(
            text("SELECT COUNT(*) FROM load_test_runs WHERE collection_id IS NULL OR collection_id = ''")
        ).scalar()

        if null_count > 0:
            raise ValueError(
                f"Cannot proceed: {null_count} load_test_runs have NULL collection_id. Please fix data first."
            )

        # Make collection_id NOT NULL after migration (if it's not already)
        try:
            op.alter_column("load_test_runs", "collection_id", existing_type=sa.String(36), nullable=False)
        except Exception:
            pass  # Column might already be NOT NULL

        # Create foreign key (if it doesn't exist)
        try:
            op.create_foreign_key(
                "fk_load_test_runs_collection_id",
                "load_test_runs",
                "collections",
                ["collection_id"],
                ["id"],
                ondelete="CASCADE",
            )
        except Exception:
            pass  # Foreign key might already exist

        # Create index (if it doesn't exist)
        try:
            op.create_index("idx_load_test_runs_collection_id", "load_test_runs", ["collection_id"])
        except Exception:
            pass  # Index might already exist

        # ALWAYS drop old foreign key, index, and column if they exist
        # This handles the case where migration was partially run
        if "load_test_configuration_id" in existing_run_columns:
            # First, get all foreign key constraints on this column
            # MySQL might name them differently, so we need to check
            fk_constraints = inspector.get_foreign_keys("load_test_runs")
            for fk in fk_constraints:
                if "load_test_configuration_id" in fk.get("constrained_columns", []):
                    constraint_name = fk.get("name")
                    if constraint_name:
                        try:
                            op.drop_constraint(constraint_name, "load_test_runs", type_="foreignkey")
                        except Exception:
                            pass

            # Also try common constraint names in case inspector didn't find them
            constraint_names = [
                "load_test_runs_ibfk_1",
                "fk_load_test_runs_config_id",
                "fk_load_test_runs_load_test_configuration_id",
            ]
            for constraint_name in constraint_names:
                try:
                    op.drop_constraint(constraint_name, "load_test_runs", type_="foreignkey")
                except Exception:
                    pass

            # Drop index
            try:
                op.drop_index("idx_load_test_runs_config_id", "load_test_runs")
            except Exception:
                pass

            # Drop column (now that foreign key is removed)
            try:
                op.drop_column("load_test_runs", "load_test_configuration_id")
            except Exception:
                pass  # Column might already be dropped

    # Step 5: Drop load_test_configurations table
    # First, ensure all foreign keys referencing this table are dropped
    if "load_test_configurations" in inspector.get_table_names():
        # Check all tables for foreign keys referencing load_test_configurations
        all_tables = inspector.get_table_names()
        for table_name in all_tables:
            try:
                table_fks = inspector.get_foreign_keys(table_name)
                for fk in table_fks:
                    if fk.get("referred_table") == "load_test_configurations":
                        constraint_name = fk.get("name")
                        if constraint_name:
                            try:
                                op.drop_constraint(constraint_name, table_name, type_="foreignkey")
                            except Exception:
                                pass
            except Exception:
                pass  # Skip if we can't inspect this table

        # Also try dropping the specific constraint name from the error on webhooks
        if "webhooks" in inspector.get_table_names():
            constraint_names = [
                "fk_webhooks_load_test_config",
                "webhooks_ibfk_2",
                "fk_webhooks_load_test_configuration_id",
            ]
            for constraint_name in constraint_names:
                try:
                    op.drop_constraint(constraint_name, "webhooks", type_="foreignkey")
                except Exception:
                    pass

        # Now drop the table
        op.drop_table("load_test_configurations")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    connection = op.get_bind()

    # Step 1: Recreate load_test_configurations table
    op.create_table(
        "load_test_configurations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.Index("idx_load_test_configs_project_id", "project_id"),
        sa.Index("idx_load_test_configs_created_at", "created_at"),
    )

    # Step 2: Migrate data from collections to load_test_configurations
    if "collections" in inspector.get_table_names():
        collections = connection.execute(
            text(
                """
                SELECT id, project_id, name, created_at, updated_at
                FROM collections
            """
            )
        )

        for row in collections:
            connection.execute(
                text(
                    """
                    INSERT INTO load_test_configurations (id, project_id, name, created_at, updated_at)
                    VALUES (:id, :project_id, :name, :created_at, :updated_at)
                """
                ),
                {
                    "id": row[0],
                    "project_id": row[1],
                    "name": row[2] or "",
                    "created_at": row[3],
                    "updated_at": row[4],
                },
            )

    # Step 3: Add load_test_configuration_id back to webhooks
    if "webhooks" in inspector.get_table_names():
        existing_webhook_columns = [col["name"] for col in inspector.get_columns("webhooks")]

        if "load_test_configuration_id" not in existing_webhook_columns:
            op.add_column("webhooks", sa.Column("load_test_configuration_id", sa.String(36), nullable=True))

            # Migrate data: copy collection_id to load_test_configuration_id
            if "collection_id" in existing_webhook_columns:
                connection.execute(
                    text(
                        """
                        UPDATE webhooks
                        SET load_test_configuration_id = collection_id
                        WHERE collection_id IS NOT NULL
                    """
                    )
                )

            # Create foreign key
            op.create_foreign_key(
                "fk_webhooks_load_test_configuration_id",
                "webhooks",
                "load_test_configurations",
                ["load_test_configuration_id"],
                ["id"],
                ondelete="CASCADE",
            )

            # Create index
            op.create_index("idx_webhooks_load_test_config_id", "webhooks", ["load_test_configuration_id"])

            # Drop collection_id
            if "collection_id" in existing_webhook_columns:
                op.drop_constraint("fk_webhooks_collection_id", "webhooks", type_="foreignkey")
                op.drop_index("idx_webhooks_collection_id", "webhooks")
                op.drop_column("webhooks", "collection_id")

    # Step 4: Add load_test_configuration_id back to load_test_runs
    if "load_test_runs" in inspector.get_table_names():
        existing_run_columns = [col["name"] for col in inspector.get_columns("load_test_runs")]

        if "load_test_configuration_id" not in existing_run_columns:
            op.add_column("load_test_runs", sa.Column("load_test_configuration_id", sa.String(36), nullable=True))

            # Migrate data: copy collection_id to load_test_configuration_id
            if "collection_id" in existing_run_columns:
                connection.execute(
                    text(
                        """
                        UPDATE load_test_runs
                        SET load_test_configuration_id = collection_id
                        WHERE collection_id IS NOT NULL
                    """
                    )
                )

            # Make load_test_configuration_id NOT NULL after migration
            op.alter_column("load_test_runs", "load_test_configuration_id", existing_type=sa.String(36), nullable=False)

            # Create foreign key
            op.create_foreign_key(
                "fk_load_test_runs_load_test_configuration_id",
                "load_test_runs",
                "load_test_configurations",
                ["load_test_configuration_id"],
                ["id"],
                ondelete="CASCADE",
            )

            # Create index
            op.create_index("idx_load_test_runs_config_id", "load_test_runs", ["load_test_configuration_id"])

            # Drop collection_id
            if "collection_id" in existing_run_columns:
                op.drop_constraint("fk_load_test_runs_collection_id", "load_test_runs", type_="foreignkey")
                op.drop_index("idx_load_test_runs_collection_id", "load_test_runs")
                op.drop_column("load_test_runs", "collection_id")

    # Step 5: Drop collections table
    if "collections" in inspector.get_table_names():
        op.drop_table("collections")
