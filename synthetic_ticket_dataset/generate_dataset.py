#!/usr/bin/env python3
"""Generate a deterministic synthetic mobile-banking support screenshot dataset."""

from __future__ import annotations

import argparse
import json
import random
import string
import sys
import warnings
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

SEED = 20260724
COUNT = 500
SIZE = (720, 1280)
LANGUAGES = ["English", "Sinhala", "Tamil", "Singlish", "Tanglish", "Mixed-language"]
REQUIRED_FIELDS = {
    "image_path", "category", "priority", "sentiment", "language",
    "visible_text", "error_code", "expected_image_summary",
    "issue_clues", "priority_clues",
}

SCENARIOS: dict[str, dict[str, Any]] = {
    "Cash withdrawal failure": {"status": "Failed", "priority": "medium", "clues": ["ATM withdrawal", "transaction failed"]},
    "Card payment declined": {"status": "Declined", "priority": "medium", "clues": ["card payment", "payment declined"]},
    "Transfer failed": {"status": "Failed", "priority": "medium", "clues": ["bank transfer", "transfer failed"]},
    "Transfer pending": {"status": "Pending", "priority": "medium", "clues": ["bank transfer", "still pending"]},
    "Wrong exchange rate": {"status": "Review", "priority": "low", "clues": ["currency conversion", "exchange rate"]},
    "Cash withdrawal charged incorrectly": {"status": "Review", "priority": "low", "clues": ["ATM fee", "incorrect charge"]},
    "Card stolen": {"status": "Urgent", "priority": "critical", "clues": ["stolen card", "freeze card"]},
    "Cash not received": {"status": "Failed", "priority": "high", "clues": ["cash missing", "ATM debited"]},
    "Duplicate transaction": {"status": "Review", "priority": "high", "clues": ["charged twice", "duplicate entry"]},
    "Beneficiary not added": {"status": "Failed", "priority": "low", "clues": ["new beneficiary", "could not add"]},
    "Balance not updated": {"status": "Pending", "priority": "low", "clues": ["available balance", "not refreshed"]},
    "Account blocked": {"status": "Blocked", "priority": "critical", "clues": ["account access", "security block"]},
    "OTP not received": {"status": "Waiting", "priority": "low", "clues": ["verification code", "SMS missing"]},
    "Refund pending": {"status": "Pending", "priority": "medium", "clues": ["merchant refund", "not credited"]},
    "Unauthorized transaction": {"status": "Urgent", "priority": "critical", "clues": ["not recognized", "secure account"]},
}

EN_MESSAGES = {
    "Cash withdrawal failure": "We could not complete this cash withdrawal.",
    "Card payment declined": "Your card payment was declined.",
    "Transfer failed": "The transfer could not be completed.",
    "Transfer pending": "Your transfer is still being processed.",
    "Wrong exchange rate": "The exchange rate needs your review.",
    "Cash withdrawal charged incorrectly": "The cash withdrawal charge may be incorrect.",
    "Card stolen": "Freeze your stolen card immediately.",
    "Cash not received": "Your account was debited but cash was not received.",
    "Duplicate transaction": "This transaction appears more than once.",
    "Beneficiary not added": "The new beneficiary could not be added.",
    "Balance not updated": "Your available balance has not updated yet.",
    "Account blocked": "Your account is blocked for security.",
    "OTP not received": "The verification code has not arrived.",
    "Refund pending": "Your refund is still pending.",
    "Unauthorized transaction": "You reported a transaction you do not recognize.",
}

