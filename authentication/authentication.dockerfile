FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY authentication.py ./authentication.py
COPY configuration.py ./configuration.py
COPY models.py ./models.py
COPY authorizationDecorator.py ./authorizationDecorator.py
COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

# ENV PYTHONPATH="/opt/src/authentication"

ENTRYPOINT ["python", "./authentication.py"]