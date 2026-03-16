# nsjail.Dockerfile
FROM ubuntu:22.04

# Устанавливаем зависимости для сборки
RUN apt-get update && apt-get install -y \
    autoconf \
    bison \
    flex \
    gcc \
    g++ \
    git \
    libprotobuf-dev \
    libnl-3-dev \
    libnl-route-3-dev \
    libtool \
    make \
    pkg-config \
    protobuf-compiler \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Клонируем и собираем nsjail
RUN git clone https://github.com/google/nsjail.git /nsjail
WORKDIR /nsjail
RUN make
RUN cp nsjail /usr/local/bin/

RUN mkdir -p /snekbox /snekbox/user_base /snekbin

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && ln -s /usr/bin/python3 /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/nsjail
COPY nsjail.cfg /etc/nsjail/python.cfg

# Точка входа
ENTRYPOINT ["nsjail", "--config", "/etc/nsjail/python.cfg"]