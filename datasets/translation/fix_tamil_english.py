#!/usr/bin/env python3
"""
Remove English (Latin-script) words from the native-Tamil `text` column of
`tamil/train_labeled.csv` (or `tamil/test_labeled.csv` via --file), so the
Tamil side is a pure Tamil translation.

Unlike the Tanglish dataset (see TAMIL_STYLE.md), which keeps English banking
terms on purpose, `tamil/` is native-script Tamil and should carry none.

Two passes, applied only to rows that contain a Latin letter:
  1. GLOSSES - drop a redundant English gloss after a Tamil word:
               "பின் (PIN)" -> "பின்", "நிலுவையில் (pending)" -> "நிலுவையில்".
  2. PHRASES - ordered exact-substring replacements, most specific first, so
               an English word and the Tamil suffix glued to it are rewritten
               together: "USD ஐ" -> "அமெரிக்க டொலரை", "card-ஐ" -> "அட்டையை".
               Native Tamil where one exists (reusing the dataset's own terms:
               கொடுப்பனவு, நிலுவையில், மீள்நிரப்பு, பணப் பெறுகை ...); brand,
               scheme and acronym names with no Tamil word are written in
               Tamil script (ஆப்பிள் பே, ஸ்விஃப்ட், ஏடிஎம்).

Default is a dry run: it lists every English word found, how many rows each
pass fixes, and any row still containing Latin letters. --apply rewrites the
CSV in place (other columns and untouched rows are byte-identical);
--report PATH writes id,text_en,old,new for every changed row for review.
Re-running after --apply is a no-op.

Usage:
    python fix_tamil_english.py                       # dry run on train
    python fix_tamil_english.py --report changes.csv  # dry run + review file
    python fix_tamil_english.py --apply
    python fix_tamil_english.py --file ../tamil/test_labeled.csv
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
DEFAULT_FILE = os.path.join(DATASETS, "tamil", "train_labeled.csv")

LATIN = re.compile(r"[A-Za-z]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9'&.\-]*")
# "(...)" holding Latin text and no Tamil letters (Tamil block U+0B80-U+0BFF)
GLOSS = re.compile(r"\s*\(([^()஀-௿]*[A-Za-z][^()஀-௿]*)\)")

# Ordered: earlier entries win, so specific phrases come before the bare word.
PHRASES = [
    # --- placeholder names (X / Y) -> generic Tamil wording
    ("நான் X இலிருந்து வருகிறேன் ஆனால் Y இற்குப் பயணம் செய்கிறேன் - Y இற்கான",
     "நான் ஒரு நாட்டிலிருந்து வருகிறேன் ஆனால் வேறொரு நாட்டிற்குப் பயணம் செய்கிறேன் - அந்த நாட்டிற்கான"),
    ("நாணயம் X ஐ நாணயம் Y ஆக", "ஒரு நாணயத்தை வேறொரு நாணயமாக"),
    ("X என்பவரைப் பயனாளியாகச்", "குறிப்பிட்ட ஒருவரைப் பயனாளியாகச்"),
    ("பயனாளி X க்கான", "குறிப்பிட்ட ஒரு பயனாளிக்கான"),
    ("X ஐ ஒரு பயனாளி என சேர்க்க", "குறிப்பிட்ட ஒருவரைப் பயனாளியாகச் சேர்க்க"),

    # --- stray Latin letter inside a Tamil word
    ("செய்யuங்கோ", "செய்யுங்கோ"),

    # --- brands, card schemes, payment rails (no Tamil word -> Tamil script)
    ("American Express", "அமெரிக்கன் எக்ஸ்பிரஸ்"),
    ("Apple Watch", "ஆப்பிள் வாட்ச்"),
    ("Apple Pay", "ஆப்பிள் பே"),
    ("ApplePay", "ஆப்பிள் பே"),
    ("Apple", "ஆப்பிள்"),
    ("eBay", "ஈபே"),
    ("NFC", "என்எஃப்சி"),
    ("Durham இலிருந்து Walton-On-The-Naze இலுள்ள", "டர்ஹாமிலிருந்து வோல்டன்-ஆன்-தி-நேஸிலுள்ள"),
    ("Google Play", "கூகுள் ப்ளே"),
    ("Google Pay", "கூகுள் பே"),
    ("MasterCard", "மாஸ்டர்கார்ட்"),
    ("Mastercard", "மாஸ்டர்கார்ட்"),
    ("VISA", "விசா"),
    ("Visa", "விசா"),
    ("SWIFT", "ஸ்விஃப்ட்"),
    ("SEPA", "செபா"),
    ("Next நிறுவனத்திடம்", "நெக்ஸ்ட் நிறுவனத்திடம்"),
    ("3D", "3டி"),
    ("ATM", "ஏடிஎம்"),
    ("PIN-ஐ", "பின் இலக்கத்தை"),
    ("PIN", "பின்"),
    ("ID நிரூபிக்க", "அடையாளத்தை நிரூபிக்க"),

    # --- currencies
    ("USD இலிருந்து", "அமெரிக்க டொலரிலிருந்து"),
    ("LKR இலிருந்து", "இலங்கை ரூபாவிலிருந்து"),
    ("USD இற்குப் பதிலாக", "அமெரிக்க டொலருக்குப் பதிலாக"),
    ("LKR க்கு பதிலாக", "இலங்கை ரூபாவுக்குப் பதிலாக"),
    ("USD க்குப்", "அமெரிக்க டொலருக்குப்"),
    ("LKR க்குப்", "இலங்கை ரூபாவுக்குப்"),
    ("USD க்கு", "அமெரிக்க டொலருக்கு"),
    ("LKR க்கு", "இலங்கை ரூபாவுக்கு"),
    ("LKR இற்கான", "இலங்கை ரூபாவிற்கான"),
    ("LKR இற்கு", "இலங்கை ரூபாவிற்கு"),
    ("USD இற்கு", "அமெரிக்க டொலருக்கு"),
    ("USD ஐத்", "அமெரிக்க டொலரைத்"),
    ("LKR ஐப்", "இலங்கை ரூபாவைப்"),
    ("USD ஐ", "அமெரிக்க டொலரை"),
    ("LKR ஐ", "இலங்கை ரூபாவை"),
    ("USD ஆக", "அமெரிக்க டொலராக"),
    ("LKR ஆக", "இலங்கை ரூபாவாக"),
    ("LKR இல்", "இலங்கை ரூபாவில்"),
    ("USD", "அமெரிக்க டொலர்"),
    ("LKR", "இலங்கை ரூபா"),
    ("EUR ஆக", "யூரோவாக"),
    ("EUR", "யூரோ"),
    ("GBP", "பிரித்தானிய பவுண்ட்"),

    # --- countries / regions
    ("US ல", "அமெரிக்காவில"),
    ("US க்கான", "அமெரிக்காவுக்கான"),
    ("US க்கு", "அமெரிக்காவுக்கு"),
    ("US-இலிருந்து", "அமெரிக்காவிலிருந்து"),
    ("US transfer-க்கு", "அமெரிக்கப் பணப் பரிமாற்றத்திற்கு"),
    ("EU-வில்", "ஐரோப்பிய ஒன்றியத்தில்"),
    ("EU பண", "ஐரோப்பிய ஒன்றியப் பண"),
    ("EU", "ஐரோப்பிய ஒன்றியம்"),
    ("UK-ல", "பிரித்தானியாவில"),

    # --- top-up: normalise spellings, then -> மீள்நிரப்பு (the dataset's term)
    ('"theft-top" தெரிவு', "auto top-up தெரிவு"),  # typo for auto-top in the English source
    ("Auto Top இற்கான", "auto top-up இற்கான"),
    ("Auto top-up", "auto top-up"),
    ("automatic top-up", "auto top-up"),
    ("auto-top up", "auto top-up"),
    ("auto top up", "auto top-up"),
    ("auto Top-up", "auto top-up"),
    ("auto top இற்கு", "auto top-up இற்கு"),
    ("auto-top", "auto top-up"),
    ("top up", "top-up"),
    ("auto top-up-க்கான", "தானியங்கி மீள்நிரப்புக்கான"),
    ("auto top-up இற்கான", "தானியங்கி மீள்நிரப்புக்கான"),
    ("auto top-up இற்கு", "தானியங்கி மீள்நிரப்புக்கு"),
    ("auto top-up ஐ", "தானியங்கி மீள்நிரப்பை"),
    ("auto top-up தெரிவ", "தானியங்கி மீள்நிரப்புத் தெரிவ"),
    ("auto top-up செயற்பாட", "தானியங்கி மீள்நிரப்புச் செயற்பாட"),
    ("auto top-up கொள்கைகள்", "தானியங்கி மீள்நிரப்புக் கொள்கைகள்"),
    ("auto top-up", "தானியங்கி மீள்நிரப்பு"),
    ("top-up களை", "மீள்நிரப்புகளை"),
    ("top-up செய்யுமா", "மீள்நிரப்புமா"),
    ("top-up செய்யும்", "மீள்நிரப்பும்"),
    ("top-up செய்வது", "மீள்நிரப்புவது"),
    ("top-up செய்ய", "மீள்நிரப்ப"),
    ("top-up பண்றது", "மீள்நிரப்புவது"),
    ("top-up பண்ண", "மீள்நிரப்ப"),
    ("top-up-ஐ", "மீள்நிரப்பை"),
    ("top-up-க்கு charges", "மீள்நிரப்புக்குக் கட்டணங்கள்"),
    ("top-up-க்கு", "மீள்நிரப்புக்கு"),
    ("top-up", "மீள்நிரப்பு"),
    ("credit குறைவாக", "மீதிப் பணம் குறைவாக"),

    # --- pending -> நிலுவை
    ('"Pending payment"', '"நிலுவையிலுள்ள கொடுப்பனவு"'),
    ('"pending" (நிலுவையில்)', '"நிலுவையில்"'),
    ('"Pending"', '"நிலுவையில்"'),
    ("Pending transaction", "நிலுவையிலுள்ள பரிவர்த்தனை"),
    ("'pending' நிலை", "'நிலுவை' நிலை"),
    ('"pending" காலம்', '"நிலுவை" காலம்'),
    ("'pending'", "'நிலுவையில்'"),
    ('"pending"', '"நிலுவையில்"'),
    ("pending ஆகத்தான்", "நிலுவையில்தான்"),
    ("pending இலேயே", "நிலுவையிலேயே"),
    ("pending-ல", "நிலுவையில"),
    ("pending நிலை", "நிலுவை நிலை"),
    ("pending ஆக", "நிலுவையில்"),
    ("கொடுப்பனவுகள் pending என்", "கொடுப்பனவுகள் நிலுவையில் உள்ளன என்"),
    ("pending என்", "நிலுவையில் உள்ளது என்"),
    ("pending", "நிலுவையில்"),

    # --- declined / rejected / reverted / failed / cancelled
    ('"decline" (நிராகரிக்கப்பட்டது)', '"நிராகரிக்கப்பட்டது"'),
    ("'Decline'", "'நிராகரிக்கப்பட்டது'"),
    ("'declined'", "'நிராகரிக்கப்பட்டது'"),
    ("decline பண்றீங்க", "நிராகரிக்கிறீங்க"),
    ("decline ஆனது", "நிராகரிக்கப்பட்டது"),
    ("reject ஆனது", "நிராகரிக்கப்பட்டது"),
    ("reject பண்ணிடுச்சு", "நிராகரிச்சிடுச்சு"),
    ("revert ஆகக்", "திரும்பப் பெறப்படக்"),
    ("revert ஆனது", "திரும்பப் பெறப்பட்டது"),
    ("fail ஆகக்", "தோல்வியடையக்"),
    ("fail ஆனது", "தோல்வியடைந்தது"),
    ("complete ஆக", "நிறைவடைய"),
    ("cancel ஆனது", "ரத்தானது"),
    ("cancel ஆயிருச்சு", "ரத்தாயிருச்சு"),
    ("அட்டை payment go through ஆகல", "அட்டைக் கொடுப்பனவு நிறைவேறல"),
    ("approve ஆகல", "அனுமதி கிடைக்கல"),

    # --- account actions
    ("கணக்கை terminate பண்ண", "கணக்கை நிறுத்தி மூட"),
    ("கணக்கை cancel பண்றது", "கணக்கை ரத்து பண்றது"),
    ("கணக்கை deactivate பண்ண", "கணக்கைச் செயலிழக்கச் செய்ய"),
    ("கணக்கை delete பண்ண", "கணக்கை நீக்க"),
    ("இலக்கத்தை unblock செய்வது", "இலக்கத்தின் முடக்கத்தை நீக்குவது"),
    ("block ஆகிவிட்டது", "முடக்கப்பட்டுவிட்டது"),
    ("passcode-ஐ reset செய்வது", "கடவுக்குறியீட்டை மீளமைப்பது"),
    ("passcode-உம்", "கடவுக்குறியீடும்"),
    ("password", "கடவுச்சொல்"),
    ("direct debit-ஐ", "நேரடிப் பற்றுதலை"),
    ("direct debit", "நேரடிப் பற்றுதல்"),
    ("set பண்ணவில்லை", "அமைக்கவில்லை"),
    ("set பண்ணாத", "அமைக்காத"),

    # --- cards
    ("card-ஐ activate பண்ணணும்", "அட்டையைச் செயல்படுத்தணும்"),
    ("card-ஐ activate பண்ண", "அட்டையைச் செயல்படுத்த"),
    ("card-ஐ active பண்றது", "அட்டையைச் செயல்படுத்துவது"),
    ("அட்டையை active செய்வது", "அட்டையைச் செயல்படுத்துவது"),
    ("அட்டையை activate பண்றது", "அட்டையைச் செயல்படுத்துவது"),
    ("card expire ஆனப்புறம்", "அட்டை காலாவதியானப்புறம்"),
    ("card expire ஆகப்போகுது", "அட்டை காலாவதியாகப்போகுது"),
    ("disposable virtual card", "ஒருமுறை பயன்பாட்டு மெய்நிகர் அட்டை"),
    ("disposable cards-ஐ", "ஒருமுறை பயன்பாட்டு அட்டைகளைப்"),
    ("virtual card-ஐ", "மெய்நிகர் அட்டையை"),
    ("physical cards", "பௌதிக அட்டைகள்"),
    ("physical card", "பௌதிக அட்டை"),
    ("actual card-க்கு", "உண்மையான அட்டைக்கு"),
    ("card payment", "அட்டைக் கொடுப்பனவு"),
    ("create பண்றது", "உருவாக்குவது"),

    # --- identity / verification
    ("அடையாளத்தை verify செய்வதில்", "அடையாளத்தைச் சரிபார்ப்பதில்"),
    ("identity verification-க்கு", "அடையாளச் சரிபார்ப்புக்கு"),
    ("identity verification", "அடையாளச் சரிபார்ப்பு"),
    ("அடையாள verification", "அடையாளச் சரிபார்ப்பு"),
    ("identity verify பண்ண", "அடையாளத்தைச் சரிபார்க்க"),
    ("funds-இன் source-க்கு verification", "பணத்தின் மூலத்திற்குச் சரிபார்ப்பு"),
    ("funds source-ஐ verify பண்றது", "பணத்தின் மூலத்தைச் சரிபார்ப்பது"),
    ("verify ஆகவில்லை", "சரிபார்க்கப்படவில்லை"),
    ("verify செய்யணும்", "சரிபார்க்கணும்"),
    ("verify பண்றது", "சரிபார்ப்பது"),
    ("verify பண்ண வேண்டுமா", "சரிபார்க்க வேண்டுமா"),
    ("verify பண்ணணுமா", "சரிபார்க்கணுமா"),
    ("verify பண்ணணும்", "சரிபார்க்கணும்"),
    ("recognize செய்ய", "அடையாளம் காண"),

    # --- transfers, withdrawals, refunds, fees
    ("funds transfer பண்ண", "பணம் அனுப்ப"),
    ("transfer பண்ண பணம்", "அனுப்பின பணம்"),
    ("பணத்தை transfer பண்றது", "பணத்தை அனுப்புவது"),
    ("money transfer", "பணப் பரிமாற்றம்"),
    ("என் transfer", "என் பணப் பரிமாற்றம்"),
    ("withdrawals-க்கு charge", "பணப் பெறுகைகளுக்குக் கட்டணம்"),
    ("withdrawal செய்ய", "பணம் எடுக்க"),
    ("withdraw செய்ய", "எடுக்க"),
    ("withdrawal", "பணப் பெறுகை"),
    ("என் refund ஏன் இன்னும் statement-ல தெரியல",
     "திருப்பியளிக்கப்பட்ட என் பணம் ஏன் இன்னும் கணக்கு அறிக்கையில தெரியல"),
    ("refund கிடைக்குமா", "பணம் திரும்பக் கிடைக்குமா"),
    ("refund வாங்க", "பணத்தைத் திரும்பப் பெற"),
    ("exchange rate", "மாற்று விகிதம்"),
    ("exchange-க்கு fee", "மாற்றத்திற்குக் கட்டணம்"),
    ("exchange-க்கு", "மாற்றத்திற்கு"),
    ("மாற்றத்திற்கு fee", "மாற்றத்திற்குக் கட்டணம்"),
    ("எடுக்க fee", "எடுக்கக் கட்டணம்"),
    ("எனக்கு fee", "எனக்குக் கட்டணம்"),
    ("fee", "கட்டணம்"),
    ("வெளிநாட்டு cash-க்கான", "வெளிநாட்டுக் காசுக்கான"),
    ("apply ஆகியுள்ளது", "பிரயோகிக்கப்பட்டுள்ளது"),
    ("cash deposit", "காசு வைப்பு"),
    ("cheque-ஆல", "காசோலையால"),
    ("cheque", "காசோலை"),
    ("discount", "தள்ளுபடி"),
    ("payment-ஐ", "கொடுப்பனவை"),
    ("payment", "கொடுப்பனவு"),
    ("beneficiary-க்கு", "பயனாளிக்கு"),
    ("beneficiary", "பயனாளி"),
    ("funds", "பணம்"),

    # --- general verbs / words
    ("accept செய்கிறீர்களா", "ஏற்றுக்கொள்கிறீர்களா"),
    ("accept செய்வீர்களா", "ஏற்றுக்கொள்வீர்களா"),
    ("use செய்ய முடியுமா", "பயன்படுத்த முடியுமா"),
    ("use செய்யலாம்", "பயன்படுத்தலாம்"),
    ("இதை use பண்ண", "இதைப் பயன்படுத்த"),
    ("use பண்றது", "பயன்படுத்துவது"),
    ("பணம் add செய்ய", "பணம் சேர்க்க"),
    ("try பண்ணேன்", "முயற்சி பண்ணேன்"),
    ("நீங்கள் operate பண்றீங்க", "நீங்கள் செயல்படுறீங்க"),
    ("நீங்கள் available?", "உங்கள் சேவை கிடைக்கும்?"),
    ("option", "தெரிவு"),
    ("App-ல", "செயலியில"),
    ("app-ல", "செயலியில"),
    ("app", "செயலி"),
]

# Run after PHRASES: the English source kept case suffixes as separate words
# ("ATM இல்"), which reads wrong once the name is in Tamil script, so glue them
# back on. Matched as whole words only, so "இல்" can't hit "இல்லை" and "ஐ"
# can't hit "ஐந்து".
JOINS = [
    ("ஏடிஎம் இலிருந்து", "ஏடிஎம்மிலிருந்து"),
    ("ஏடிஎம் இல்", "ஏடிஎம்மில்"),
    ("ஏடிஎம் ஐப்", "ஏடிஎம்மைப்"),
    ("ஏடிஎம் ஆல்", "ஏடிஎம்மால்"),
    ("பின் ஐப்", "பின் இலக்கத்தைப்"),
    ("பின் ஐத்", "பின் இலக்கத்தைத்"),
    ("பின் ஐச்", "பின் இலக்கத்தைச்"),
    ("பின் ஐ", "பின் இலக்கத்தை"),
    ("பின் இன்", "பின் இலக்கத்தின்"),
    ("ஆப்பிள் பே இல்", "ஆப்பிள் பேயில்"),
    ("ஆப்பிள் பே ஐப்", "ஆப்பிள் பேயைப்"),
    ("ஆப்பிள் பே உடன்", "ஆப்பிள் பேயுடன்"),
    ("ஆப்பிள் வாட்ச் இலிருந்து", "ஆப்பிள் வாட்சிலிருந்து"),
    ("ஆப்பிள் வாட்ச் இல்", "ஆப்பிள் வாட்சில்"),
    ("ஆப்பிள் வாட்ச் ஐப்", "ஆப்பிள் வாட்சைப்"),
    ("ஆப்பிள் வாட்ச் உடன்", "ஆப்பிள் வாட்சுடன்"),
    ("அமெரிக்கன் எக்ஸ்பிரஸ் ஐப்", "அமெரிக்கன் எக்ஸ்பிரஸைப்"),
    ("அமெரிக்கன் எக்ஸ்பிரஸ் ஐ", "அமெரிக்கன் எக்ஸ்பிரஸை"),
    ("கூகுள் பே இல்", "கூகுள் பேயில்"),
    ("கூகுள் பே ஐப்", "கூகுள் பேயைப்"),
    ("கூகுள் பே ஐ", "கூகுள் பேயை"),
    ("கூகுள் ப்ளே இல்", "கூகுள் ப்ளேயில்"),
    ("கூகுள் ப்ளே ஐப்", "கூகுள் ப்ளேயைப்"),
    ("ஸ்விஃப்ட் இலிருந்து", "ஸ்விஃப்டிலிருந்து"),
    ("ஸ்விஃப்ட் ஐப்", "ஸ்விஃப்டைப்"),
    ("ஈபே இல்", "ஈபேயில்"),
]


def _compile(src: str, whole_word: bool = False) -> re.Pattern:
    """Exact-substring pattern that won't match inside a longer Latin word
    (or, with whole_word, run on into a following Tamil letter)."""
    pat = re.escape(src)
    if LATIN.match(src[0]):
        pat = r"(?<![A-Za-z])" + pat
    if LATIN.match(src[-1]):
        pat += r"(?![A-Za-z])"
    elif whole_word:
        pat += r"(?![஀-௿])"
    return re.compile(pat)


RULES = ([(_compile(src), dst) for src, dst in PHRASES]
         + [(_compile(src, whole_word=True), dst) for src, dst in JOINS])


def fix(text: str) -> str:
    text = GLOSS.sub("", text)
    for pat, dst in RULES:
        text = pat.sub(dst, text)
    return text


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT_FILE, help="dataset CSV (default: tamil/train_labeled.csv)")
    ap.add_argument("--apply", action="store_true", help="rewrite the CSV in place")
    ap.add_argument("--report", help="write id,text_en,old,new for every changed row to this CSV")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        rows = list(reader)

    words = Counter(w for r in rows for w in LATIN_WORD.findall(r["text"]))
    print(f"{os.path.relpath(args.file, DATASETS)}: {len(rows)} rows, "
          f"{sum(1 for r in rows if LATIN.search(r['text']))} contain English, "
          f"{len(words)} distinct English words")
    for w, c in words.most_common():
        print(f"  {c:5d}  {w}")

    changed, leftover = [], []
    for r in rows:
        old = r["text"]
        if not LATIN.search(old):
            continue
        new = fix(old)
        if new != old:
            changed.append((r, old, new))
        if LATIN.search(new):
            leftover.append((r["id"], new))

    print(f"\n{len(changed)} row(s) {'updated' if args.apply else 'would change'}; "
          f"{len(leftover)} still contain English")
    for i, t in leftover:
        print(f"  id={i}: {t}")

    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "text_en", "old", "new"])
            w.writerows((r["id"], r["text_en"], old, new) for r, old, new in changed)
        print(f"review file: {args.report}")

    if args.apply and changed:
        for r, _, new in changed:
            r["text"] = new
        with open(args.file, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
