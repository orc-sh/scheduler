"""multi_webhook_benchmark

Revision ID: multi_webhook_benchmark
Revises: add_notifications_table
Create Date: 2025-11-26 23:29:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "multi_webhook_benchmark"
down_revision: Union[str, None] = "add_notifications_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    connection = op.get_bind()

    # Step 1: Add load_test_configuration_id to webhooks table
    existing_columns = [col["name"] for col in inspector.get_columns("webhooks")]
    if "load_test_configuration_id" not in existing_columns:
        op.add_column("webhooks", sa.Column("load_test_configuration_id", sa.String(length=36), nullable=True))
        op.create_foreign_key(
            "fk_webhooks_load_test_config",
            "webhooks",
            "load_test_configurations",
            ["load_test_configuration_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index("idx_webhooks_load_test_config_id", "webhooks", ["load_test_configuration_id"], unique=False)

    # Step 2: Add order column to webhooks table
    if "order" not in existing_columns:
        op.add_column("webhooks", sa.Column("order", sa.Integer(), nullable=True))

    # Step 3: Migrate existing data
    # For each load_test_configuration with a webhook_id, update the webhook to have load_test_configuration_id
    if "load_test_configurations" in inspector.get_table_names():
        result = connection.execute(
            text(
                """
                SELECT id, webhook_id
                FROM load_test_configurations
                WHERE webhook_id IS NOT NULL
            """
            )
        )

        for row in result:
            config_id = row[0]
            webhook_id = row[1]

            # Update the webhook to reference the configuration
            connection.execute(
                text(
                    """
                    UPDATE webhooks
                    SET load_test_configuration_id = :config_id, `order` = 0
                    WHERE id = :webhook_id
                """
                ),
                {"config_id": config_id, "webhook_id": webhook_id},
            )

    # Step 4: Remove webhook_id from load_test_configurations
    if "load_test_configurations" in inspector.get_table_names():
        existing_config_columns = [col["name"] for col in inspector.get_columns("load_test_configurations")]
        if "webhook_id" in existing_config_columns:
            # Drop the index first
            try:
                op.drop_index("idx_load_test_configs_webhook_id", table_name="load_test_configurations")
            except Exception:
                pass  # Index might not exist

            # Drop the foreign key constraint
            try:
                op.drop_constraint("load_test_configurations_ibfk_2", "load_test_configurations", type_="foreignkey")
            except Exception:
                try:
                    op.drop_constraint("fk_load_test_configs_webhook", "load_test_configurations", type_="foreignkey")
                except Exception:
                    pass  # Constraint might have different name or not exist

            # Drop the column
            op.drop_column("load_test_configurations", "webhook_id")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    connection = op.get_bind()

    # Step 1: Add webhook_id back to load_test_configurations
    if "load_test_configurations" in inspector.get_table_names():
        existing_config_columns = [col["name"] for col in inspector.get_columns("load_test_configurations")]
        if "webhook_id" not in existing_config_columns:
            op.add_column("load_test_configurations", sa.Column("webhook_id", sa.String(length=36), nullable=True))

            # Migrate data back: get first webhook for each configuration
            result = connection.execute(
                text(
                    """
                    SELECT id, load_test_configuration_id
                    FROM webhooks
                    WHERE load_test_configuration_id IS NOT NULL
                    ORDER BY `order` ASC, created_at ASC
                """
                )
            )

            # Group by configuration and take first webhook
            config_webhook_map = {}
            for row in result:
                config_id = row[1]
                webhook_id = row[0]
                if config_id not in config_webhook_map:
                    config_webhook_map[config_id] = webhook_id

            # Update configurations
            for config_id, webhook_id in config_webhook_map.items():
                connection.execute(
                    text(
                        """
                        UPDATE load_test_configurations
                        SET webhook_id = :webhook_id
                        WHERE id = :config_id
                    """
                    ),
                    {"webhook_id": webhook_id, "config_id": config_id},
                )

            # Make webhook_id NOT NULL and add constraints
            op.alter_column("load_test_configurations", "webhook_id", nullable=False)
            op.create_foreign_key(
                "fk_load_test_configs_webhook",
                "load_test_configurations",
                "webhooks",
                ["webhook_id"],
                ["id"],
                ondelete="CASCADE",
            )
            op.create_index(
                "idx_load_test_configs_webhook_id", "load_test_configurations", ["webhook_id"], unique=False
            )

    # Step 2: Remove load_test_configuration_id from webhooks
    existing_columns = [col["name"] for col in inspector.get_columns("webhooks")]
    if "load_test_configuration_id" in existing_columns:
        try:
            op.drop_index("idx_webhooks_load_test_config_id", table_name="webhooks")
        except Exception:
            pass
        try:
            op.drop_constraint("fk_webhooks_load_test_config", "webhooks", type_="foreignkey")
        except Exception:
            pass
        op.drop_column("webhooks", "load_test_configuration_id")

    # Step 3: Remove order column from webhooks
    if "order" in existing_columns:
        op.drop_column("webhooks", "order")
