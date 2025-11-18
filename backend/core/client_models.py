"""
Pydantic models for client and campaign management.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# CLIENT MODELS
# ============================================================================

class ClientCreate(BaseModel):
    """Request model for creating a client."""
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    description: Optional[str] = Field(None, description="Client description")
    brand_guidelines: Optional[str] = Field(None, description="Brand guidelines and style information")


class ClientUpdate(BaseModel):
    """Request model for updating a client."""
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Client name")
    description: Optional[str] = Field(None, description="Client description")
    brand_guidelines: Optional[str] = Field(None, description="Brand guidelines and style information")


class Client(BaseModel):
    """Client response model."""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Client unique identifier")
    user_id: int = Field(..., description="User ID who owns this client")
    name: str = Field(..., description="Client name")
    description: Optional[str] = Field(None, description="Client description")
    brand_guidelines: Optional[str] = Field(None, description="Brand guidelines")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ============================================================================
# CAMPAIGN MODELS
# ============================================================================

class CampaignCreate(BaseModel):
    """Request model for creating a campaign."""
    model_config = ConfigDict(use_enum_values=True)

    client_id: str = Field(..., description="Client ID this campaign belongs to")
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    goal: str = Field(..., min_length=1, description="Campaign goal/objective")
    status: str = Field(default="draft", pattern="^(active|archived|draft)$", description="Campaign status")
    brief: Optional[str] = Field(None, description="Campaign brief")


class CampaignUpdate(BaseModel):
    """Request model for updating a campaign."""
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Campaign name")
    goal: Optional[str] = Field(None, min_length=1, description="Campaign goal/objective")
    status: Optional[str] = Field(None, pattern="^(active|archived|draft)$", description="Campaign status")
    brief: Optional[str] = Field(None, description="Campaign brief")


class Campaign(BaseModel):
    """Campaign response model."""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Campaign unique identifier")
    client_id: str = Field(..., description="Client ID")
    user_id: int = Field(..., description="User ID who owns this campaign")
    name: str = Field(..., description="Campaign name")
    goal: str = Field(..., description="Campaign goal/objective")
    status: str = Field(..., description="Campaign status")
    brief: Optional[str] = Field(None, description="Campaign brief")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ============================================================================
# LIST FILTERS
# ============================================================================

class ClientFilter(BaseModel):
    """Filter for client list queries."""
    model_config = ConfigDict(use_enum_values=True)

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
    search: Optional[str] = Field(None, description="Search by client name")


class CampaignFilter(BaseModel):
    """Filter for campaign list queries."""
    model_config = ConfigDict(use_enum_values=True)

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
    client_id: Optional[str] = Field(None, description="Filter by client ID")
    status: Optional[str] = Field(None, pattern="^(active|archived|draft)$", description="Filter by status")
    search: Optional[str] = Field(None, description="Search by campaign name")
