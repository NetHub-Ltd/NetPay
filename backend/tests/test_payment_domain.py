from app.models import Payment
from app.payments.phone import InvalidPhoneNumber, normalize_ke_phone
from app.payments.state import apply_status


def test_phone_normalization_accepts_common_kenyan_formats() -> None:
    assert normalize_ke_phone("0712 345 678") == "254712345678"
    assert normalize_ke_phone("+254 712-345-678") == "254712345678"
    assert normalize_ke_phone("254112345678") == "254112345678"


def test_phone_normalization_rejects_invalid_number() -> None:
    try:
        normalize_ke_phone("12345")
    except InvalidPhoneNumber:
        pass
    else:
        raise AssertionError("invalid phone number should be rejected")


def test_payment_state_does_not_regress_from_terminal_state() -> None:
    payment = Payment(
        merchant_id="d7b4f2df-06a1-4d7e-bf3d-1b96bffec8b1",
        integration_id="d7b4f2df-06a1-4d7e-bf3d-1b96bffec8b1",
        client_reference="ref-1",
        amount_minor=100,
        phone_number="254712345678",
        status="succeeded",
    )

    assert not apply_status(payment, "failed")
    assert payment.status == "succeeded"


def test_unknown_payment_can_resolve_from_provider_evidence() -> None:
    payment = Payment(
        merchant_id="d7b4f2df-06a1-4d7e-bf3d-1b96bffec8b1",
        integration_id="d7b4f2df-06a1-4d7e-bf3d-1b96bffec8b1",
        client_reference="ref-2",
        amount_minor=100,
        phone_number="254712345678",
        status="unknown",
    )

    assert apply_status(payment, "succeeded")
    assert payment.status == "succeeded"
