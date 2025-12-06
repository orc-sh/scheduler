# Multi-stage build to copy exporters from their official images
FROM prom/node-exporter:latest AS node-exporter
FROM grafana/celery-exporter:latest AS celery-exporter

# Base image with supervisord
FROM ubuntu:22.04

# Install supervisord and Python 3.11
RUN apt-get update && apt-get install -y \
    supervisor \
    curl \
    python3.11 \
    python3.11-distutils \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python3
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3

# Create dist-packages directory (Ubuntu/Debian convention)
RUN mkdir -p /usr/local/lib/python3.11/dist-packages

# Copy exporters from their official images
COPY --from=node-exporter /bin/node_exporter /usr/local/bin/node_exporter

# Copy celery-exporter Python package and all dependencies from official image
# celery-exporter is a Python module, not a binary, so we copy the entire site-packages
# Ubuntu uses dist-packages instead of site-packages, so we copy there
COPY --from=celery-exporter /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/dist-packages/

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create supervisor log directory
RUN mkdir -p /var/log/supervisor

# Expose exporter ports
EXPOSE 9100 9808

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf", "-n"]

