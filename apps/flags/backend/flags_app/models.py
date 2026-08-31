"""Feature flag domain model and lifecycle states."""

from enum import Enum

from pydantic import BaseModel, Field


class FlagState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class FeatureFlag(BaseModel):
    id: str
    key: str
    description: str
    owner_team: str
    state: FlagState
    staging_enabled: bool = False
    prod_enabled: bool = False
    prod_rollout_pct: int = 0
    created_at: str
    updated_by: str | None = None
    change_note: str | None = None


class CreateInput(BaseModel):
    key: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_team: str = Field(min_length=1)


class ActivateInput(BaseModel):
    pass


class SetStagingInput(BaseModel):
    enabled: bool


class SetProductionInput(BaseModel):
    enabled: bool
    reason: str = Field(min_length=1)


class SetRolloutInput(BaseModel):
    percentage: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1)


class ArchiveInput(BaseModel):
    note: str = Field(min_length=1)
