"""Conjuntos de datos versionados, series, observaciones y autorizaciones (Fase 1).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _creado_en() -> sa.Column:
    return sa.Column(
        "creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "autorizacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("comercio_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("alcance", sa.Text(), nullable=False),
        sa.Column("finalidad", sa.String(length=120), server_default="académica", nullable=False),
        sa.Column("documento_ref", sa.String(length=255), nullable=True),
        _creado_en(),
        sa.ForeignKeyConstraint(
            ["comercio_id"],
            ["comercio.id"],
            name=op.f("fk_autorizacion_comercio_id_comercio"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autorizacion")),
    )
    op.create_table(
        "dataset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column(
            "origen",
            sa.Enum(
                "publico",
                "transaccional",
                "sintetico",
                name="origendatos",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("fuente", sa.String(length=200), nullable=False),
        sa.Column("frecuencia", sa.String(length=8), nullable=False),
        sa.Column("comercio_id", sa.Integer(), nullable=True),
        _creado_en(),
        sa.ForeignKeyConstraint(
            ["comercio_id"],
            ["comercio.id"],
            name=op.f("fk_dataset_comercio_id_comercio"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset")),
        sa.UniqueConstraint("nombre", "comercio_id", name="uq_dataset_nombre_comercio"),
    )
    op.create_table(
        "dataset_version",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("archivo_original", sa.String(length=255), nullable=False),
        sa.Column("filas", sa.Integer(), nullable=False),
        sa.Column("reporte_calidad", JSON_TYPE, nullable=False),
        sa.Column("columnas_eliminadas", JSON_TYPE, nullable=False),
        sa.Column("autorizacion_id", sa.Integer(), nullable=True),
        _creado_en(),
        sa.ForeignKeyConstraint(
            ["autorizacion_id"],
            ["autorizacion.id"],
            name=op.f("fk_dataset_version_autorizacion_id_autorizacion"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["dataset.id"],
            name=op.f("fk_dataset_version_dataset_id_dataset"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_version")),
        sa.UniqueConstraint("dataset_id", "version", name="uq_dataset_version"),
    )
    op.create_table(
        "serie",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_version_id", sa.Integer(), nullable=False),
        sa.Column("clave", sa.String(length=120), nullable=False),
        sa.Column("nivel", sa.String(length=20), nullable=False),
        sa.Column("unidad", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_version.id"],
            name=op.f("fk_serie_dataset_version_id_dataset_version"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_serie")),
        sa.UniqueConstraint("dataset_version_id", "clave", name="uq_serie_clave"),
    )
    op.create_table(
        "observacion",
        sa.Column("serie_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["serie_id"],
            ["serie.id"],
            name=op.f("fk_observacion_serie_id_serie"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("serie_id", "fecha", name=op.f("pk_observacion")),
    )


def downgrade() -> None:
    op.drop_table("observacion")
    op.drop_table("serie")
    op.drop_table("dataset_version")
    op.drop_table("dataset")
    op.drop_table("autorizacion")
