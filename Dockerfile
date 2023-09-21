FROM gcc:11-bullseye AS isolate-build

WORKDIR /app

RUN apt-get update && apt-get install -y libcap-dev && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/ioi/isolate.git

WORKDIR /app/isolate
RUN CFLAGS="-static" make isolate
RUN make install

FROM python:3.11-bookworm AS base

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PATH=.local/bin:$PATH

RUN pip install --upgrade pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

COPY . /app/

COPY --from=isolate-build /app/isolate /app/isolate/
COPY --from=isolate-build /lib/x86_64-linux-gnu/libcap* /lib/x86_64-linux-gnu/
COPY --from=isolate-build /usr/local/etc/isolate /usr/local/etc/

WORKDIR /app/src
CMD ["python3 main.py"]