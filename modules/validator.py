"""
============================================================
DATA REDUNDANCY REMOVAL SYSTEM - Input Validator Module
File: modules/validator.py
Purpose: Validates all fields before any record is processed.
         Catches bad data early to ensure database integrity.
============================================================
"""

import re


# ─────────────────────────────────────────────
# Regex Patterns for Validation
# ─────────────────────────────────────────────
EMAIL_REGEX = re.compile(r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^[6-9]\d{9}$')        # Indian 10-digit mobile numbers
UID_REGEX   = re.compile(r'^[A-Z0-9]{3,20}$')    # Alphanumeric IDs like EMP001


def validate_record(data: dict) -> dict:
    """
    Validates all fields of a submitted record.
    
    Checks:
    1. Required fields are not empty
    2. Email format is valid
    3. Phone number is valid (10 digits, starts with 6-9)
    4. Unique ID format is valid
    
    Args:
        data (dict): Dictionary of form fields

    Returns:
        dict: A dictionary of field errors. Empty dict means no errors.
              Example: {"email": "Invalid email format"}
    """
    errors = {}

    # ── Unique ID ──────────────────────────────
    uid = data.get("unique_id", "").strip()
    if not uid:
        errors["unique_id"] = "Unique ID is required."
    elif not UID_REGEX.match(uid):
        errors["unique_id"] = "Unique ID must be 3-20 alphanumeric characters (e.g., EMP001)."

    # ── Full Name ──────────────────────────────
    name = data.get("full_name", "").strip()
    if not name:
        errors["full_name"] = "Full name is required."
    elif len(name) < 3:
        errors["full_name"] = "Full name must be at least 3 characters."
    elif len(name) > 255:
        errors["full_name"] = "Full name is too long (max 255 characters)."

    # ── Email ──────────────────────────────────
    email = data.get("email", "").strip()
    if not email:
        errors["email"] = "Email address is required."
    elif not EMAIL_REGEX.match(email):
        errors["email"] = "Please enter a valid email address (e.g., name@domain.com)."

    # ── Phone Number ───────────────────────────
    phone = data.get("phone", "").strip()
    # Remove spaces, dashes, and country codes for validation
    phone_clean = re.sub(r'[\s\-\+]', '', phone)
    if phone_clean.startswith("91") and len(phone_clean) == 12:
        phone_clean = phone_clean[2:]  # Remove +91 prefix
    if not phone:
        errors["phone"] = "Phone number is required."
    elif not PHONE_REGEX.match(phone_clean):
        errors["phone"] = "Enter a valid 10-digit Indian mobile number (starts with 6-9)."

    # ── Address (optional but recommended) ────
    address = data.get("address", "").strip()
    if address and len(address) > 500:
        errors["address"] = "Address is too long (max 500 characters)."

    # ── City ───────────────────────────────────
    city = data.get("city", "").strip()
    if not city:
        errors["city"] = "City is required."

    # ── State ──────────────────────────────────
    state = data.get("state", "").strip()
    if not state:
        errors["state"] = "State is required."

    return errors


def sanitize_string(value: str) -> str:
    """
    Strips leading/trailing whitespace and collapses multiple spaces.
    Useful for normalizing data before comparison.
    
    Args:
        value (str): Raw string input

    Returns:
        str: Clean, normalized string
    """
    return " ".join(value.strip().split())
