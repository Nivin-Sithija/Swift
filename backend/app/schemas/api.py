import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import (
    InterfaceLanguage,
    LanguageForm,
    TicketStatus,
    UserRole,
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["customer", "agent"] = "customer"
    preferred_language: InterfaceLanguage = InterfaceLanguage.english
    agent_registration_code: str | None = Field(default=None, max_length=256)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    preferred_language: InterfaceLanguage


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class TicketCreate(BaseModel):
    subject: str = Field(min_length=5, max_length=150)
    message: str = Field(min_length=15, max_length=5000)
    preferred_response_language: InterfaceLanguage = InterfaceLanguage.english


class PredictionOut(BaseModel):
    id: uuid.UUID
    task: str
    value: str
    confidence: float = Field(ge=0, le=1)
    model_version: str
    predicted_at: datetime


class EventOut(BaseModel):
    id: uuid.UUID
    label: str
    detail: str
    at: datetime
    customer_visible: bool


class NoteOut(BaseModel):
    id: uuid.UUID
    author: str
    text: str
    at: datetime


class AttachmentOut(BaseModel):
    id: uuid.UUID
    name: str
    size: int
    type: str
    download_url: str


class ResponseOut(BaseModel):
    id: uuid.UUID
    text: str
    language: InterfaceLanguage
    status: str
    updated_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None


class TicketOut(BaseModel):
    id: str
    internal_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str
    subject: str
    message: str
    preferred_response_language: InterfaceLanguage
    language: LanguageForm
    category: PredictionOut | None
    priority: PredictionOut | None
    sentiment: PredictionOut | None
    status: TicketStatus
    assigned_queue: str
    assigned_agent: str | None
    created_at: datetime
    updated_at: datetime
    attachments: list[AttachmentOut] = []
    events: list[EventOut] = []
    notes: list[NoteOut] = []
    responses: list[ResponseOut] = []
    requires_manual_review: bool
    escalation_reason: str | None
    version: int


class TicketList(BaseModel):
    items: list[TicketOut]
    page: int
    page_size: int
    total: int


class StatusUpdate(BaseModel):
    status: TicketStatus
    version: int | None = None


class AssignmentRequest(BaseModel):
    agent_id: uuid.UUID | None = None
    queue_id: uuid.UUID | None = None


class EscalationRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class NoteCreate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class PredictionReview(BaseModel):
    value: str = Field(min_length=1, max_length=150)
    reason: str = Field(min_length=3, max_length=1000)


class ResponseEdit(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


class DashboardOut(BaseModel):
    new_tickets: int
    assigned_to_me: int
    high_priority: int
    critical: int
    escalated: int
    resolved_today: int
    average_first_response: str
    low_confidence: int
    category_distribution: list["DashboardBreakdownItem"]
    language_distribution: list["DashboardBreakdownItem"]
    weekly_volume: list["DashboardTrendPoint"]


class DashboardBreakdownItem(BaseModel):
    label: str
    count: int


class DashboardTrendPoint(BaseModel):
    date: str
    count: int


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class AdminDashboardOut(BaseModel):
    customers: int
    agents: int
    administrators: int
    active_sessions: int
    open_tickets: int
    support_queues: int
    audit_events: int
    recent_users: list[AdminUserOut]


class AdminUserList(BaseModel):
    items: list[AdminUserOut]
    total: int


class AdminUserUpdate(BaseModel):
    role: Literal["customer", "agent", "administrator"] | None = None
    is_active: bool | None = None


class AdminQueueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    ticket_count: int = 0


class AdminQueueCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class AdminQueueUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None


class AdminAuditOut(BaseModel):
    id: uuid.UUID
    actor: str
    action: str
    entity_type: str
    entity_id: str
    detail: str | None
    created_at: datetime


class AdminAuditList(BaseModel):
    items: list[AdminAuditOut]
    total: int


class AdminSettingOut(BaseModel):
    key: str
    value: str
    value_type: str
    description: str
    updated_at: datetime


class AdminSettingsUpdate(BaseModel):
    values: dict[str, str]


class ErrorOut(BaseModel):
    code: str
    message: str
    request_id: str | None = None
