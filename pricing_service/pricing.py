"""Quote calculation, with monetary values expressed as integer USD cents."""

SKU = "WIDGET-100"
UNIT_PRICE_CENTS = 10_000
MAX_QUANTITY = 10_000


class InvalidQuote(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def quote(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise InvalidQuote("invalid_request", "The request must be a JSON object.")
    if set(payload) != {"sku", "quantity"}:
        raise InvalidQuote("invalid_fields", "Provide exactly sku and quantity.")
    if payload["sku"] != SKU:
        raise InvalidQuote("unknown_sku", "The supported SKU is WIDGET-100.")
    quantity = payload["quantity"]
    if type(quantity) is not int or not 1 <= quantity <= MAX_QUANTITY:
        raise InvalidQuote("invalid_quantity", "Quantity must be an integer from 1 to 10000.")

    subtotal = quantity * UNIT_PRICE_CENTS
    eligible_for_discount = quantity >= 10
    discount = subtotal // 10 if eligible_for_discount else 0
    return {
        "sku": SKU,
        "quantity": quantity,
        "unit_price_cents": UNIT_PRICE_CENTS,
        "subtotal_cents": subtotal,
        "discount_cents": discount,
        "total_cents": subtotal - discount,
        "currency": "USD",
    }
