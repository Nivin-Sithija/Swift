import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, File, HTTPException, Query, UploadFile
from fastapi import Response as HttpResponse
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from app.api.dependencies import AdministratorUser, CurrentUser, Db, StaffUser
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.domain.enums import (
    JobStatus,
    LanguageForm,
    PredictionTask,
    Priority,
    ResponseStatus,
    Sentiment,
    TicketStatus,
    UserRole,
)
from app.domain.policies import can_transition, requires_manual_review
from app.inference.services import classify, detect_language, response_template
from app.models.entities import (
    Attachment,
    AuditLog,
    AuthSession,
    Prediction,
    ProcessingJob,
    Response,
    SupportQueue,
    SystemSetting,
    Ticket,
    TicketEvent,
    TicketNote,
    User,
    utcnow,
)
from app.rag.dependencies import ConsumerRAG
from app.schemas.api import (
    AdminAuditList,
    AdminAuditOut,
    AdminDashboardOut,
    AdminQueueCreate,
    AdminQueueOut,
    AdminQueueUpdate,
    AdminSettingOut,
    AdminSettingsUpdate,
    AdminUserList,
    AdminUserOut,
    AdminUserUpdate,
    AssignmentRequest,
    AttachmentOut,
    ConsumerAssistanceOut,
    ConsumerAssistanceRequest,
    DashboardBreakdownItem,
    DashboardOut,
    DashboardTrendPoint,
    EscalationRequest,
    EventOut,
    LoginRequest,
    NoteCreate,
    NoteOut,
    PredictionOut,
    PredictionReview,
    RegisterRequest,
    ResponseEdit,
    ResponseOut,
    StatusUpdate,
    TicketCreate,
    TicketList,
    TicketOut,
    TokenResponse,
    UserOut,
)

router = APIRouter()
settings = get_settings()


def event(
    ticket: Ticket, actor: User | None, kind: str, detail: str, visible: bool = False
) -> None:
    ticket.events.append(
        TicketEvent(
            actor_id=actor.id if actor else None,
            event_type=kind,
            detail=detail,
            customer_visible=visible,
        )
    )


def audit(
    db: AsyncSession, actor: User, action: str, entity: str, entity_id: str, detail: str = ""
) -> None:
    db.add(
        AuditLog(
            user_id=actor.id, action=action, entity_type=entity, entity_id=entity_id, detail=detail
        )
    )


def prediction_out(p: Prediction | None) -> PredictionOut | None:
    return (
        None
        if p is None
        else PredictionOut(
            id=p.id,
            task=p.task.value,
            value=p.reviewed_value or p.value,
            confidence=p.confidence,
            model_version=p.model_version,
            predicted_at=p.predicted_at,
        )
    )


def ticket_out(ticket: Ticket, *, staff_view: bool) -> TicketOut:
    by_task = {p.task: p for p in ticket.predictions}
    visible_responses = (
        ticket.responses
        if staff_view
        else [
            r
            for r in ticket.responses
            if r.status in {ResponseStatus.approved, ResponseStatus.sent}
        ]
    )
    return TicketOut(
        id=ticket.public_id,
        internal_id=ticket.id,
        customer_id=ticket.customer_id,
        customer_name=ticket.customer.full_name,
        subject=ticket.subject,
        message=ticket.original_text,
        preferred_response_language=ticket.response_language,
        language=ticket.language,
        category=prediction_out(by_task.get(PredictionTask.category)),
        priority=prediction_out(by_task.get(PredictionTask.priority)),
        sentiment=prediction_out(by_task.get(PredictionTask.sentiment)),
        status=ticket.status,
        assigned_queue=ticket.queue.name if ticket.queue else "General Support",
        assigned_agent=ticket.assigned_agent.full_name if ticket.assigned_agent else None,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        attachments=[
            AttachmentOut(
                id=a.id,
                name=a.filename,
                size=a.size,
                type=a.mime_type,
                download_url=f"/api/v1/attachments/{a.id}/download",
            )
            for a in ticket.attachments
        ],
        events=[
            EventOut(
                id=e.id,
                label=e.event_type.replace("_", " ").title(),
                detail=e.detail,
                at=e.created_at,
                customer_visible=e.customer_visible,
            )
            for e in ticket.events
            if staff_view or e.customer_visible
        ],
        notes=[
            NoteOut(id=n.id, author=n.author.full_name, text=n.text, at=n.created_at)
            for n in ticket.notes
        ]
        if staff_view
        else [],
        responses=[
            ResponseOut(
                id=r.id,
                text=r.text,
                language=r.language,
                status=r.status.value,
                updated_at=r.updated_at,
                approved_at=r.approved_at,
            )
            for r in visible_responses
        ],
        requires_manual_review=ticket.manual_review_required,
        escalation_reason=ticket.escalation_reason,
        version=ticket.version,
    )


