"""add tool_executions table

Revision ID: c584b34b4ad6
Revises: 
Create Date: 2026-05-21 13:06:11.943173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c584b34b4ad6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tool_executions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('arguments', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_executions_conversation_id'), 'tool_executions', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_tool_executions_tool_name'), 'tool_executions', ['tool_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tool_executions_tool_name'), table_name='tool_executions')
    op.drop_index(op.f('ix_tool_executions_conversation_id'), table_name='tool_executions')
    op.drop_table('tool_executions')
