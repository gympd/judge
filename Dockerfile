# isolate build
FROM gcc:14-bookworm AS isolate-build

WORKDIR /app

RUN apt-get update && apt-get install -y libcap-dev && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/ioi/isolate.git

WORKDIR /app/isolate
RUN CFLAGS="-static" make isolate
RUN make install

# our judge
FROM python:3.11-slim-bookworm AS base

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PATH=.local/bin:$PATH

# install packages required for each runner:
## (judge): pipenv (other packages are defined in Pipfile)
## python: ruff
## c++: g++
RUN pip install --upgrade ruff pipenv
RUN apt-get update && apt-get install -y g++ && rm -rf /var/lib/apt/lists/*

COPY . /app/
RUN pipenv install --system --deploy

COPY --from=isolate-build /app/isolate /app/isolate/
COPY --from=isolate-build /usr/lib/x86_64-linux-gnu/libcap* /lib/x86_64-linux-gnu/
COPY --from=isolate-build /usr/local/etc/isolate /usr/local/etc/

WORKDIR /app/src
CMD ["python3 main.py"]