def ticket_options() -> tuple[ORMOption, ...]:
    return (
        selectinload(Ticket.customer),
        selectinload(Ticket.assigned_agent),
        selectinload(Ticket.queue),
        selectinload(Ticket.predictions),
        selectinload(Ticket.events),
        selectinload(Ticket.notes).selectinload(TicketNote.author),
        selectinload(Ticket.responses),
        selectinload(Ticket.attachments),
    )


async def get_ticket(db: AsyncSession, public_id: str, user: User) -> Ticket:
    ticket = await db.scalar(
        select(Ticket).where(Ticket.public_id == public_id).options(*ticket_options())
    )
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    if user.role == UserRole.customer and ticket.customer_id != user.id:
        raise HTTPException(404, "Ticket not found")
    return ticket


@router.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "swift-api"}


@router.post("/consumer-assistance/drafts", response_model=ConsumerAssistanceOut, tags=["RAG"])
async def create_consumer_assistance_draft(
    payload: ConsumerAssistanceRequest, _user: StaffUser, service: ConsumerRAG
) -> ConsumerAssistanceOut:
    """Create a safety-routed draft. This endpoint never approves or sends it."""
    result = await service.assist(**payload.model_dump())
    return ConsumerAssistanceOut.model_validate(result, from_attributes=True)


@router.get("/ready", tags=["Health"])
async def ready(db: Db) -> dict[str, str]:
    await db.scalar(select(1))
    return {"status": "ready"}


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(
    payload: RegisterRequest, response: HttpResponse, db: Db
) -> TokenResponse:
    email = payload.email.lower()
    if await db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(409, "An account with this email already exists")
    role = UserRole(payload.role)
    if role == UserRole.agent:
        configured_code = settings.agent_registration_code
        provided_code = payload.agent_registration_code or ""
        if not configured_code:
            raise HTTPException(503, "Support-agent registration is not configured")
        if not secrets.compare_digest(provided_code, configured_code):
            raise HTTPException(403, "Invalid support-agent registration code")
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=role,
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    await db.flush()
    raw, hashed = new_refresh_token()
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hashed,
            expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        )
    )
    await db.commit()
    response.set_cookie(
        "swift_refresh",
        raw,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.refresh_token_days * 86400,
        path="/api/v1/auth",
    )
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=settings.access_token_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: HttpResponse, db: Db) -> TokenResponse:
    user = await db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    raw, hashed = new_refresh_token()
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hashed,
            expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        )
    )
    await db.commit()
    response.set_cookie(
        "swift_refresh",
        raw,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.refresh_token_days * 86400,
        path="/api/v1/auth",
    )
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=settings.access_token_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    response: HttpResponse, db: Db, swift_refresh: Annotated[str | None, Cookie()] = None
) -> TokenResponse:
    if not swift_refresh:
        raise HTTPException(401, "Refresh token missing")
    session = await db.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_refresh_token(swift_refresh))
    )
    if not session or session.revoked_at or session.expires_at <= utcnow():
        raise HTTPException(401, "Refresh token invalid")
    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "Account unavailable")
    session.revoked_at = utcnow()
    raw, hashed = new_refresh_token()
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hashed,
            expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        )
    )
    await db.commit()
    response.set_cookie(
        "swift_refresh",
        raw,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.refresh_token_days * 86400,
        path="/api/v1/auth",
    )
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=settings.access_token_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/auth/logout", status_code=204)
async def logout(
    response: HttpResponse, db: Db, swift_refresh: Annotated[str | None, Cookie()] = None
) -> None:
    if swift_refresh:
        session = await db.scalar(
            select(AuthSession).where(AuthSession.token_hash == hash_refresh_token(swift_refresh))
        )
        if session:
            session.revoked_at = utcnow()
            await db.commit()
    response.delete_cookie("swift_refresh", path="/api/v1/auth")


