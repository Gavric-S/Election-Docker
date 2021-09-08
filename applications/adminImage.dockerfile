FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR /opt/src/admin

COPY admin.py ./admin.py
COPY configuration.py ./configuration.py
COPY models.py ./models.py
COPY requirements.txt ./requirements.txt
COPY authorizationDecorator.py ./authorizationDecorator.py

RUN pip install -r ./requirements.txt

# ENV PYTHONPATH="/opt/src/admin"
# ENV TZ=Europe/Belgrade
# cd /var/lib/boot2docker
# docker stack deploy --compose-file stack.yaml authentication_stack

ENTRYPOINT ["python", "./admin.py"]