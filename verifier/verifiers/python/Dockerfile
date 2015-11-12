FROM python:3.4-slim

RUN mkdir -p /app && adduser --system verifier

ENV PATH="$PATH:/app"
COPY verify /app/
RUN chmod +x /app/verify