"""add_extracted_text_to_resumes

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d7e8
Create Date: 2026-08-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("extracted_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "extracted_text")
