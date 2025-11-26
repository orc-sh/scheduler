"""fix_drop_load_test_config_id

Revision ID: fix_drop_load_test_config_id
Revises: collections_refactor
Create Date: 2025-11-27 00:37:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = "fix_drop_load_test_config_id"
down_revision: Union[str, None] = "collections_refactor"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop load_test_configuration_id column from load_test_runs if it still exists."""
    inspector = inspect(op.get_bind())

    if "load_test_runs" in inspector.get_table_names():
        existing_run_columns = [col["name"] for col in inspector.get_columns("load_test_runs")]

        # If load_test_configuration_id still exists, drop it
        if "load_test_configuration_id" in existing_run_columns:
            # First, drop any foreign key constraints
            fk_constraints = inspector.get_foreign_keys("load_test_runs")
            for fk in fk_constraints:
                if "load_test_configuration_id" in fk.get("constrained_columns", []):
                    constraint_name = fk.get("name")
                    if constraint_name:
                        try:
                            op.drop_constraint(constraint_name, "load_test_runs", type_="foreignkey")
                        except Exception:
                            pass

            # Also try common constraint names
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

            # Drop index if it exists
            try:
                op.drop_index("idx_load_test_runs_config_id", "load_test_runs")
            except Exception:
                pass

            # Finally, drop the column
            try:
                op.drop_column("load_test_runs", "load_test_configuration_id")
            except Exception as e:
                # If column doesn't exist, that's fine
                print(f"Warning: Could not drop load_test_configuration_id: {e}")


def downgrade() -> None:
    """Re-add load_test_configuration_id column (not typically needed)."""
    inspector = inspect(op.get_bind())

    if "load_test_runs" in inspector.get_table_names():
        existing_run_columns = [col["name"] for col in inspector.get_columns("load_test_runs")]

        if "load_test_configuration_id" not in existing_run_columns:
            # Re-add the column (nullable for now)
            op.add_column("load_test_runs", sa.Column("load_test_configuration_id", sa.String(36), nullable=True))

            # Copy data from collection_id
            connection = op.get_bind()
            connection.execute(
                text(
                    """
                    UPDATE load_test_runs
                    SET load_test_configuration_id = collection_id
                    WHERE collection_id IS NOT NULL
                """
                )
            )

            # Make it NOT NULL
            op.alter_column("load_test_runs", "load_test_configuration_id", existing_type=sa.String(36), nullable=False)

            # Recreate foreign key (if load_test_configurations table exists)
            try:
                op.create_foreign_key(
                    "fk_load_test_runs_load_test_configuration_id",
                    "load_test_runs",
                    "load_test_configurations",
                    ["load_test_configuration_id"],
                    ["id"],
                    ondelete="CASCADE",
                )
            except Exception:
                pass

            # Recreate index
            try:
                op.create_index("idx_load_test_runs_config_id", "load_test_runs", ["load_test_configuration_id"])
            except Exception:
                pass
