# Base image: Ubuntu 22.04
FROM ubuntu:22.04

# ARGs: Set build arguments for compatibility
ARG TARGETPLATFORM=linux/amd64,linux/arm64
ARG DEBIAN_FRONTEND=noninteractive

# Install essential packages, Java, and Neo4j 5.5.0
RUN apt-get update && \
    apt-get install -y wget gnupg software-properties-common openjdk-17-jdk git && \
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - && \
    echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list && \
    apt-get update && \
    apt-get install -y nano unzip neo4j=1:5.5.0 python3-pip && \
    apt-get autoremove -y && \
    apt-get clean

# Install required Python libraries
RUN pip install --upgrade pip && \
    pip install neo4j pandas pyarrow

# Set the Neo4j password using neo4j-admin
RUN neo4j-admin dbms set-initial-password project1phase1

# Configure Neo4j for remote access and plugin settings
RUN echo "server.default_listen_address=0.0.0.0" >> /etc/neo4j/neo4j.conf && \
    echo "dbms.security.procedures.unrestricted=gds.*,apoc.*" >> /etc/neo4j/neo4j.conf && \
    echo "dbms.security.procedures.allowlist=gds.*,apoc.*" >> /etc/neo4j/neo4j.conf

# Download and install GDS plugin directly to Neo4j's plugin folder
RUN wget https://graphdatascience.ninja/neo4j-graph-data-science-2.3.1.zip -O gds.zip && \
    unzip gds.zip -d /var/lib/neo4j/plugins/ && \
    chmod 777 /var/lib/neo4j/plugins/* && \
    rm gds.zip

# Download the dataset
RUN wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet -P /app/data/

# Add GitHub to known hosts and clone the repository securely with BuildKit
RUN mkdir -p ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN --mount=type=ssh git clone git@github.com:Fall-24-CSE511-Data-Processing-at-Scale/Project-1-ssrika21.git /app/repo

# Set permissions for the data loader script
RUN chmod +x /app/repo/data_loader.py

# Expose Neo4j ports for external access
EXPOSE 7474 7687

# Start Neo4j, load data, and keep Neo4j running
CMD neo4j console & sleep 20 && python3 /app/repo/data_loader.py && tail -f /var/log/neo4j/debug.log