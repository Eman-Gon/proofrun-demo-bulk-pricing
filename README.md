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

## Prepare this repo for ProofRun

From `main`, use Python 3.12, Git, and a running Docker daemon:

```sh
docker pull python:3.12-slim
python3.12 scripts/prepare_proofrun.py
```

The helper builds both tagged releases from their committed Git trees, runs the
original tests in each image as an unprivileged user with no network, and writes
`.proofrun/setup/targets.json`, `request.json`, and `setup.json`. It resolves the
trusted collector image to an immutable ID. Generated files remain local and
ignored by Git. The helper does not call a model or deploy a repair. For another
preparation, choose a fresh `--output .proofrun/setup-02` directory.

The registry includes the real local repository path, exact revision hashes,
immutable Docker image IDs, startup/test commands, and a general compatibility
requirement. The presenter README and setup scripts are excluded from agent
inspection; the product contract and application source remain included. No
predeclared failing request or prepared repair is passed to the investigator.

In the separate ProofRun checkout, after installing its worker dependencies and
exporting your private `OPENROUTER_API_KEY` and explicit `PROOFRUN_MODEL`, run:

```sh
python3.12 -m src.proofrun.release_api \
  --targets ../proofrun-demo-bulk-pricing/.proofrun/setup/targets.json \
  --once ../proofrun-demo-bulk-pricing/.proofrun/setup/request.json \
  --artifacts .commit-watch/proofrun-demo-bulk-pricing-run-01
```

These relative paths assume the two checkouts are siblings. Use an absolute path
if yours are elsewhere. Select a new artifact directory for every run. A `skip`
verdict exits with code 2; inspect the result artifacts rather than treating that
exit as absence of results. Model access can incur your provider's normal costs.
Do not put keys in this demo repository or in its Docker images.

The default target scope is `operator` for local use. Set `--scope WORKSPACE_ID`
when preparing it for an authorized portal workspace. Portal initiation, remote
hosting, and staging replay require their own actual configuration and evidence.

The default `main` branch contains the working app and setup helper. The
`demo-baseline` and `demo-update` tags stay fixed to the original two releases;
the helper always compares those tags, regardless of later setup-doc changes.
