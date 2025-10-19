FROM docker.elastic.co/kibana/kibana:8.11.0

# Switch to root to install packages and set permissions
USER root

# Install curl if not present (should be available in Kibana image)
RUN which curl || (apt-get update && apt-get install -y curl)

# Create directory for saved objects
RUN mkdir -p /usr/share/kibana/saved_objects

# Copy saved objects
COPY dashboards/ /usr/share/kibana/saved_objects/

# Copy import script
COPY import-dashboards.sh /usr/local/bin/import-dashboards.sh

# Make script executable
RUN chmod +x /usr/local/bin/import-dashboards.sh

# Verify files are copied correctly
RUN ls -la /usr/share/kibana/saved_objects/ && \
    ls -la /usr/local/bin/import-dashboards.sh

# Switch back to kibana user
USER kibana

# Run import script in background after Kibana starts
CMD bash /usr/local/bin/import-dashboards.sh & /usr/share/kibana/bin/kibana
