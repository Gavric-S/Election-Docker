FROM python:3

RUN mkdir -p /opt/src/official
WORKDIR /opt/src/official

COPY official.py ./official.py
COPY configuration.py ./configuration.py
COPY models.py ./models.py
COPY requirements.txt ./requirements.txt
COPY authorizationDecorator.py ./authorizationDecorator.py

RUN pip install -r ./requirements.txt

# ENV PYTHONPATH="/opt/src/official"

ENTRYPOINT ["python", "./official.py"]