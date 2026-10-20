"""Kenyan phone normalization for M-Pesa Express."""

import re


class InvalidPhoneNumber(ValueError):
    """The supplied phone number is not a supported Kenyan MSISDN."""


def normalize_ke_phone(value: str) -> str:
    digits = re.sub(r"[\s()+-]", "", value)
    if digits.startswith("0"):
        digits = "254" + digits[1:]
    if not re.fullmatch(r"254(?:7|1)\d{8}", digits):
        raise InvalidPhoneNumber("Enter a valid Kenyan M-Pesa phone number")
    return digits
