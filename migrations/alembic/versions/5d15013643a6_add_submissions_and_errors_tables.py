"""add submissions and errors tables

Revision ID: 5d15013643a6
Revises: 83af075accc0
Create Date: 2024-03-16 10:35:43.244219

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d15013643a6"
down_revision: Union[str, None] = "83af075accc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String, nullable=False),
        sa.Column("md5", sa.String, nullable=False),
        sa.Column("verification_code", sa.String, nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "errors",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("detail", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("errors")
    op.drop_table("submissions")
