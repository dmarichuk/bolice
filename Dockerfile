FROM python:3.10.4-alpine AS requirements-stage

# Adding dependencies for poetry
RUN apk update && apk upgrade && apk add gcc musl-dev libffi-dev

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.10.4

RUN apt-get update && apt-get upgrade -y && apt-get install gfortran libopenblas-dev bash -y

WORKDIR /workspace

COPY --from=requirements-stage /tmp/requirements.txt /workspace/requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./app/static/ ./
COPY  ./app/ ./

CMD ["python3", "bot.py"]