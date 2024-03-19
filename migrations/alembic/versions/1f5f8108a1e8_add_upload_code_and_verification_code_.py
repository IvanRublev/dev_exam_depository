"""Add upload_code and verification_code indexes

Revision ID: 1f5f8108a1e8
Revises: 5d15013643a6
Create Date: 2024-03-19 10:26:35.213726

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1f5f8108a1e8"
down_revision: Union[str, None] = "5d15013643a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # we create unique constraints which also create indexes
    op.create_unique_constraint("upload_code_unique", "students", ["upload_code"])
    op.create_unique_constraint("verification_code_unique", "submissions", ["verification_code"])


def downgrade() -> None:
    op.drop_constraint("upload_code_unique", "students", type_="unique")
    op.drop_constraint("verification_code_unique", "submissions", type_="unique")
