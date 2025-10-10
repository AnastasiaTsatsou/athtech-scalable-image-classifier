FROM opensearchproject/opensearch-dashboards:2.11.0

# Copy configuration
COPY opensearch_dashboards.yml /usr/share/opensearch-dashboards/config/opensearch_dashboards.yml

# Copy saved objects
COPY dashboards/ /usr/share/opensearch-dashboards/saved_objects/

# Copy import script
COPY import-dashboards.sh /usr/local/bin/import-dashboards.sh

# Run import script in background after OpenSearch Dashboards starts
CMD bash /usr/local/bin/import-dashboards.sh & /usr/share/opensearch-dashboards/bin/opensearch-dashboards
