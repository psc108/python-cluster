FROM mysql:8.0.35

# Install additional tools for cluster management
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy custom configuration
COPY config/my.cnf /etc/mysql/conf.d/cluster.cnf
COPY scripts/init-cluster.sh /docker-entrypoint-initdb.d/
COPY scripts/health-check.sh /usr/local/bin/

# Make scripts executable
RUN chmod +x /docker-entrypoint-initdb.d/init-cluster.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Expose MySQL ports
EXPOSE 3306 33060

# Use custom health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD /usr/local/bin/health-check.sh