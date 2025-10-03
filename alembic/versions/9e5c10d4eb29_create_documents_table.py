"""create documents table

Revision ID: 9e5c10d4eb29
Revises:
Create Date: 2025-10-02 20:30:34.233794

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg


# revision identifiers, used by Alembic.
revision: str = "9e5c10d4eb29"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

document_status_enum = pg.ENUM("PENDING", "SUCCESS", "FAILED", name="documentstatus")


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("document_uuid", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column(
            "status", sa.Enum("PENDING", "PROCESSING", "SUCCESS", "FAILED", name="documentstatus"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER set_updated_at
        BEFORE UPDATE ON documents
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS set_updated_at ON documents;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column;")

    op.drop_table("documents")

    document_status_enum.drop(op.get_bind(), checkfirst=True)
