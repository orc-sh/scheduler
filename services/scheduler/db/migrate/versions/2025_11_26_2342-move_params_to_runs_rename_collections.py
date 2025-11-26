"""move_params_to_runs_rename_collections

Revision ID: move_params_to_runs
Revises: multi_webhook_benchmark
Create Date: 2025-11-26 23:42:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "move_params_to_runs"
down_revision: Union[str, None] = "multi_webhook_benchmark"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    connection = op.get_bind()

    # Step 1: Add execution parameters to load_test_runs
    existing_run_columns = [col["name"] for col in inspector.get_columns("load_test_runs")]

    if "concurrent_users" not in existing_run_columns:
        op.add_column("load_test_runs", sa.Column("concurrent_users", sa.Integer(), nullable=True, server_default="10"))
    if "duration_seconds" not in existing_run_columns:
        op.add_column("load_test_runs", sa.Column("duration_seconds", sa.Integer(), nullable=True, server_default="60"))
    if "requests_per_second" not in existing_run_columns:
        op.add_column("load_test_runs", sa.Column("requests_per_second", sa.Integer(), nullable=True))

    # Step 2: Migrate data from configurations to runs
    if "load_test_configurations" in inspector.get_table_names() and "load_test_runs" in inspector.get_table_names():
        # Get config values
        configs = connection.execute(
            text(
                """
                SELECT id, concurrent_users, duration_seconds, requests_per_second
                FROM load_test_configurations
            """
            )
        )

        config_map = {
            row[0]: {"concurrent_users": row[1], "duration_seconds": row[2], "requests_per_second": row[3]}
            for row in configs
        }

        # Update runs with config values
        for config_id, params in config_map.items():
            connection.execute(
                text(
                    """
                    UPDATE load_test_runs
                    SET concurrent_users = :concurrent_users,
                        duration_seconds = :duration_seconds,
                        requests_per_second = :requests_per_second
                    WHERE load_test_configuration_id = :config_id
                    AND (concurrent_users IS NULL OR duration_seconds IS NULL)
                """
                ),
                {
                    "config_id": config_id,
                    "concurrent_users": params["concurrent_users"],
                    "duration_seconds": params["duration_seconds"],
                    "requests_per_second": params["requests_per_second"],
                },
            )

    # Step 3: Make columns NOT NULL after data migration
    # For MySQL, we need to handle server_default separately
    # First, ensure all NULL values are filled
    connection.execute(
        text(
            """
            UPDATE load_test_runs
            SET concurrent_users = COALESCE(concurrent_users, 10),
                duration_seconds = COALESCE(duration_seconds, 60)
            WHERE concurrent_users IS NULL OR duration_seconds IS NULL
        """
        )
    )

    # Now alter columns to NOT NULL (MySQL requires existing_type)
    op.alter_column("load_test_runs", "concurrent_users", existing_type=sa.Integer(), nullable=False)
    op.alter_column("load_test_runs", "duration_seconds", existing_type=sa.Integer(), nullable=False)

    # Step 4: Remove execution parameters from load_test_configurations
    if "load_test_configurations" in inspector.get_table_names():
        existing_config_columns = [col["name"] for col in inspector.get_columns("load_test_configurations")]

        if "concurrent_users" in existing_config_columns:
            op.drop_column("load_test_configurations", "concurrent_users")
        if "duration_seconds" in existing_config_columns:
            op.drop_column("load_test_configurations", "duration_seconds")
        if "requests_per_second" in existing_config_columns:
            op.drop_column("load_test_configurations", "requests_per_second")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    connection = op.get_bind()

    # Step 1: Add execution parameters back to load_test_configurations
    if "load_test_configurations" in inspector.get_table_names():
        existing_config_columns = [col["name"] for col in inspector.get_columns("load_test_configurations")]

        if "concurrent_users" not in existing_config_columns:
            op.add_column(
                "load_test_configurations",
                sa.Column("concurrent_users", sa.Integer(), nullable=True, server_default="10"),
            )
        if "duration_seconds" not in existing_config_columns:
            op.add_column(
                "load_test_configurations",
                sa.Column("duration_seconds", sa.Integer(), nullable=True, server_default="60"),
            )
        if "requests_per_second" not in existing_config_columns:
            op.add_column("load_test_configurations", sa.Column("requests_per_second", sa.Integer(), nullable=True))

        # Migrate data back: use first run's values for each config
        if "load_test_runs" in inspector.get_table_names():
            runs = connection.execute(
                text(
                    """
                    SELECT load_test_configuration_id, concurrent_users, duration_seconds, requests_per_second
                    FROM load_test_runs
                    ORDER BY created_at ASC
                """
                )
            )

            config_map = {}
            for row in runs:
                config_id = row[0]
                if config_id not in config_map:
                    config_map[config_id] = {
                        "concurrent_users": row[1],
                        "duration_seconds": row[2],
                        "requests_per_second": row[3],
                    }

            for config_id, params in config_map.items():
                connection.execute(
                    text(
                        """
                        UPDATE load_test_configurations
                        SET concurrent_users = :concurrent_users,
                            duration_seconds = :duration_seconds,
                            requests_per_second = :requests_per_second
                        WHERE id = :config_id
                    """
                    ),
                    {
                        "config_id": config_id,
                        "concurrent_users": params["concurrent_users"],
                        "duration_seconds": params["duration_seconds"],
                        "requests_per_second": params["requests_per_second"],
                    },
                )

        # Ensure all NULL values are filled before making NOT NULL
        connection.execute(
            text(
                """
                UPDATE load_test_configurations
                SET concurrent_users = COALESCE(concurrent_users, 10),
                    duration_seconds = COALESCE(duration_seconds, 60)
                WHERE concurrent_users IS NULL OR duration_seconds IS NULL
            """
            )
        )

        op.alter_column("load_test_configurations", "concurrent_users", existing_type=sa.Integer(), nullable=False)
        op.alter_column("load_test_configurations", "duration_seconds", existing_type=sa.Integer(), nullable=False)

    # Step 2: Remove execution parameters from load_test_runs
    existing_run_columns = [col["name"] for col in inspector.get_columns("load_test_runs")]

    if "concurrent_users" in existing_run_columns:
        op.drop_column("load_test_runs", "concurrent_users")
    if "duration_seconds" in existing_run_columns:
        op.drop_column("load_test_runs", "duration_seconds")
    if "requests_per_second" in existing_run_columns:
        op.drop_column("load_test_runs", "requests_per_second")
