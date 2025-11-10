FROM php:8.2-apache

# Install required PHP extensions and tools
RUN apt-get update && apt-get install -y \
    curl \
    zip \
    unzip \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    sudo \
    && docker-php-ext-install pdo pdo_mysql \
    && a2enmod rewrite headers deflate \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /var/www/html

# Copy application files
COPY src/ .
COPY apache.conf /etc/apache2/sites-available/000-default.conf

# Set permissions and configure sudo for www-data
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html \
    && groupadd -f docker \
    && usermod -aG docker www-data \
    && echo "www-data ALL=(ALL) NOPASSWD: /usr/bin/docker" >> /etc/sudoers

# Create data directory for persistent storage
RUN mkdir -p /var/www/html/data \
    && chown -R www-data:www-data /var/www/html/data

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health.php || exit 1

# Start Apache
CMD ["apache2-foreground"]