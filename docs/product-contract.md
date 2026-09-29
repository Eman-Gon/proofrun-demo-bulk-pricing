# Wholesale quote contract

The wholesale customer purchases `WIDGET-100` at a fixed unit price of $100 USD.
An order of **10 or more units receives a 10% discount on its subtotal**.
Orders of fewer than 10 units receive no discount. There are no taxes, shipping
charges, additional promotions, or external price lookups in this demo.

`POST /quotes` accepts a JSON object with exactly these fields:

- `sku`: the string `WIDGET-100`.
- `quantity`: an integer between 1 and 10,000, inclusive. Booleans, floats, strings,
  nulls, zero, negative values, and values beyond the limit are invalid.

Successful responses have status 200 and include `sku`, `quantity`, `currency`
(`USD`), `unit_price_cents`, `subtotal_cents`, `discount_cents`, and `total_cents`.
All monetary values use integer cents. Repeating the same request produces the
same JSON response. Quotes are read-only and do not create orders.

Unknown SKUs and invalid request values return status 422 and an `error` object
with stable `code` and `message` strings. Unsupported media types return 415;
malformed JSON returns 400; bodies larger than 16,384 bytes return 413.
JSON bodies must use UTF-8 and `Content-Type: application/json`. Duplicate JSON
keys and nonstandard numeric values such as NaN are rejected.

`GET /health` returns status 200 and `{"status":"ok"}`. `GET /` serves the quote
page. Both routes are available without authentication. The service stores no
customer data and makes no outbound network requests.
