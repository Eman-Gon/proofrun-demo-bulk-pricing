# Wholesale quote demo for ProofRun

A tiny customer-facing pricing API and quote page for a **prepared regression
demo**. The client expects orders of 10 or more units to receive a 10% discount.
A seeded release changes the discount boundary while the original tests still
pass. This is an intentionally constructed example, not evidence that ProofRun
has already found or repaired a production defect.

## Run locally

Requires Python 3.12. There are no third-party dependencies.

```sh
python3 -m pricing_service --host 127.0.0.1 --port 8080
```

Open <http://localhost:8080>. In another terminal, run:

```sh
python3 -m unittest discover -s tests -v
curl -s http://localhost:8080/health
curl -s http://localhost:8080/quotes \
  -H 'Content-Type: application/json' \
  -d '{"sku":"WIDGET-100","quantity":10}'
```

## Run in Docker

```sh
docker build -t proofrun-demo-bulk-pricing:local .
docker run --rm -p 127.0.0.1:8080:8080 proofrun-demo-bulk-pricing:local
```

The image runs Python 3.12 as an unprivileged numeric user from `/workspace`.
Run the original tests inside the image with:

```sh
docker run --rm proofrun-demo-bulk-pricing:local python -m unittest discover -s tests -v
```

## Demo sequence

The two immutable demo tags define the comparison:

| Version | Git reference | Prepared behavior |
| --- | --- | --- |
| Working baseline | `demo-baseline` | 10 or more units get the discount |
| Candidate release | `demo-update` | Only more than 10 units get the discount |

`main` is the working app. Branch `codex/pricing-refactor` contains the candidate
release. The candidate commit changes only the eligibility condition. The
original suite covers 1 and 20 units plus invalid inputs; it deliberately omits
the 10-unit boundary. Keep this coverage gap explicit when presenting the demo.

1. On `main`, open the page and quote 10 units. The total is **$900**.
2. Stop the server. Switch to `codex/pricing-refactor` and run the tests. They pass.
3. Restart the server and quote the same 10 units. The total is now **$1,000**.
4. Configure ProofRun to compare `demo-baseline` with `demo-update`, using the
   behavior in [the product contract](docs/product-contract.md). Supply the test
   command and startup command shown above and separate prepared environments
   for each revision.
5. Run the investigation and inspect its actual requests, responses, and verdict.
   A repair is a separate candidate that must pass the original suite and checks
   for the contract's boundary and invalid inputs before it can be called verified.
6. Stop the server and return to `main` when finished.

This repository includes no prepared repair and no fabricated investigation
results. A passing local check is not a deployment or staging verification.
ProofRun integration, model access, and any deployment event must be configured
separately; this demo does not claim automatic DuploCloud or other sponsor wiring.

## Service scope

- `GET /`: single-page quote form.
- `GET /health`: deterministic health response.
- `POST /quotes`: deterministic USD quote, using integer cents.
- No authentication, persistence, external APIs, or real customer data.

This standard-library server is intended for a local or isolated demo. Its default
container bind is `0.0.0.0`; the local command and Docker example above restrict
access to your own machine. Full request and response expectations are documented
in [docs/product-contract.md](docs/product-contract.md).
