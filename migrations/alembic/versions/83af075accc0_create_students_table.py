"""create students table

Revision ID: 83af075accc0
Revises:
Create Date: 2024-03-14 17:32:52.001686

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "83af075accc0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nickname", sa.String, unique=True, nullable=False),
        sa.Column("first_name", sa.String, nullable=False),
        sa.Column("last_name", sa.String, nullable=False),
        sa.Column("upload_code", sa.String, nullable=False),
        sa.Column("email", sa.String, unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("students")
