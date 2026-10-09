from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_example_notes"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the example notes table."""
    op.create_table(
        "example_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("content", sa.String(length=500), nullable=False),
    )


def downgrade() -> None:
    """Remove the example notes table."""
    op.drop_table("example_notes")