SINHALA_MESSAGES = {
    "Cash withdrawal failure": "මුදල් ආපසු ගැනීම සම්පූර්ණ කළ නොහැකි විය.",
    "Card payment declined": "ඔබගේ කාඩ් ගෙවීම ප්‍රතික්ෂේප විය.",
    "Transfer failed": "මුදල් මාරුව සම්පූර්ණ කළ නොහැකි විය.",
    "Transfer pending": "ඔබගේ මුදල් මාරුව තවම සැකසෙමින් පවතී.",
    "Wrong exchange rate": "විනිමය අනුපාතය පරීක්ෂා කරන්න.",
    "Cash withdrawal charged incorrectly": "මුදල් ගැනීමේ ගාස්තුව වැරදි විය හැක.",
    "Card stolen": "සොරකම් කළ කාඩ්පත වහාම අත්හිටුවන්න.",
    "Cash not received": "ගිණුමෙන් අඩු වූ නමුත් මුදල් ලැබුණේ නැත.",
    "Duplicate transaction": "මෙම ගනුදෙනුව දෙවරක් පෙන්වයි.",
    "Beneficiary not added": "නව ප්‍රතිලාභියා එක් කළ නොහැකි විය.",
    "Balance not updated": "ඔබගේ ශේෂය තවම යාවත්කාලීන වී නැත.",
    "Account blocked": "ආරක්ෂාව සඳහා ඔබගේ ගිණුම අවහිර කර ඇත.",
    "OTP not received": "තහවුරු කිරීමේ කේතය ලැබුණේ නැත.",
    "Refund pending": "ඔබගේ මුදල් ආපසු ගෙවීම තවම පවතී.",
    "Unauthorized transaction": "ඔබ නොහඳුනන ගනුදෙනුවක් වාර්තා කර ඇත.",
}

TAMIL_MESSAGES = {
    "Cash withdrawal failure": "பணம் எடுப்பதை நிறைவு செய்ய முடியவில்லை.",
    "Card payment declined": "உங்கள் அட்டை கட்டணம் மறுக்கப்பட்டது.",
    "Transfer failed": "பணப் பரிமாற்றத்தை நிறைவு செய்ய முடியவில்லை.",
    "Transfer pending": "உங்கள் பணப் பரிமாற்றம் இன்னும் செயலாக்கப்படுகிறது.",
    "Wrong exchange rate": "மாற்று விகிதத்தைச் சரிபார்க்கவும்.",
    "Cash withdrawal charged incorrectly": "பணம் எடுத்த கட்டணம் தவறாக இருக்கலாம்.",
    "Card stolen": "திருடப்பட்ட அட்டையை உடனே முடக்கவும்.",
    "Cash not received": "கணக்கில் கழிந்தது, ஆனால் பணம் கிடைக்கவில்லை.",
    "Duplicate transaction": "இந்தப் பரிவர்த்தனை இருமுறை காணப்படுகிறது.",
    "Beneficiary not added": "புதிய பயனாளியைச் சேர்க்க முடியவில்லை.",
    "Balance not updated": "உங்கள் இருப்பு இன்னும் புதுப்பிக்கப்படவில்லை.",
    "Account blocked": "பாதுகாப்பிற்காக உங்கள் கணக்கு முடக்கப்பட்டுள்ளது.",
    "OTP not received": "சரிபார்ப்புக் குறியீடு வரவில்லை.",
    "Refund pending": "உங்கள் பணத்திருப்பம் இன்னும் நிலுவையில் உள்ளது.",
    "Unauthorized transaction": "நீங்கள் அறியாத பரிவர்த்தனை பதிவாகியுள்ளது.",
}

ROMANIZED = {
    "Singlish": {
        "Cash withdrawal failure": "Salli ganna transaction eka fail una.",
        "Card payment declined": "Card payment eka decline wela.",
        "Transfer failed": "Salli transfer eka complete une naha.",
        "Transfer pending": "Transfer eka thawama process wenawa.",
        "Wrong exchange rate": "Exchange rate eka hari naha wage.",
        "Cash withdrawal charged incorrectly": "ATM charge eka waradi wage.",
        "Card stolen": "Card eka horakam kala; danma freeze karanna.",
        "Cash not received": "Account eken adu una, cash labune naha.",
        "Duplicate transaction": "Transaction eka deparak penenawa.",
        "Beneficiary not added": "Beneficiary add karanna bari una.",
        "Balance not updated": "Balance eka thawama update wela naha.",
        "Account blocked": "Security nisa account eka block wela.",
        "OTP not received": "OTP eka thawama awe naha.",
        "Refund pending": "Refund eka thawama pending.",
        "Unauthorized transaction": "Mama nodanna transaction ekak thiyenawa.",
    },
    "Tanglish": {
        "Cash withdrawal failure": "Panam edukka mudiyala; transaction fail aachu.",
        "Card payment declined": "Card payment decline aayiduchu.",
        "Transfer failed": "Money transfer complete aagala.",
        "Transfer pending": "Transfer innum process aaguthu.",
        "Wrong exchange rate": "Exchange rate sari illa pola.",
        "Cash withdrawal charged incorrectly": "ATM charge thappa irukku.",
        "Card stolen": "Card thirudu pochu; udane freeze pannunga.",
        "Cash not received": "Account-la debit aachu, cash kidaikala.",
        "Duplicate transaction": "Transaction rendu murai kaatuthu.",
        "Beneficiary not added": "Beneficiary add panna mudiyala.",
        "Balance not updated": "Balance innum update aagala.",
        "Account blocked": "Security-kaaga account block aayiduchu.",
        "OTP not received": "OTP innum varala.",
        "Refund pending": "Refund innum pending-la irukku.",
        "Unauthorized transaction": "Enakku theriyatha transaction irukku.",
    },
}

