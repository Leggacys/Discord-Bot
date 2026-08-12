"""add pubg tracking

Revision ID: b7e41e5af904
Revises: f3c8096926fa
Create Date: 2026-08-11 23:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e41e5af904'
down_revision: Union[str, Sequence[str], None] = 'f3c8096926fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'pubg_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('pubg_account_id', sa.String(length=255), nullable=True),
        sa.Column('platform', sa.String(length=40), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_pubg_accounts_pubg_account_id'),
        'pubg_accounts',
        ['pubg_account_id'],
        unique=True,
    )
    op.create_index(
        op.f('ix_pubg_accounts_username'),
        'pubg_accounts',
        ['username'],
        unique=True,
    )

    op.create_table(
        'pubg_matches',
        sa.Column('match_id', sa.String(length=255), nullable=False),
        sa.Column('platform', sa.String(length=40), nullable=False),
        sa.Column('game_mode', sa.String(length=80), nullable=False),
        sa.Column('match_type', sa.String(length=80), nullable=True),
        sa.Column('played_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('match_id'),
    )

    op.create_table(
        'pubg_player_match_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('match_id', sa.String(length=255), nullable=False),
        sa.Column('pubg_account_id', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('win_place', sa.Integer(), nullable=True),
        sa.Column('kills', sa.Integer(), nullable=False),
        sa.Column('damage_dealt', sa.Float(), nullable=False),
        sa.Column('longest_kill', sa.Float(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['match_id'],
            ['pubg_matches.match_id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['pubg_account_id'],
            ['pubg_accounts.pubg_account_id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'match_id',
            'pubg_account_id',
            name='uq_pubg_stat_match_account',
        ),
    )
    op.create_index(
        op.f('ix_pubg_player_match_stats_match_id'),
        'pubg_player_match_stats',
        ['match_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_pubg_player_match_stats_pubg_account_id'),
        'pubg_player_match_stats',
        ['pubg_account_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_pubg_player_match_stats_username'),
        'pubg_player_match_stats',
        ['username'],
        unique=False,
    )

    op.create_table(
        'pubg_announcements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('match_id', sa.String(length=255), nullable=False),
        sa.Column('pubg_account_id', sa.String(length=255), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'event_type',
            'match_id',
            'pubg_account_id',
            name='uq_pubg_announcement_event',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('pubg_announcements')
    op.drop_index(
        op.f('ix_pubg_player_match_stats_username'),
        table_name='pubg_player_match_stats',
    )
    op.drop_index(
        op.f('ix_pubg_player_match_stats_pubg_account_id'),
        table_name='pubg_player_match_stats',
    )
    op.drop_index(
        op.f('ix_pubg_player_match_stats_match_id'),
        table_name='pubg_player_match_stats',
    )
    op.drop_table('pubg_player_match_stats')
    op.drop_table('pubg_matches')
    op.drop_index(
        op.f('ix_pubg_accounts_username'),
        table_name='pubg_accounts',
    )
    op.drop_index(
        op.f('ix_pubg_accounts_pubg_account_id'),
        table_name='pubg_accounts',
    )
    op.drop_table('pubg_accounts')
