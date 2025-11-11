#!/bin/bash

# MySQL health check script
MYSQL_USER="cluster_monitor"
MYSQL_PASSWORD="monitor_pass"

# Check if MySQL is running
if ! mysqladmin ping -h localhost -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" --silent; then
    echo "MySQL is not responding"
    exit 1
fi

# Check if we can connect and query
if ! mysql -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1; then
    echo "Cannot execute queries"
    exit 1
fi

# Check replication status (if slave)
SLAVE_STATUS=$(mysql -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SHOW SLAVE STATUS\G" 2>/dev/null | grep "Slave_IO_Running" | awk '{print $2}')
if [ ! -z "$SLAVE_STATUS" ] && [ "$SLAVE_STATUS" != "Yes" ]; then
    echo "Replication IO thread not running"
    exit 1
fi

echo "MySQL health check passed"
exit 0