FONT_CANDIDATES = {
    "latin": [
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/opentype/cantarell/Cantarell-VF.otf",
    ],
    "sinhala": [
        "/usr/share/fonts/truetype/noto/NotoSansSinhala-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifSinhala-Regular.ttf",
        "/usr/share/fonts/truetype/sinhala/AbhayaLibre-Regular.ttf",
    ],
    "tamil": [
        "/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifTamil-Regular.ttf",
        "/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf",
    ],
}


def find_fonts() -> dict[str, str | None]:
    """Find Unicode fonts in common system locations and warn on fallback."""
    found: dict[str, str | None] = {}
    for script, candidates in FONT_CANDIDATES.items():
        found[script] = next((p for p in candidates if Path(p).is_file()), None)
        if found[script] is None:
            warnings.warn(
                f"No {script} Unicode font found. Pillow's default font will be used; "
                "some characters may appear as boxes.", RuntimeWarning,
            )
    return found


def font(fonts: dict[str, str | None], language: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    script = "sinhala" if language in {"Sinhala"} else "tamil" if language in {"Tamil"} else "latin"
    path = fonts.get(script) or fonts.get("latin")
    try:
        return ImageFont.truetype(path, size) if path else ImageFont.load_default(size=size)
    except (OSError, ValueError):
        return ImageFont.load_default(size=size)


def localized_message(category: str, language: str, index: int) -> str:
    """Return a scenario-specific message in the requested language style."""
    if language == "English":
        return EN_MESSAGES[category]
    if language == "Sinhala":
        return SINHALA_MESSAGES[category]
    if language == "Tamil":
        return TAMIL_MESSAGES[category]
    if language in ROMANIZED:
        return ROMANIZED[language][category]
    # A readable Latin-script blend of colloquial Sinhala, Tamil, and English.
    return f"{ROMANIZED['Singlish'][category]} {ROMANIZED['Tanglish'][category]}"


def display_language(language: str, index: int) -> str:
    if language == "Mixed-language":
        return "English"
    return language


def wrap_text(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.ImageFont, width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=text_font)[2] <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def add_noise(image: Image.Image, rng: random.Random) -> Image.Image:
    """Add subtle, deterministic sensor/compression-like noise."""
    px = image.load()
    for _ in range(9000):
        x, y = rng.randrange(image.width), rng.randrange(image.height)
        r, g, b = px[x, y]
        d = rng.choice((-3, -2, -1, 1, 2, 3))
        px[x, y] = tuple(max(0, min(255, c + d)) for c in (r, g, b))
    return image


def draw_icon(draw: ImageDraw.ImageDraw, center: tuple[int, int], status: str, color: str) -> None:
    x, y = center
    draw.ellipse((x - 48, y - 48, x + 48, y + 48), fill=color)
    if status in {"Pending", "Waiting", "Review"}:
        draw.line((x, y, x, y - 23), fill="white", width=8)
        draw.line((x, y, x + 19, y + 13), fill="white", width=8)
    elif status in {"Urgent", "Blocked"}:
        draw.line((x, y - 25, x, y + 10), fill="white", width=9)
        draw.ellipse((x - 5, y + 22, x + 5, y + 32), fill="white")
    else:
        draw.line((x - 22, y - 20, x + 22, y + 22), fill="white", width=9)
        draw.line((x + 22, y - 20, x - 22, y + 22), fill="white", width=9)


def make_details(rng: random.Random, category: str) -> dict[str, str]:
    currency = rng.choice(["LKR", "USD", "EUR", "GBP", "SGD"])
    amount = f"{currency} {rng.uniform(5, 2500):,.2f}"
    moment = datetime(2024, 1, 1, 8, 0) + timedelta(minutes=rng.randrange(1_300_000))
    prefix = "".join(rng.choices(string.ascii_uppercase, k=3))
    return {
        "amount": amount,
        "date": moment.strftime("%d %b %Y"),
        "time": moment.strftime("%H:%M"),
        "reference": f"NMB-{moment:%y%m}-{rng.randrange(100000, 999999)}",
        "error_code": f"{prefix}-{rng.randrange(100, 999)}",
        "category": category,
    }


def render_screen(
    rng: random.Random, category: str, language: str, index: int,
    details: dict[str, str], fonts: dict[str, str | None],
) -> tuple[Image.Image, list[str]]:
    """Render one of three randomized mobile banking templates."""
    info = SCENARIOS[category]
    status, priority = info["status"], info["priority"]
    theme = rng.choice([
        ((244, 248, 252), (23, 54, 93)), ((249, 247, 242), (31, 74, 70)),
        ((244, 243, 250), (59, 43, 92)), ((239, 247, 247), (18, 83, 94)),
    ])
    image = Image.new("RGB", SIZE, theme[0])
    draw = ImageDraw.Draw(image)
    accent = theme[1]
    status_color = "#C0392B" if status in {"Failed", "Declined", "Urgent", "Blocked"} else "#D17B0F"
    lang_for_font = display_language(language, index)
    small = font(fonts, lang_for_font, rng.randint(24, 28))
    body = font(fonts, lang_for_font, rng.randint(27, 32))
    title = font(fonts, "English", rng.randint(38, 45))
    amount_font = font(fonts, "English", rng.randint(46, 55))
    header_font = font(fonts, "English", 31)
    message = localized_message(category, language, index)
    layout = rng.randrange(3)
    jitter_x, jitter_y = rng.randint(-10, 10), rng.randint(-8, 8)

    draw.rectangle((0, 0, 720, 72), fill=(15, 25, 38))
    draw.text((34, 20), moment_text := f"{rng.randrange(8, 23):02d}:{rng.choice([0, 5, 10, 15, 30, 45]):02d}", font=font(fonts, "English", 23), fill="white")
    draw.text((578, 20), "●  4G  ▰", font=font(fonts, "English", 20), fill="white")
    header_h = 132 if layout != 2 else 158
    draw.rectangle((0, 72, 720, header_h + 72), fill=accent)
    draw.ellipse((30, 104, 83, 157), fill=(255, 255, 255))
    draw.text((47, 112), "N", font=font(fonts, "English", 27), fill=accent)
    draw.text((103, 109), "Nova Mobile Banking", font=header_font, fill="white")
    draw.text((104, 151), "Secure transaction centre", font=font(fonts, "English", 20), fill=(220, 232, 241))

    card_left, card_right = 38 + jitter_x, 682 + jitter_x
    card_top = 238 + jitter_y
    draw.rounded_rectangle((card_left, card_top, card_right, 1124 + jitter_y), radius=28, fill="white", outline=(220, 226, 232), width=2)
    icon_y = card_top + (110 if layout == 0 else 86)
    draw_icon(draw, (360 + jitter_x, icon_y), status, status_color)
    status_y = icon_y + 75
    status_text = status.upper()
    box = draw.textbbox((0, 0), status_text, font=title)
    draw.text(((720 - (box[2] - box[0])) / 2 + jitter_x, status_y), status_text, font=title, fill=status_color)
    amount_y = status_y + 73
    box = draw.textbbox((0, 0), details["amount"], font=amount_font)
    draw.text(((720 - (box[2] - box[0])) / 2 + jitter_x, amount_y), details["amount"], font=amount_font, fill=(22, 35, 50))

    msg_y = amount_y + 86
    for line in wrap_text(draw, message, body, 530):
        box = draw.textbbox((0, 0), line, font=body)
        draw.text(((720 - (box[2] - box[0])) / 2 + jitter_x, msg_y), line, font=body, fill=(65, 74, 85))
        msg_y += int(body.size * 1.45) if hasattr(body, "size") else 42

    details_y = max(msg_y + 35, card_top + 480)
    if layout == 1:
        draw.rounded_rectangle((75 + jitter_x, details_y - 25, 645 + jitter_x, details_y + 310), 18, fill=(247, 249, 251))
    rows = [
        ("Date & time", f"{details['date']}  •  {details['time']}"),
        ("Reference", details["reference"]),
        ("Error code", details["error_code"]),
        ("Issue", category),
    ]
    for row_i, (label, value) in enumerate(rows):
        y = details_y + row_i * 74
        draw.text((82 + jitter_x, y), label, font=font(fonts, "English", 21), fill=(118, 127, 138))
        value_font = font(fonts, "English", min(getattr(small, "size", 25), 25)) if label == "Issue" else font(fonts, "English", 24)
        clipped = value if len(value) < 31 else value[:30] + "…"
        draw.text((270 + jitter_x, y), clipped, font=value_font, fill=(29, 42, 58))
        if layout != 1 and row_i < 3:
            draw.line((80 + jitter_x, y + 48, 640 + jitter_x, y + 48), fill=(230, 234, 238), width=1)

    primary = "Freeze card" if category == "Card stolen" else "Secure account" if category == "Unauthorized transaction" else "Get help"
    button_y = 1006 + jitter_y
    draw.rounded_rectangle((82 + jitter_x, button_y, 638 + jitter_x, button_y + 70), 18, fill=accent)
    bf = font(fonts, "English", 26)
    box = draw.textbbox((0, 0), primary, font=bf)
    draw.text(((720 - (box[2] - box[0])) / 2 + jitter_x, button_y + 18), primary, font=bf, fill="white")
    draw.text((269 + jitter_x, button_y + 91), "Back to activity", font=font(fonts, "English", 21), fill=accent)
    draw.rectangle((0, 1218, 720, 1280), fill=(250, 251, 252))
    draw.ellipse((347, 1240, 373, 1266), fill=accent)

    visible = [
        moment_text, "4G", "Nova Mobile Banking", "Secure transaction centre", status_text,
        details["amount"], message, "Date & time", f"{details['date']} • {details['time']}",
        "Reference", details["reference"], "Error code", details["error_code"], "Issue",
        category, primary, "Back to activity",
    ]
    return add_noise(image, rng), visible


def create_label(
    image_path: str, category: str, language: str, details: dict[str, str],
    visible: list[str],
) -> dict[str, Any]:
    info = SCENARIOS[category]
    priority = info["priority"]
    sentiment = "negative" if priority in {"critical", "high"} or info["status"] in {"Failed", "Declined", "Blocked"} else "neutral"
    return {
        "image_path": image_path,
        "category": category,
        "priority": priority,
        "sentiment": sentiment,
        "language": language,
        "visible_text": "\n".join(visible),
        "error_code": details["error_code"],
        "expected_image_summary": (
            f"A fictional Nova Mobile Banking screen showing {category.lower()}, "
            f"status {info['status'].lower()}, amount {details['amount']}, and reference {details['reference']}."
        ),
        "issue_clues": info["clues"] + [info["status"].lower(), details["error_code"]],
        "priority_clues": {
            "critical": ["immediate security risk", "urgent action required"],
            "high": ["money missing or charged twice", "prompt investigation needed"],
            "medium": ["transaction disrupted", "support follow-up needed"],
            "low": ["informational or non-urgent", "standard review"],
        }[priority],
    }


def create_preview(labels: list[dict[str, Any]], root: Path) -> None:
    thumb_size, cols, rows = (216, 384), 5, 4
    grid = Image.new("RGB", (cols * 216, rows * 420), (226, 231, 237))
    draw = ImageDraw.Draw(grid)
    label_font = ImageFont.load_default(size=15)
    # Evenly spaced examples ensure broad visual/category coverage.
    chosen = [labels[i * len(labels) // 20] for i in range(20)]
    for i, item in enumerate(chosen):
        with Image.open(root / item["image_path"]) as source:
            thumb = source.convert("RGB").resize(thumb_size, Image.Resampling.LANCZOS)
        x, y = (i % cols) * 216, (i // cols) * 420
        grid.paste(thumb, (x, y))
        caption = f"{i * len(labels) // 20 + 1:03d} · {item['language']}"
        draw.rectangle((x, y + 384, x + 216, y + 420), fill=(250, 251, 252))
        draw.text((x + 8, y + 394), caption, font=label_font, fill=(25, 37, 52))
    grid.save(root / "preview_grid.png", optimize=True)


def validate_dataset(root: Path, expected_count: int = COUNT) -> dict[str, Any]:
    """Validate image integrity, labels, required fields, and full coverage."""
    labels_path = root / "labels.json"
    if not labels_path.is_file() or labels_path.stat().st_size == 0:
        raise ValueError("labels.json is missing or empty")
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    pngs = sorted((root / "screenshots").glob("*.png"))
    errors: list[str] = []
    if len(pngs) != expected_count:
        errors.append(f"expected {expected_count} images, found {len(pngs)}")
    if len(labels) != expected_count:
        errors.append(f"expected {expected_count} labels, found {len(labels)}")
    paths = [item.get("image_path") for item in labels]
    if len(paths) != len(set(paths)):
        errors.append("duplicate image_path entries found")
    for i, item in enumerate(labels):
        missing = REQUIRED_FIELDS - item.keys()
        if missing:
            errors.append(f"label {i} missing fields: {sorted(missing)}")
            continue
        path = root / item["image_path"]
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty image: {item['image_path']}")
            continue
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                if image.size != SIZE or image.format != "PNG":
                    errors.append(f"invalid format/size: {item['image_path']}")
        except Exception as exc:
            errors.append(f"cannot open {item['image_path']}: {exc}")
    categories = Counter(item.get("category") for item in labels)
    languages = Counter(item.get("language") for item in labels)
    if set(categories) != set(SCENARIOS):
        errors.append(f"category coverage mismatch: {set(SCENARIOS) - set(categories)}")
    if set(languages) != set(LANGUAGES):
        errors.append(f"language coverage mismatch: {set(LANGUAGES) - set(languages)}")
    for extra in ("preview_grid.png", "generate_dataset.py", "requirements.txt", "README.md"):
        path = root / extra
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"required file missing or empty: {extra}")
    result = {
        "valid": not errors,
        "expected_images": expected_count,
        "images_found": len(pngs),
        "labels_found": len(labels),
        "categories_represented": len(categories),
        "languages_represented": len(languages),
        "category_distribution": dict(sorted(categories.items())),
        "language_distribution": dict(sorted(languages.items())),
        "errors": errors,
    }
    if errors:
        raise ValueError("Dataset validation failed:\n- " + "\n- ".join(errors))
    return result


def generate_dataset(root: Path, count: int = COUNT, seed: int = SEED) -> dict[str, Any]:
    rng = random.Random(seed)
    screenshots = root / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    for stale in screenshots.glob("synthetic_bank_*.png"):
        stale.unlink()
    fonts = find_fonts()
    categories = list(SCENARIOS)
    plan = [(categories[i % len(categories)], LANGUAGES[i % len(LANGUAGES)]) for i in range(count)]
    rng.shuffle(plan)
    labels = []
    for i, (category, language) in enumerate(plan, 1):
        details = make_details(rng, category)
        image, visible = render_screen(rng, category, language, i, details, fonts)
        relative = f"screenshots/synthetic_bank_{i:04d}.png"
        image.save(root / relative, format="PNG", optimize=True)
        labels.append(create_label(relative, category, language, details, visible))
        if i % 50 == 0 or i == count:
            print(f"Generated {i}/{count} screenshots")
    (root / "labels.json").write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    create_preview(labels, root)
    return validate_dataset(root, count)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=COUNT, help=f"number of screenshots (default: {COUNT})")
    parser.add_argument("--seed", type=int, default=SEED, help=f"fixed random seed (default: {SEED})")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent, help="dataset output directory")
    parser.add_argument("--validate-only", action="store_true", help="validate existing output without regenerating")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    try:
        report = validate_dataset(args.output, args.count) if args.validate_only else generate_dataset(args.output, args.count, args.seed)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("\nValidation: PASS")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
