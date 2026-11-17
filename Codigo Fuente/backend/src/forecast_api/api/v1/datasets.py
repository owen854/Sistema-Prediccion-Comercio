"""Comercios, autorizaciones y conjuntos de datos (RF-06 a RF-11, RF-59).

Mientras no exista la autenticación (HU-19, Sprint 2) las operaciones de escritura
solo se permiten fuera de producción.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from forecast_api.core.config import Settings, get_settings
from forecast_api.db.models import (
    Autorizacion,
    Comercio,
    Dataset,
    DatasetVersion,
    Observacion,
    Serie,
)
from forecast_api.db.session import get_session
from forecast_api.schemas.datasets import (
    AutorizacionCreate,
    AutorizacionOut,
    CargaOut,
    ComercioCreate,
    ComercioOut,
    DatasetOut,
    DatasetVersionOut,
    ErrorCargaOut,
    ProblemaOut,
    SerieOut,
)
from forecast_api.services import datasets as service
from forecast_core.ingestion.transactional import SalesValidationError

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def escritura_permitida(settings: SettingsDep) -> None:
    if settings.environment == "produccion":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere autenticación (HU-19, Sprint 2).")


WriteGuard = Depends(escritura_permitida)


def _commit_or_error(session: Session, exc: service.DatasetError) -> HTTPException:
    session.rollback()
    return HTTPException(exc.status_code, str(exc))


@router.post("/comercios", response_model=ComercioOut, status_code=201, dependencies=[WriteGuard])
def crear_comercio(body: ComercioCreate, session: SessionDep) -> Comercio:
    comercio = service.create_comercio(session, body.municipio, body.tipo_negocio)
    session.commit()
    return comercio


@router.get("/comercios", response_model=list[ComercioOut])
def listar_comercios(session: SessionDep) -> list[Comercio]:
    return list(session.scalars(select(Comercio).order_by(Comercio.id)))


@router.post(
    "/comercios/{comercio_id}/autorizaciones",
    response_model=AutorizacionOut,
    status_code=201,
    dependencies=[WriteGuard],
)
def registrar_autorizacion(
    comercio_id: int, body: AutorizacionCreate, session: SessionDep
) -> AutorizacionOut:
    try:
        aut = service.create_autorizacion(
            session, comercio_id, body.fecha, body.alcance, body.documento_ref
        )
    except service.DatasetError as exc:
        raise _commit_or_error(session, exc) from exc
    session.commit()
    return AutorizacionOut.model_validate(aut)


@router.get("/comercios/{comercio_id}/autorizaciones", response_model=list[AutorizacionOut])
def listar_autorizaciones(comercio_id: int, session: SessionDep) -> list[Autorizacion]:
    return list(
        session.scalars(
            select(Autorizacion)
            .where(Autorizacion.comercio_id == comercio_id)
            .order_by(Autorizacion.fecha.desc())
        )
    )


@router.get("/datasets", response_model=list[DatasetOut])
def listar_datasets(session: SessionDep, comercio_id: int | None = None) -> list[Dataset]:
    query = select(Dataset).options(selectinload(Dataset.versiones)).order_by(Dataset.id)
    if comercio_id is not None:
        query = query.where(Dataset.comercio_id == comercio_id)
    return list(session.scalars(query))


@router.get("/datasets/{dataset_id}", response_model=DatasetOut)
def obtener_dataset(dataset_id: int, session: SessionDep) -> Dataset:
    dataset = session.get(Dataset, dataset_id, options=[selectinload(Dataset.versiones)])
    if dataset is None:
        raise HTTPException(404, "El conjunto de datos no existe.")
    return dataset


def _version(session: Session, dataset_id: int, version: int) -> DatasetVersion:
    dv = session.scalar(
        select(DatasetVersion).where(
            DatasetVersion.dataset_id == dataset_id, DatasetVersion.version == version
        )
    )
    if dv is None:
        raise HTTPException(404, "La versión no existe.")
    return dv


@router.get("/datasets/{dataset_id}/versiones/{version}/calidad")
def calidad_version(dataset_id: int, version: int, session: SessionDep) -> dict[str, object]:
    return _version(session, dataset_id, version).reporte_calidad


@router.get("/datasets/{dataset_id}/versiones/{version}/series", response_model=list[SerieOut])
def series_version(dataset_id: int, version: int, session: SessionDep) -> list[SerieOut]:
    dv = _version(session, dataset_id, version)
    rows = session.execute(
        select(
            Serie.id,
            Serie.clave,
            Serie.nivel,
            func.count(Observacion.fecha),
            func.min(Observacion.fecha),
            func.max(Observacion.fecha),
        )
        .join(Observacion, Observacion.serie_id == Serie.id, isouter=True)
        .where(Serie.dataset_version_id == dv.id)
        .group_by(Serie.id)
        .order_by(Serie.clave)
    ).all()
    return [
        SerieOut(id=r[0], clave=r[1], nivel=r[2], observaciones=r[3], desde=r[4], hasta=r[5])
        for r in rows
    ]


@router.post(
    "/datasets/carga",
    response_model=CargaOut,
    status_code=201,
    dependencies=[WriteGuard],
    responses={422: {"model": ErrorCargaOut}, 409: {"model": ErrorCargaOut}},
)
async def cargar_ventas(
    session: SessionDep,
    settings: SettingsDep,
    archivo: Annotated[UploadFile, File(description="Plantilla de ventas en .csv o .xlsx")],
    comercio_id: Annotated[int, Form()],
    autorizacion_id: Annotated[int, Form()],
    nombre: Annotated[str, Form(max_length=120)] = "Ventas",
) -> CargaOut | JSONResponse:
    content = await archivo.read(settings.max_upload_mb * 1024 * 1024 + 1)
    try:
        version, nueva = service.upload_sales(
            session,
            settings,
            content=content,
            filename=archivo.filename or "ventas.csv",
            comercio_id=comercio_id,
            autorizacion_id=autorizacion_id,
            nombre=nombre,
        )
    except SalesValidationError as exc:
        session.rollback()
        body = ErrorCargaOut(
            detalle="El archivo no cumple la plantilla de ventas.",
            problemas=[ProblemaOut(**vars(p)) for p in exc.problemas],
        )
        return JSONResponse(body.model_dump(), status_code=422)
    except service.DatasetError as exc:
        session.rollback()
        return JSONResponse(ErrorCargaOut(detalle=str(exc)).model_dump(), exc.status_code)
    session.commit()
    return CargaOut(
        dataset_id=version.dataset_id,
        version=DatasetVersionOut.model_validate(version),
        nueva=nueva,
        reporte_calidad=version.reporte_calidad,
    )
