FROM rocker/r-ver:4.3.2

WORKDIR /app

# Install system dependencies for mirt
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    gfortran \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgit2-dev \
    libv8-dev \
    libicu-dev \
    libsodium-dev \
    libunwind-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('plumber','jsonlite','dplyr','ggplot2','purrr','mirt'), repos='https://cloud.r-project.org/')"

# Verify
RUN R -e "library(plumber); library(mirt); library(jsonlite); library(dplyr); library(ggplot2); library(purrr); cat('✓ All packages installed successfully\n')"

COPY . .

EXPOSE 8001

# Simple health check that actually works
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["R", "-e", "pr <- plumber::plumb('plumber.R'); pr$run(host='0.0.0.0', port=8001)"]
