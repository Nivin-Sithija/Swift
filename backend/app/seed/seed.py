import asyncio
import csv
from pathlib import Path

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.domain.enums import UserRole
from app.models.entities import Category, SupportQueue, User


async def seed() -> None:
    async with SessionLocal() as db:
        queues = {}
        for name in ("General Support", "Payments", "Fraud & Security"):
            queue = await db.scalar(select(SupportQueue).where(SupportQueue.name == name))
            if not queue:
                queue = SupportQueue(name=name, description=f"{name} ticket queue")
                db.add(queue)
                await db.flush()
            queues[name] = queue
        for name, email, role in (
            ("Maya Silva", "customer@swift.demo", UserRole.customer),
            ("Anika Perera", "agent@swift.demo", UserRole.agent),
            ("Meera Ravi", "supervisor@swift.demo", UserRole.supervisor),
            ("Swift Admin", "admin@swift.demo", UserRole.administrator),
        ):
            if not await db.scalar(select(User).where(User.email == email)):
                db.add(
                    User(
                        full_name=name,
                        email=email,
                        role=role,
                        password_hash=hash_password("password123"),
                    )
                )
        repository_dataset = (
            Path(__file__).resolve().parents[3] / "datasets" / "english" / "train_labeled.csv"
        )
        container_dataset = Path("datasets/english/train_labeled.csv")
        dataset = repository_dataset if repository_dataset.exists() else container_dataset
        if dataset.exists():
            with dataset.open(encoding="utf-8") as handle:
                categories = sorted({row["category"] for row in csv.DictReader(handle)})
            for code in categories:
                if not await db.scalar(select(Category).where(Category.code == code)):
                    queue = (
                        queues["Fraud & Security"]
                        if any(x in code for x in ("cash_withdrawal", "card_stolen"))
                        else queues["Payments"]
                    )
                    db.add(
                        Category(
                            code=code,
                            display_name=code.replace("_", " ").title(),
                            default_queue_id=queue.id,
                        )
                    )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
