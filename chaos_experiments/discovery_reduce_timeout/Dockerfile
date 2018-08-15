FROM python:3.6

WORKDIR experiment

RUN mkdir output

COPY experiment.json .

COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["chaos", "run", "experiment.json"]
