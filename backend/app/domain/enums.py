from enum import StrEnum


class UserRole(StrEnum):
    customer = "customer"
    agent = "agent"
    supervisor = "supervisor"
    administrator = "administrator"


class InterfaceLanguage(StrEnum):
    english = "english"
    sinhala = "sinhala"
    tamil = "tamil"


class LanguageForm(StrEnum):
    english = "english"
    sinhala = "sinhala"
    tamil = "tamil"
    singlish = "singlish"
    tanglish = "tanglish"
    code_mixed = "code_mixed"
    unknown = "unknown"


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Sentiment(StrEnum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class TicketStatus(StrEnum):
    new = "new"
    processing = "processing"
    in_review = "in_review"
    assigned = "assigned"
    escalated = "escalated"
    response_draft = "response_draft"
    responded = "responded"
    resolved = "resolved"
    closed = "closed"
    reopened = "reopened"


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class PredictionTask(StrEnum):
    category = "category"
    priority = "priority"
    sentiment = "sentiment"
    language = "language"


class ResponseStatus(StrEnum):
    generated_draft = "generated_draft"
    agent_edited = "agent_edited"
    approved = "approved"
    rejected = "rejected"
    sent = "sent"
