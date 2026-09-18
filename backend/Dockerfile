FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    curl \
    ca-certificates \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libgobject-2.0-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Docker CLI static binary (docker.io package only ships dockerd, not the CLI)
RUN DOCKER_VERSION=27.4.1 && \
    curl -fsSLo /tmp/docker.tgz \
      "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz" && \
    tar xz -C /tmp -f /tmp/docker.tgz && \
    mv /tmp/docker/docker /usr/local/bin/docker && \
    rm -rf /tmp/docker /tmp/docker.tgz

# Trivy vulnerability scanner
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/reports

EXPOSE 8000
