"""Idempotent demo seed covering every persistent support-workflow entity."""

import asyncio
import base64
import csv
import hashlib
import uuid
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.domain.enums import (
    InterfaceLanguage,
    JobStatus,
    LanguageForm,
    PredictionTask,
    Priority,
    ResponseStatus,
    Sentiment,
    TicketStatus,
    UserRole,
)
from app.models.entities import (
    Attachment,
    AuditLog,
    Category,
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

NAMESPACE = uuid.UUID("9f4210bc-14e8-4f71-8a79-4f1387c03ef0")
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def stable_id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{kind}:{key}")


TICKET_SEEDS = (
    ("Card payment reversed", "My card payment failed at the shop but the amount is still deducted.", LanguageForm.english, "card_payment_wrong_exchange_rate"),
    ("ATM issue", "ATM එකෙන් සල්ලි ආවේ නැහැ, නමුත් account එකෙන් amount එක අඩු වෙලා.", LanguageForm.code_mixed, "cash_withdrawal_not_received"),
    ("பணம் கிடைக்கவில்லை", "ATM இல் பணம் எடுக்க முயன்றேன், ஆனால் பணம் வரவில்லை.", LanguageForm.tamil, "cash_withdrawal_not_received"),
    ("Transfer pending", "mage transfer eka dawas dekak thisse pending. check karanna.", LanguageForm.singlish, "pending_transfer"),
    ("Beneficiary blocked", "en beneficiary add panna mudiyala. error kaatudhu.", LanguageForm.tanglish, "beneficiary_not_allowed"),
    ("Cannot access account", "I cannot sign in after changing my phone.", LanguageForm.english, "cash_withdrawal"),
    ("PIN අමතක වුණා", "මගේ card PIN එක අමතක වුණා. Reset කරන්නේ කොහොමද?", LanguageForm.code_mixed, "cash_withdrawal"),
    ("Suspicious transaction", "I do not recognise a card transaction made this morning.", LanguageForm.english, "card_payment_wrong_exchange_rate"),
    ("Card dispute", "කාඩ් ගනුදෙනුවක් සම්බන්ධයෙන් පැමිණිල්ලක් කරන්න ඕන.", LanguageForm.sinhala, "card_payment_wrong_exchange_rate"),
    ("Cash transfer problem", "cash transfer eka recipient ta gihin naha.", LanguageForm.singlish, "cash_transfer"),
    ("Loan enquiry", "What documents are required for a personal loan?", LanguageForm.english, "cash_transfer"),
    ("அடையாள சரிபார்ப்பு", "எனது அடையாளச் சரிபார்ப்பு தொடர்ந்து தோல்வியடைகிறது.", LanguageForm.tamil, "beneficiary_not_allowed"),
    ("Cash deposit missing", "I deposited cash but it is not shown in my account.", LanguageForm.english, "cash_transfer"),
    ("Card delivery late", "en card delivery innum varala. status sollunga.", LanguageForm.tanglish, "cash_withdrawal"),
    ("Account information", "කරුණාකර savings account fees ගැන විස්තර දෙන්න.", LanguageForm.code_mixed, "beneficiary_not_allowed"),
)


async def seed() -> None:
    settings = get_settings()
    async with SessionLocal() as db:
        queues: dict[str, SupportQueue] = {}
        for name, description in (
            ("General Support", "Default multilingual support queue"),
            ("Payments", "Card, transfer, cash, and payment investigations"),
            ("Fraud & Security", "Urgent fraud, access, and security review"),
        ):
            queue = await db.scalar(select(SupportQueue).where(SupportQueue.name == name))
            if not queue:
                queue = SupportQueue(id=stable_id("queue", name), name=name, description=description)
                db.add(queue)
                await db.flush()
            queues[name] = queue

        users: dict[str, User] = {}
        user_specs = (
            ("Maya Silva", "customer@swift.demo", UserRole.customer, InterfaceLanguage.english),
            ("Nimal Perera", "nimal@swift.demo", UserRole.customer, InterfaceLanguage.sinhala),
            ("Arun Kumar", "arun@swift.demo", UserRole.customer, InterfaceLanguage.tamil),
            ("Sara Nizam", "sara@swift.demo", UserRole.customer, InterfaceLanguage.english),
            ("Anika Perera", "agent@swift.demo", UserRole.agent, InterfaceLanguage.english),
            ("Dilan Jay", "dilan@swift.demo", UserRole.agent, InterfaceLanguage.sinhala),
            ("Meera Ravi", "meera@swift.demo", UserRole.agent, InterfaceLanguage.tamil),
            ("Swift Admin", "admin@swift.demo", UserRole.administrator, InterfaceLanguage.english),
        )
        for name, email, role, language in user_specs:
            user = await db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(
                    id=stable_id("user", email),
                    full_name=name,
                    email=email,
                    role=role,
                    preferred_language=language,
                    password_hash=hash_password("password123"),
                )
                db.add(user)
                await db.flush()
            users[email] = user

        repository_dataset = Path(__file__).resolve().parents[3] / "datasets/english/train_labeled.csv"
        container_dataset = Path("datasets/english/train_labeled.csv")
        dataset = repository_dataset if repository_dataset.exists() else container_dataset
        category_codes = {row[3] for row in TICKET_SEEDS}
        if dataset.exists():
            with dataset.open(encoding="utf-8") as handle:
                category_codes.update(row["category"] for row in csv.DictReader(handle))
        categories: dict[str, Category] = {}
        for code in sorted(category_codes):
            category = await db.scalar(select(Category).where(Category.code == code))
            if not category:
                security_terms = ("cash_withdrawal", "card_stolen", "cash_withdrawal_not_received")
                queue = queues["Fraud & Security"] if any(term in code for term in security_terms) else queues["Payments"]
                category = Category(code=code, display_name=code.replace("_", " ").title(), default_queue_id=queue.id)
                db.add(category)
                await db.flush()
            categories[code] = category

        now = utcnow()
        statuses = tuple(TicketStatus)
        priorities = (Priority.critical, Priority.high, Priority.high, Priority.medium, Priority.medium, Priority.low)
        sentiments = (Sentiment.negative, Sentiment.negative, Sentiment.neutral, Sentiment.positive)
        customers = [users[email] for email in ("customer@swift.demo", "nimal@swift.demo", "arun@swift.demo", "sara@swift.demo")]
        agents = [users[email] for email in ("agent@swift.demo", "dilan@swift.demo", "meera@swift.demo")]

        for index, (subject, message, language, category_code) in enumerate(TICKET_SEEDS):
            public_id = f"SW-2026-{1042 - index:06d}"
            if await db.scalar(select(Ticket.id).where(Ticket.public_id == public_id)):
                continue
            created_at = now - timedelta(hours=index * 7 + 2)
            updated_at = now - timedelta(hours=index + 1)
            status = statuses[index % len(statuses)]
            priority = priorities[index % len(priorities)]
            sentiment = sentiments[index % len(sentiments)]
            customer = customers[index % len(customers)]
            assigned_agent = None if index % 4 == 0 else agents[index % len(agents)]
            queue = queues["Fraud & Security"] if priority == Priority.critical else queues["Payments"] if index % 2 else queues["General Support"]
            response_language = InterfaceLanguage.tamil if language in {LanguageForm.tamil, LanguageForm.tanglish} else InterfaceLanguage.sinhala if language == LanguageForm.sinhala else InterfaceLanguage.english
            category_confidence = (0.94, 0.87, 0.72, 0.54, 0.83)[index % 5]
            ticket = Ticket(
                id=stable_id("ticket", public_id), public_id=public_id,
                customer_id=customer.id, assigned_agent_id=assigned_agent.id if assigned_agent else None,
                queue_id=queue.id, category_id=categories[category_code].id,
                subject=subject, original_text=message, masked_model_text=message,
                language=language, response_language=response_language,
                priority=priority, sentiment=sentiment, status=status,
                manual_review_required=category_confidence < 0.60,
                escalation_reason="Security-related category requires specialist review." if status == TicketStatus.escalated else None,
                created_at=created_at, updated_at=updated_at,
            )
            db.add(ticket)
            await db.flush()
            prediction_specs = (
                (PredictionTask.language, language.value, 0.96, "language-preview-0.2"),
                (PredictionTask.category, category_code, category_confidence, "classifier-preview-0.4"),
                (PredictionTask.priority, priority.value, 0.68 + ((index * 3) % 29) / 100, "priority-preview-0.3"),
                (PredictionTask.sentiment, sentiment.value, 0.61 + ((index * 7) % 37) / 100, "sentiment-preview-0.5"),
            )
            for task, value, confidence, model in prediction_specs:
                db.add(Prediction(id=stable_id("prediction", f"{public_id}:{task.value}"), ticket_id=ticket.id, task=task, value=value, confidence=confidence, model_version=model, predicted_at=created_at + timedelta(minutes=2)))
            db.add(ProcessingJob(id=stable_id("job", public_id), ticket_id=ticket.id, job_type="ticket_analysis", status=JobStatus.succeeded, created_at=created_at, completed_at=created_at + timedelta(minutes=2)))
            db.add(TicketEvent(id=stable_id("event", f"{public_id}:created"), ticket_id=ticket.id, actor_id=customer.id, event_type="ticket_created", detail="Ticket received securely", customer_visible=True, created_at=created_at))
            db.add(TicketEvent(id=stable_id("event", f"{public_id}:processed"), ticket_id=ticket.id, event_type="processing_completed", detail="Advisory predictions prepared", customer_visible=True, created_at=created_at + timedelta(minutes=2)))
            if status != TicketStatus.new:
                db.add(TicketEvent(id=stable_id("event", f"{public_id}:status"), ticket_id=ticket.id, actor_id=assigned_agent.id if assigned_agent else None, event_type="escalated" if status == TicketStatus.escalated else "agent_assigned", detail="Forwarded for specialist review" if status == TicketStatus.escalated else "Support team is reviewing", customer_visible=True, created_at=updated_at))
            if index % 3 == 0:
                db.add(TicketNote(id=stable_id("note", public_id), ticket_id=ticket.id, author_id=agents[0].id, text="Checked supplied evidence; reference is legible.", created_at=updated_at))
                attachment_id = stable_id("attachment", public_id)
                directory = settings.storage_root / str(ticket.id)
                directory.mkdir(parents=True, exist_ok=True)
                path = directory / f"{attachment_id}.png"
                if not path.exists():
                    path.write_bytes(PNG_BYTES)
                db.add(Attachment(id=attachment_id, ticket_id=ticket.id, uploaded_by=customer.id, filename=f"evidence-{index + 1}.png", storage_path=str(path), mime_type="image/png", size=len(PNG_BYTES), file_hash=hashlib.sha256(PNG_BYTES).hexdigest(), validation_status="valid", created_at=created_at))
            resolved = status in {TicketStatus.resolved, TicketStatus.closed}
            response_status = ResponseStatus.sent if resolved else ResponseStatus.generated_draft
            approved_at = updated_at if resolved else None
            db.add(Response(id=stable_id("response", public_id), ticket_id=ticket.id, text=("We reviewed the details you shared and completed the support review. Please reply through this ticket if you need further assistance." if resolved else f"Hello, thank you for contacting Swift Support about {subject}. A support specialist will verify the relevant records and update you through this ticket."), language=response_language, status=response_status, author_id=agents[0].id if resolved else None, approved_by=agents[2].id if resolved else None, approved_at=approved_at, sent_at=approved_at, created_at=created_at + timedelta(minutes=8), updated_at=updated_at))
            db.add(AuditLog(id=stable_id("audit", public_id), user_id=assigned_agent.id if assigned_agent else None, action="seeded_ticket_review", entity_type="ticket", entity_id=public_id, detail=f"Demo workflow record: {status.value}", created_at=updated_at))

        setting_specs = {
            "customer_registration_enabled": ("true", "boolean", "Allow customers to create accounts"),
            "agent_registration_enabled": ("true", "boolean", "Allow invite-code support-agent registration"),
            "low_confidence_threshold": ("0.60", "number", "Predictions below this confidence require review"),
            "max_upload_mb": ("10", "integer", "Maximum attachment size in megabytes"),
            "maintenance_message": ("", "string", "Optional customer-facing maintenance message"),
        }
        for key, (value, value_type, description) in setting_specs.items():
            if not await db.get(SystemSetting, key):
                db.add(SystemSetting(key=key, value=value, value_type=value_type, description=description, updated_by=users["admin@swift.demo"].id))
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
