FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
COPY --chown=65532:65532 . /workspace
USER 65532:65532
EXPOSE 8080
CMD ["python", "-m", "pricing_service"]