@router.get("/users/me", response_model=UserOut)
async def me(user: CurrentUser) -> User:
    return user


@router.post("/tickets", response_model=TicketOut, status_code=201)
async def create_ticket(payload: TicketCreate, user: CurrentUser, db: Db) -> TicketOut:
    if user.role != UserRole.customer:
        raise HTTPException(403, "Only customers can submit tickets")
    count = (await db.scalar(select(func.count(Ticket.id)))) or 0
    public_id = f"SW-{datetime.now(UTC).year}-{count + 1:06d}"
    queue = await db.scalar(select(SupportQueue).where(SupportQueue.name == "General Support"))
    ticket = Ticket(
        public_id=public_id,
        customer_id=user.id,
        queue_id=queue.id if queue else None,
        subject=payload.subject,
        original_text=payload.message,
        response_language=payload.preferred_response_language,
    )
    event(ticket, user, "ticket_created", "Ticket received securely", True)
    db.add(ticket)
    await db.flush()
    await process_ticket_record(db, ticket)
    await db.commit()
    return ticket_out(await get_ticket(db, public_id, user), staff_view=False)


async def process_ticket_record(db: AsyncSession, ticket: Ticket) -> None:
    job = ProcessingJob(ticket_id=ticket.id, job_type="ticket_analysis", status=JobStatus.running)
    db.add(job)
    language = detect_language(ticket.original_text)
    intent, priority, sentiment = classify(ticket.original_text)
    for task, result in (
        (PredictionTask.language, language),
        (PredictionTask.category, intent),
        (PredictionTask.priority, priority),
        (PredictionTask.sentiment, sentiment),
    ):
        db.add(
            Prediction(
                ticket_id=ticket.id,
                task=task,
                value=result.value,
                confidence=result.confidence,
                model_version=result.model_version,
            )
        )
    ticket.language = LanguageForm(language.value)
    ticket.priority = Priority(priority.value)
    ticket.sentiment = Sentiment(sentiment.value)
    ticket.manual_review_required = requires_manual_review(
        confidence_values=[intent.confidence, priority.confidence, sentiment.confidence],
        priority=ticket.priority,
        sentiment=ticket.sentiment,
        category=intent.value,
    )
    ticket.status = TicketStatus.in_review
    ticket.responses.append(
        Response(
            text=response_template(ticket.response_language.value),
            language=ticket.response_language,
        )
    )
    event(ticket, None, "processing_completed", "Advisory predictions prepared", True)
    job.status, job.completed_at = JobStatus.succeeded, utcnow()


