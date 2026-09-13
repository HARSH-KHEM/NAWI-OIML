"""Instrument and configuration API endpoints."""

from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.configuration import InstrumentConfiguration
from app.models.instrument import Instrument
from app.models.metrology import AuditEvent
from app.models.range import InstrumentConfigurationRange
from app.schemas.configuration import (
    InstrumentConfigurationCreate,
    InstrumentConfigurationRead,
)
from app.schemas.instrument import (
    InstrumentCreate,
    InstrumentRead,
)

router = APIRouter(tags=["Instruments"])


@router.post("/instruments", response_model=InstrumentRead, status_code=status.HTTP_201_CREATED)
def create_instrument(
    payload: InstrumentCreate,
    db: Session = Depends(get_db),
) -> Instrument:
    """Create a new weighing instrument identity."""
    inst = Instrument(
        manufacturer=payload.manufacturer,
        model_name=payload.model_name,
        instrument_family=payload.instrument_family,
        serial_number=payload.serial_number,
        status=payload.status,
        is_synthetic=payload.is_synthetic,
    )
    db.add(inst)
    db.flush()

    audit = AuditEvent(
        entity_type="INSTRUMENT",
        entity_id=inst.id,
        action="INSTRUMENT_CREATED",
        metadata_json={"manufacturer": inst.manufacturer, "model": inst.model_name},
    )
    db.add(audit)
    db.commit()
    db.refresh(inst)
    return inst


@router.get("/instruments", response_model=List[InstrumentRead])
def list_instruments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[Instrument]:
    """List all registered instruments."""
    return db.scalars(select(Instrument).offset(skip).limit(limit)).all()


@router.get("/instruments/{instrument_id}", response_model=InstrumentRead)
def get_instrument(
    instrument_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Instrument:
    """Retrieve an instrument by ID."""
    inst = db.get(Instrument, instrument_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return inst


@router.post(
    "/instruments/{instrument_id}/configurations",
    response_model=InstrumentConfigurationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_configuration(
    instrument_id: uuid.UUID,
    payload: InstrumentConfigurationCreate,
    db: Session = Depends(get_db),
) -> InstrumentConfiguration:
    """Create and link a metrological configuration to an instrument."""
    inst = db.get(Instrument, instrument_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")

    config = InstrumentConfiguration(
        instrument_id=instrument_id,
        accuracy_class=payload.accuracy_class,
        max_capacity=payload.max_capacity,
        min_capacity=payload.min_capacity,
        verification_scale_interval=payload.verification_scale_interval,
        actual_scale_interval=payload.actual_scale_interval,
        unit=payload.unit,
        number_of_ranges=payload.number_of_ranges,
        is_multiple_range=payload.is_multiple_range,
        tare_type=payload.tare_type,
        is_electronic=payload.is_electronic,
        has_zero_setting=payload.has_zero_setting,
        extra_capabilities=payload.extra_capabilities,
        is_active=payload.is_active,
    )
    db.add(config)
    db.flush()

    # If multiple ranges are provided, persist them
    if payload.ranges:
        for r_in in payload.ranges:
            r_row = InstrumentConfigurationRange(
                configuration_id=config.id,
                range_index=r_in.range_index,
                min_capacity=r_in.min_capacity,
                max_capacity=r_in.max_capacity,
                verification_scale_interval=r_in.verification_scale_interval,
                actual_scale_interval=r_in.actual_scale_interval,
                unit=r_in.unit,
            )
            db.add(r_row)

    audit = AuditEvent(
        entity_type="CONFIGURATION",
        entity_id=config.id,
        action="CONFIGURATION_CREATED",
        metadata_json={
            "instrument_id": str(instrument_id),
            "max": str(config.max_capacity),
            "e": str(config.verification_scale_interval),
            "is_multiple_range": config.is_multiple_range,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(config)
    return config


@router.get(
    "/instruments/{instrument_id}/configurations/{configuration_id}",
    response_model=InstrumentConfigurationRead,
)
def get_configuration(
    instrument_id: uuid.UUID,
    configuration_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> InstrumentConfiguration:
    """Retrieve a specific instrument configuration."""
    config = db.scalar(
        select(InstrumentConfiguration).where(
            InstrumentConfiguration.id == configuration_id,
            InstrumentConfiguration.instrument_id == instrument_id,
        )
    )
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config
