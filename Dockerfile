FROM docker/compose:alpine-1.29.2

WORKDIR /app

# Copy all files
COPY . .

# Install curl for health checks
RUN apk add --no-cache curl

# Create shared directory
RUN mkdir -p shared_data

# Expose ports
EXPOSE 80 8000 8001

# Health check for the main backend
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["docker-compose", "-f", "docker-compose.prod.yml", "up"]