@router.get("/tickets", response_model=TicketList)
async def list_tickets(
    user: CurrentUser,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: str | None = None,
    status: TicketStatus | None = None,
    priority: Priority | None = None,
) -> TicketList:
    filters = []
    if user.role == UserRole.customer:
        filters.append(Ticket.customer_id == user.id)
    if query:
        filters.append(
            or_(
                Ticket.subject.ilike(f"%{query}%"),
                Ticket.original_text.ilike(f"%{query}%"),
                Ticket.public_id.ilike(f"%{query}%"),
            )
        )
    if status:
        filters.append(Ticket.status == status)
    if priority:
        filters.append(Ticket.priority == priority)
    total = (await db.scalar(select(func.count(Ticket.id)).where(*filters))) or 0
    stmt = (
        select(Ticket)
        .where(*filters)
        .options(*ticket_options())
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.scalars(stmt)).unique().all()
    return TicketList(
        items=[ticket_out(t, staff_view=user.role != UserRole.customer) for t in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
async def ticket_detail(ticket_id: str, user: CurrentUser, db: Db) -> TicketOut:
    ticket = await get_ticket(db, ticket_id, user)
    return ticket_out(ticket, staff_view=user.role != UserRole.customer)


@router.post("/tickets/{ticket_id}/notes", response_model=NoteOut, status_code=201)
async def add_note(ticket_id: str, payload: NoteCreate, user: StaffUser, db: Db) -> NoteOut:
    ticket = await get_ticket(db, ticket_id, user)
    note = TicketNote(ticket_id=ticket.id, author_id=user.id, text=payload.text)
    db.add(note)
    event(ticket, user, "note_added", "Internal note added")
    audit(db, user, "note_added", "ticket", ticket.public_id)
    await db.commit()
    await db.refresh(note)
    return NoteOut(id=note.id, author=user.full_name, text=note.text, at=note.created_at)


@router.put("/tickets/{ticket_id}/status", response_model=TicketOut)
async def set_status(ticket_id: str, payload: StatusUpdate, user: StaffUser, db: Db) -> TicketOut:
    ticket = await get_ticket(db, ticket_id, user)
    if payload.version is not None and payload.version != ticket.version:
        raise HTTPException(409, "Ticket was updated by another user")
    if not can_transition(ticket.status, payload.status):
        raise HTTPException(409, f"Cannot transition from {ticket.status} to {payload.status}")
    old = ticket.status
    ticket.status = payload.status
    ticket.version += 1
    event(
        ticket,
        user,
        "status_changed",
        f"Status changed from {old.value} to {payload.status.value}",
        True,
    )
    audit(db, user, "status_changed", "ticket", ticket.public_id)
    await db.commit()
    return ticket_out(await get_ticket(db, ticket_id, user), staff_view=True)


@router.put("/tickets/{ticket_id}/assignment", response_model=TicketOut)
async def assign(ticket_id: str, payload: AssignmentRequest, user: StaffUser, db: Db) -> TicketOut:
    ticket = await get_ticket(db, ticket_id, user)
    agent_id = payload.agent_id or user.id
    agent = await db.get(User, agent_id)
    if not agent or agent.role not in {UserRole.agent, UserRole.administrator}:
        raise HTTPException(400, "Target user is not an active agent")
    ticket.assigned_agent_id = agent.id
    if payload.queue_id:
        ticket.queue_id = payload.queue_id
    ticket.status = TicketStatus.assigned
    ticket.version += 1
    event(ticket, user, "agent_assigned", f"Assigned to {agent.full_name}", True)
    audit(db, user, "agent_assigned", "ticket", ticket.public_id)
    await db.commit()
    return ticket_out(await get_ticket(db, ticket_id, user), staff_view=True)


@router.post("/tickets/{ticket_id}/escalate", response_model=TicketOut)
async def escalate(
    ticket_id: str, payload: EscalationRequest, user: StaffUser, db: Db
) -> TicketOut:
    ticket = await get_ticket(db, ticket_id, user)
    queue = await db.scalar(select(SupportQueue).where(SupportQueue.name == "Fraud & Security"))
    ticket.status = TicketStatus.escalated
    ticket.escalation_reason = payload.reason
    if queue:
        ticket.queue_id = queue.id
    ticket.version += 1
    event(ticket, user, "escalated", payload.reason, True)
    audit(db, user, "escalated", "ticket", ticket.public_id, payload.reason)
    await db.commit()
    return ticket_out(await get_ticket(db, ticket_id, user), staff_view=True)


@router.put("/predictions/{prediction_id}/reviews", response_model=PredictionOut)
async def review_prediction(
    prediction_id: uuid.UUID, payload: PredictionReview, user: StaffUser, db: Db
) -> PredictionOut:
    prediction = await db.get(Prediction, prediction_id)
    if not prediction:
        raise HTTPException(404, "Prediction not found")
    prediction.reviewed_value, prediction.review_reason, prediction.reviewed_by = (
        payload.value,
        payload.reason,
        user.id,
    )
    ticket = await db.get(Ticket, prediction.ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    if prediction.task == PredictionTask.priority:
        ticket.priority = Priority(payload.value)
    elif prediction.task == PredictionTask.sentiment:
        ticket.sentiment = Sentiment(payload.value)
    event(ticket, user, f"{prediction.task.value}_corrected", payload.reason)
    audit(db, user, "prediction_reviewed", "prediction", str(prediction.id), payload.reason)
    await db.commit()
    await db.refresh(prediction)
    return prediction_out(prediction)  # type: ignore[return-value]


@router.post("/tickets/{ticket_id}/attachments", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    ticket_id: str,
    user: CurrentUser,
    db: Db,
    file: Annotated[UploadFile, File()],
) -> AttachmentOut:
    ticket = await get_ticket(db, ticket_id, user)
    allowed = {"image/png": b"\x89PNG", "image/jpeg": b"\xff\xd8\xff", "application/pdf": b"%PDF"}
    if file.content_type not in allowed:
        raise HTTPException(415, "Unsupported attachment type")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "Attachment too large")
    if not data.startswith(allowed[file.content_type]):
        raise HTTPException(415, "File signature does not match its type")
    identifier = uuid.uuid4()
    suffix = {"image/png": ".png", "image/jpeg": ".jpg", "application/pdf": ".pdf"}[
        file.content_type
    ]
    directory = settings.storage_root / str(ticket.id)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{identifier}{suffix}"
    path.write_bytes(data)
    attachment = Attachment(
        id=identifier,
        ticket_id=ticket.id,
        uploaded_by=user.id,
        filename=Path(file.filename or "attachment").name,
        storage_path=str(path),
        mime_type=file.content_type,
        size=len(data),
        file_hash=hashlib.sha256(data).hexdigest(),
    )
    db.add(attachment)
    event(ticket, user, "attachment_uploaded", "Attachment validated and stored", True)
    await db.commit()
    return AttachmentOut(
        id=attachment.id,
        name=attachment.filename,
        size=attachment.size,
        type=attachment.mime_type,
        download_url=f"/api/v1/attachments/{attachment.id}/download",
    )


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(attachment_id: uuid.UUID, user: CurrentUser, db: Db) -> FileResponse:
    attachment = await db.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(404, "Attachment not found")
    ticket = await db.get(Ticket, attachment.ticket_id)
    if not ticket or (user.role == UserRole.customer and ticket.customer_id != user.id):
        raise HTTPException(404, "Attachment not found")
    path = Path(attachment.storage_path).resolve()
    root = settings.storage_root.resolve()
    if not path.is_relative_to(root) or not path.exists():
        raise HTTPException(404, "Attachment unavailable")
    return FileResponse(path, media_type=attachment.mime_type, filename=attachment.filename)


@router.patch("/responses/{response_id}", response_model=ResponseOut)
async def edit_response(
    response_id: uuid.UUID, payload: ResponseEdit, user: StaffUser, db: Db
) -> Response:
    response = await db.get(Response, response_id)
    if not response:
        raise HTTPException(404, "Response not found")
    if response.status in {ResponseStatus.approved, ResponseStatus.sent}:
        raise HTTPException(409, "Approved response cannot be edited")
    response.text, response.status, response.author_id = (
        payload.text,
        ResponseStatus.agent_edited,
        user.id,
    )
    await db.commit()
    await db.refresh(response)
    return response


@router.post("/responses/{response_id}/approve", response_model=ResponseOut)
async def approve_response(response_id: uuid.UUID, user: StaffUser, db: Db) -> Response:
    response = await db.get(Response, response_id)
    if not response:
        raise HTTPException(404, "Response not found")
    response.status, response.approved_by, response.approved_at = (
        ResponseStatus.approved,
        user.id,
        utcnow(),
    )
    ticket = await db.get(Ticket, response.ticket_id)
    assert ticket
    ticket.status = TicketStatus.response_draft
    event(ticket, user, "response_approved", "Response approved by an authorised agent")
    await db.commit()
    await db.refresh(response)
    return response


@router.post("/responses/{response_id}/reject", response_model=ResponseOut)
async def reject_response(response_id: uuid.UUID, user: StaffUser, db: Db) -> Response:
    response = await db.get(Response, response_id)
    if not response:
        raise HTTPException(404, "Response not found")
    if response.status == ResponseStatus.sent:
        raise HTTPException(409, "Sent response cannot be rejected")
    response.status = ResponseStatus.rejected
    await db.commit()
    await db.refresh(response)
    return response


@router.post("/responses/{response_id}/send", response_model=ResponseOut)
async def send_response(response_id: uuid.UUID, user: StaffUser, db: Db) -> Response:
    response = await db.get(Response, response_id)
    if not response:
        raise HTTPException(404, "Response not found")
    if response.status == ResponseStatus.sent:
        return response
    if response.status != ResponseStatus.approved:
        raise HTTPException(409, "Only approved responses can be sent")
    response.status, response.sent_at = ResponseStatus.sent, utcnow()
    ticket = await db.get(Ticket, response.ticket_id)
    assert ticket
    ticket.status = TicketStatus.responded
    event(ticket, user, "response_sent", "Reviewed response made customer-visible", True)
    await db.commit()
    await db.refresh(response)
    return response


@router.get("/dashboard/metrics", response_model=DashboardOut)
async def dashboard(user: StaffUser, db: Db) -> DashboardOut:
    async def count(*conditions: Any) -> int:
        return (await db.scalar(select(func.count(Ticket.id)).where(*conditions))) or 0

    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    tickets = (
        await db.scalars(select(Ticket).options(selectinload(Ticket.category)))
    ).all()
    category_counts: dict[str, int] = {}
    language_counts: dict[str, int] = {}
    for ticket in tickets:
        category = ticket.category.display_name if ticket.category else "Unclassified"
        category_counts[category] = category_counts.get(category, 0) + 1
        language = ticket.language.value.replace("code_mixed", "mixed").title()
        language_counts[language] = language_counts.get(language, 0) + 1
    response_durations = [
        (response.sent_at - ticket.created_at).total_seconds()
        for response, ticket in (
            await db.execute(
                select(Response, Ticket)
                .join(Ticket, Ticket.id == Response.ticket_id)
                .where(Response.sent_at.is_not(None))
            )
        ).all()
        if response.sent_at is not None and response.sent_at >= ticket.created_at
    ]
    if response_durations:
        average_minutes = round(sum(response_durations) / len(response_durations) / 60)
        average_first_response = (
            f"{average_minutes} min"
            if average_minutes < 60
            else f"{average_minutes / 60:.1f} hr"
        )
    else:
        average_first_response = "Not available"
    weekly_volume = []
    for days_ago in range(6, -1, -1):
        day = (today - timedelta(days=days_ago)).date()
        weekly_volume.append(
            DashboardTrendPoint(
                date=day.isoformat(),
                count=sum(ticket.created_at.date() == day for ticket in tickets),
            )
        )
    return DashboardOut(
        new_tickets=await count(Ticket.status == TicketStatus.new),
        assigned_to_me=await count(Ticket.assigned_agent_id == user.id),
        high_priority=await count(Ticket.priority == Priority.high),
        critical=await count(Ticket.priority == Priority.critical),
        escalated=await count(Ticket.status == TicketStatus.escalated),
        resolved_today=await count(
            Ticket.status == TicketStatus.resolved, Ticket.updated_at >= today
        ),
        average_first_response=average_first_response,
        low_confidence=await count(Ticket.manual_review_required.is_(True)),
        category_distribution=[
            DashboardBreakdownItem(label=label, count=value)
            for label, value in sorted(
                category_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        language_distribution=[
            DashboardBreakdownItem(label=label, count=value)
            for label, value in sorted(
                language_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        weekly_volume=weekly_volume,
    )


@router.get("/admin/dashboard", response_model=AdminDashboardOut)
async def admin_dashboard(_user: AdministratorUser, db: Db) -> AdminDashboardOut:
    async def user_count(role: UserRole) -> int:
        return (await db.scalar(select(func.count(User.id)).where(User.role == role))) or 0

    now = utcnow()
    closed = {TicketStatus.resolved, TicketStatus.closed}
    recent = (
        await db.scalars(select(User).order_by(User.created_at.desc()).limit(6))
    ).all()
    return AdminDashboardOut(
        customers=await user_count(UserRole.customer),
        agents=await user_count(UserRole.agent),
        administrators=await user_count(UserRole.administrator),
        active_sessions=(
            await db.scalar(
                select(func.count(AuthSession.id)).where(
                    AuthSession.revoked_at.is_(None), AuthSession.expires_at > now
                )
            )
        )
        or 0,
        open_tickets=(
            await db.scalar(select(func.count(Ticket.id)).where(Ticket.status.not_in(closed)))
        )
        or 0,
        support_queues=(await db.scalar(select(func.count(SupportQueue.id)))) or 0,
        audit_events=(await db.scalar(select(func.count(AuditLog.id)))) or 0,
        recent_users=[AdminUserOut.model_validate(user) for user in recent],
    )


@router.get("/admin/users", response_model=AdminUserList)
async def admin_users(_admin: AdministratorUser, db: Db, query: str | None = None) -> AdminUserList:
    conditions = []
    if query:
        conditions.append(or_(User.full_name.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")))
    users = (await db.scalars(select(User).where(*conditions).order_by(User.created_at.desc()))).all()
    return AdminUserList(items=[AdminUserOut.model_validate(user) for user in users], total=len(users))


@router.patch("/admin/users/{user_id}", response_model=AdminUserOut)
async def admin_update_user(user_id: uuid.UUID, payload: AdminUserUpdate, admin: AdministratorUser, db: Db) -> AdminUserOut:
    user = await db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    if user.id == admin.id and (payload.is_active is False or (payload.role and payload.role != "administrator")):
        raise HTTPException(409, "You cannot remove your own administrator access")
    if user.role == UserRole.administrator and (payload.is_active is False or (payload.role and payload.role != "administrator")):
        active_admins = (await db.scalar(select(func.count(User.id)).where(User.role == UserRole.administrator, User.is_active.is_(True)))) or 0
        if active_admins <= 1: raise HTTPException(409, "At least one active administrator is required")
    changes = []
    if payload.role is not None and user.role.value != payload.role:
        changes.append(f"role:{user.role.value}->{payload.role}"); user.role = UserRole(payload.role)
    if payload.is_active is not None and user.is_active != payload.is_active:
        changes.append(f"active:{user.is_active}->{payload.is_active}"); user.is_active = payload.is_active
        if not payload.is_active:
            sessions = (await db.scalars(select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)))).all()
            for session in sessions: session.revoked_at = utcnow()
    audit(db, admin, "user_updated", "user", str(user.id), ";".join(changes))
    await db.commit(); await db.refresh(user)
    return AdminUserOut.model_validate(user)


@router.get("/admin/queues", response_model=list[AdminQueueOut])
async def admin_queues(_admin: AdministratorUser, db: Db) -> list[AdminQueueOut]:
    rows = (await db.execute(select(SupportQueue, func.count(Ticket.id)).outerjoin(Ticket, Ticket.queue_id == SupportQueue.id).group_by(SupportQueue.id).order_by(SupportQueue.name))).all()
    return [AdminQueueOut(id=q.id, name=q.name, description=q.description, is_active=q.is_active, ticket_count=count) for q, count in rows]


@router.post("/admin/queues", response_model=AdminQueueOut, status_code=201)
async def admin_create_queue(payload: AdminQueueCreate, admin: AdministratorUser, db: Db) -> AdminQueueOut:
    if await db.scalar(select(SupportQueue.id).where(func.lower(SupportQueue.name) == payload.name.strip().lower())): raise HTTPException(409, "Queue name already exists")
    queue = SupportQueue(name=payload.name.strip(), description=payload.description, is_active=True); db.add(queue); await db.flush()
    audit(db, admin, "queue_created", "support_queue", str(queue.id), queue.name); await db.commit(); await db.refresh(queue)
    return AdminQueueOut.model_validate(queue)


@router.patch("/admin/queues/{queue_id}", response_model=AdminQueueOut)
async def admin_update_queue(queue_id: uuid.UUID, payload: AdminQueueUpdate, admin: AdministratorUser, db: Db) -> AdminQueueOut:
    queue = await db.get(SupportQueue, queue_id)
    if not queue: raise HTTPException(404, "Queue not found")
    open_count = (await db.scalar(select(func.count(Ticket.id)).where(Ticket.queue_id == queue.id, Ticket.status.not_in({TicketStatus.resolved, TicketStatus.closed})))) or 0
    if payload.is_active is False and open_count: raise HTTPException(409, "Move or resolve open tickets before deactivating this queue")
    if payload.name is not None: queue.name = payload.name.strip()
    if payload.description is not None: queue.description = payload.description
    if payload.is_active is not None: queue.is_active = payload.is_active
    audit(db, admin, "queue_updated", "support_queue", str(queue.id), queue.name); await db.commit(); await db.refresh(queue)
    return AdminQueueOut(id=queue.id, name=queue.name, description=queue.description, is_active=queue.is_active, ticket_count=open_count)


@router.get("/admin/audit-logs", response_model=AdminAuditList)
async def admin_audit_logs(_admin: AdministratorUser, db: Db, query: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)) -> AdminAuditList:
    conditions = [or_(AuditLog.action.ilike(f"%{query}%"), AuditLog.entity_type.ilike(f"%{query}%"), AuditLog.detail.ilike(f"%{query}%"))] if query else []
    total = (await db.scalar(select(func.count(AuditLog.id)).where(*conditions))) or 0
    logs = (await db.scalars(select(AuditLog).where(*conditions).order_by(AuditLog.created_at.desc()).offset((page-1)*page_size).limit(page_size))).all()
    users = {u.id: u.full_name for u in (await db.scalars(select(User))).all()}
    return AdminAuditList(items=[AdminAuditOut(id=x.id, actor=users.get(x.user_id, "System"), action=x.action, entity_type=x.entity_type, entity_id=x.entity_id, detail=x.detail, created_at=x.created_at) for x in logs], total=total)


SETTING_DEFINITIONS = {
    "customer_registration_enabled": ("true", "boolean", "Allow customers to create accounts"),
    "agent_registration_enabled": ("true", "boolean", "Allow invite-code support-agent registration"),
    "low_confidence_threshold": ("0.60", "number", "Predictions below this confidence require review"),
    "max_upload_mb": ("10", "integer", "Maximum attachment size in megabytes"),
    "maintenance_message": ("", "string", "Optional customer-facing maintenance message"),
}

@router.get("/admin/settings", response_model=list[AdminSettingOut])
async def admin_settings(_admin: AdministratorUser, db: Db) -> list[AdminSettingOut]:
    existing = {x.key: x for x in (await db.scalars(select(SystemSetting))).all()}
    return [AdminSettingOut(key=key, value=existing[key].value if key in existing else default, value_type=kind, description=description, updated_at=existing[key].updated_at if key in existing else utcnow()) for key,(default,kind,description) in SETTING_DEFINITIONS.items()]

@router.patch("/admin/settings", response_model=list[AdminSettingOut])
async def admin_update_settings(payload: AdminSettingsUpdate, admin: AdministratorUser, db: Db) -> list[AdminSettingOut]:
    for key, value in payload.values.items():
        if key not in SETTING_DEFINITIONS: raise HTTPException(400, f"Setting is not configurable: {key}")
        default, kind, description = SETTING_DEFINITIONS[key]
        if kind == "boolean" and value not in {"true", "false"}: raise HTTPException(422, f"{key} must be true or false")
        if kind == "number" and not 0 <= float(value) <= 1: raise HTTPException(422, f"{key} must be between 0 and 1")
        if kind == "integer" and not 1 <= int(value) <= 100: raise HTTPException(422, f"{key} must be between 1 and 100")
        setting = await db.get(SystemSetting, key)
        if setting: setting.value, setting.updated_by = value, admin.id
        else: db.add(SystemSetting(key=key, value=value, value_type=kind, description=description, updated_by=admin.id))
        audit(db, admin, "system_setting_changed", "system_setting", key, "value updated")
    await db.commit(); return await admin_settings(admin, db)
