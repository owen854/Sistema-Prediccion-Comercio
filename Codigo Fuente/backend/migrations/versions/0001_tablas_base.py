"""Tablas base: comercio, usuario y trabajo (Fase 0).

Revision ID: 0001
Revises:
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "comercio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo_seudonimo", sa.String(length=32), nullable=False),
        sa.Column("municipio", sa.String(length=80), nullable=False),
        sa.Column("tipo_negocio", sa.String(length=80), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comercio")),
        sa.UniqueConstraint("codigo_seudonimo", name=op.f("uq_comercio_codigo_seudonimo")),
    )
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("correo", sa.String(length=254), nullable=False),
        sa.Column("hash_contrasena", sa.String(length=255), nullable=False),
        sa.Column(
            "rol",
            sa.Enum("admin", "analista", "comerciante", name="rol", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("comercio_id", sa.Integer(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "rol <> 'comerciante' OR comercio_id IS NOT NULL",
            name=op.f("ck_usuario_comerciante_con_comercio"),
        ),
        sa.ForeignKeyConstraint(
            ["comercio_id"],
            ["comercio.id"],
            name=op.f("fk_usuario_comercio_id_comercio"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
        sa.UniqueConstraint("correo", name=op.f("uq_usuario_correo")),
    )
    op.create_table(
        "trabajo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("parametros", JSON_TYPE, nullable=False),
        sa.Column(
            "estado",
            sa.Enum(
                "pendiente",
                "en_curso",
                "ok",
                "fallido",
                "cancelado",
                name="estadotrabajo",
                native_enum=False,
                length=20,
            ),
            server_default="pendiente",
            nullable=False,
        ),
        sa.Column("progreso", sa.Float(), server_default="0", nullable=False),
        sa.Column("intentos", sa.Integer(), server_default="0", nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=True),
        sa.Column("ruta_registros", sa.String(length=500), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terminado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["creado_por"],
            ["usuario.id"],
            name=op.f("fk_trabajo_creado_por_usuario"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trabajo")),
    )
    op.create_index("ix_trabajo_estado_creado_en", "trabajo", ["estado", "creado_en"])


def downgrade() -> None:
    op.drop_index("ix_trabajo_estado_creado_en", table_name="trabajo")
    op.drop_table("trabajo")
    op.drop_table("usuario")
    op.drop_table("comercio")
