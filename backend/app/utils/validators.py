"""
FinTwin AI — Custom Field Validators
GSTIN, PAN, IFSC, mobile number validation with check-digit verification.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import field_validator

# ============================================================
# GSTIN VALIDATOR
# ============================================================

GSTIN_PATTERN = re.compile(
    r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$'
)

# Check digit charset for GSTIN
_GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def validate_gstin(gstin: str) -> str:
    """
    Validate GSTIN format and check digit.
    Format: 2-digit state code + 10-char PAN + entity number + Z + check digit
    """
    if not gstin:
        raise ValueError("GSTIN is required")
    
    gstin = gstin.strip().upper()
    
    if not GSTIN_PATTERN.match(gstin):
        raise ValueError(
            "Invalid GSTIN format. Expected: 2-digit state + 5 letters + 4 digits + letter + digit/letter + Z + check digit"
        )
    
    # Verify state code (01-37)
    state_code = int(gstin[:2])
    if not (1 <= state_code <= 37):
        raise ValueError(f"Invalid state code: {gstin[:2]}")
    
    # Verify check digit using Luhn-like algorithm
    if not _verify_gstin_check_digit(gstin):
        raise ValueError("Invalid GSTIN check digit")
    
    return gstin


def _verify_gstin_check_digit(gstin: str) -> bool:
    """Verify the GSTIN check digit using the official algorithm."""
    charset = _GSTIN_CHARSET
    factor = 2
    total = 0
    
    for char in reversed(gstin[:-1]):
        if char not in charset:
            return False
        idx = charset.index(char)
        product = factor * idx
        total += (product // 36) + (product % 36)
        factor = 1 if factor == 2 else 2
    
    check_idx = (36 - (total % 36)) % 36
    expected = charset[check_idx]
    return gstin[-1] == expected


# ============================================================
# PAN VALIDATOR
# ============================================================

PAN_PATTERN = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]$')

# PAN type codes (4th character)
PAN_TYPE_MAP = {
    'P': 'Individual',
    'F': 'Firm',
    'C': 'Company',
    'H': 'HUF',
    'A': 'AOP',
    'B': 'BOI',
    'G': 'Government',
    'J': 'Artificial Juridical Person',
    'L': 'Local Authority',
    'T': 'Trust',
}


def validate_pan(pan: str) -> str:
    """Validate PAN (Permanent Account Number) format."""
    if not pan:
        raise ValueError("PAN is required")
    
    pan = pan.strip().upper()
    
    if not PAN_PATTERN.match(pan):
        raise ValueError(
            "Invalid PAN format. Expected: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)"
        )
    
    return pan


# ============================================================
# IFSC VALIDATOR
# ============================================================

IFSC_PATTERN = re.compile(r'^[A-Z]{4}0[A-Z0-9]{6}$')


def validate_ifsc(ifsc: str) -> str:
    """Validate IFSC code format."""
    if not ifsc:
        return ifsc
    
    ifsc = ifsc.strip().upper()
    if not IFSC_PATTERN.match(ifsc):
        raise ValueError(
            "Invalid IFSC code. Expected: 4 letters + 0 + 6 alphanumeric characters"
        )
    return ifsc


# ============================================================
# MOBILE NUMBER VALIDATOR
# ============================================================

MOBILE_PATTERN = re.compile(r'^[6-9][0-9]{9}$')


def validate_mobile(phone: str) -> str:
    """Validate Indian mobile number."""
    if not phone:
        return phone
    
    # Remove spaces, dashes, country code
    clean = re.sub(r'[\s\-\.\(\)]', '', phone)
    clean = re.sub(r'^\+?91', '', clean)
    
    if not MOBILE_PATTERN.match(clean):
        raise ValueError(
            "Invalid mobile number. Must be 10 digits starting with 6-9"
        )
    return clean


# ============================================================
# PINCODE VALIDATOR
# ============================================================

def validate_pincode(pincode: str) -> str:
    """Validate 6-digit Indian pincode."""
    if not pincode:
        return pincode
    clean = re.sub(r'\s', '', pincode)
    if not re.match(r'^[1-9][0-9]{5}$', clean):
        raise ValueError("Invalid pincode. Must be a 6-digit number.")
    return clean


# ============================================================
# VALID INDIAN STATES
# ============================================================

INDIAN_STATES = {
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
    "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    # Union Territories
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh",
    "Lakshadweep", "Puducherry",
}


def validate_indian_state(state: str) -> str:
    """Validate Indian state name."""
    if state not in INDIAN_STATES:
        raise ValueError(f"'{state}' is not a valid Indian state or union territory")
    return state
