ARG PYTHON_BASE_IMAGE=python:3.9-slim
FROM ${PYTHON_BASE_IMAGE} AS builder

# Set environment variables for the build
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for the project
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        curl \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create a virtual environment for dependencies
RUN python -m venv /opt/env

# Set virtual environment path
ENV VIRTUAL_ENV="/opt/env"
ENV PATH="/opt/env/bin:$PATH"

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . /app/

# Collect static files for Django
RUN python manage.py collectstatic --noinput

# Runtime stage
FROM ${PYTHON_BASE_IMAGE} AS runner

# Copy virtual environment and application from builder
COPY --from=builder /opt/env /opt/env
COPY --from=builder /app /app

# Install runtime dependencies only
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq5 \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Make sure we use the virtual environment
ENV PATH="/opt/env/bin:$PATH"
ENV DJANGO_SETTINGS_MODULE=backend.settings

# Create user to run as non-root
RUN useradd --uid 1000 --create-home runner

# Set proper ownership and permissions
RUN chown -R runner:runner /app \
    && chmod 755 /app

# Switch to non-root user
USER runner

WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose Django port
EXPOSE 8000
