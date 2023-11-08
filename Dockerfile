FROM python:3.9

WORKDIR /app/

RUN adduser appuser

COPY --chown=appuser:appuser ./requirements.txt /app/
RUN pip install -r requirements.txt

COPY --chown=appuser:appuser bad /app/bad/

USER appuser

ENTRYPOINT PYTHONPATH=. python ./bad/main.py