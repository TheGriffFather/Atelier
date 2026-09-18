# =============================================================================
# Atelier - Digital Catalogue Raisonne Platform
# Multi-stage build: Node.js (CSS) -> Python (Runtime)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Tailwind CSS
# -----------------------------------------------------------------------------
FROM node:20-slim AS css-builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json ./
COPY tailwind.config.js ./

# Install dependencies (including devDependencies for tailwindcss)
RUN npm ci

# Copy source files needed for Tailwind
COPY src/api/static/css/input.css ./src/api/static/css/
COPY src/api/templates/ ./src/api/templates/

# Build minified CSS
RUN npm run css:build

# -----------------------------------------------------------------------------
# Stage 2: Python Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package metadata and source before building the Python wheel.
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY config/ ./config/

# Install Python dependencies
# Note: We install playwright package but skip browser installation (API-only mode)
RUN pip install --no-cache-dir . \
    && rm -rf ~/.cache/pip

# Copy operational helpers; application source was installed above.
COPY scripts/ ./scripts/

# Preserve the newly built CSS after copying committed static assets.
COPY --from=css-builder /build/src/api/static/css/output.css ./src/api/static/css/output.css

# Copy entrypoint script and fix Windows line endings
COPY docker-entrypoint.sh ./
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

# Create data directory (will be mounted as volume)
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
