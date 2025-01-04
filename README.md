# Taxi Graph Workflow

## Project Overview
This project explores Neo4j’s capabilities by analyzing a dataset of NYC taxi trips, where each trip represents a `TRIP` relationship between two `Location` nodes. By setting up the Neo4j Graph Data Science (GDS) library, we implement:
- **PageRank**: To determine the relative importance of locations.
- **Breadth-First Search (BFS)**: To find the shortest paths between start and target locations.

## Setup and Installation
### Steps to Set Up

1. **Clone the Repository**  
   Clone the GitHub repository to your local machine:
   ```bash
   git clone git@github.com:sriranjan06/Taxi-Graph-Workflow.git
   
   cd Taxi-Graph-Workflow
   ```

2. **SSH Key Setup**  
   Ensure SSH keys are configured for private repositories.

3. **Build the Docker Image**  
   Use Docker BuildKit to build the image with SSH access:
   ```bash
   DOCKER_BUILDKIT=1 docker build --no-cache --ssh default -t project1_neo4j .
   ```

4. **Run the Docker Container**  
   Once built, start the container and expose necessary ports:
   ```bash
   docker run -d -p 7474:7474 -p 7687:7687 project1_neo4j
   ```

### Dockerfile Configuration
The Dockerfile configures the Neo4j environment with:
- **Neo4j 5.5.0**: The base image, installed with necessary libraries.
- **Graph Data Science Plugin 2.3.1**: Downloaded and placed in the Neo4j plugins directory.
- **Configuration Changes**: Settings in `neo4j.conf` allow unrestricted access to GDS.

## Data Loading and Testing

### Data Loader Script
`data_loader.py` loads and processes NYC taxi trip data:
- **Filter and Save CSV**: The Parquet file is filtered for trips within the Bronx and saved as a CSV in `/var/lib/neo4j/import`.
- **Data Import**: Location nodes and TRIP relationships are created in the Neo4j database.

### Running Data Loading
With the container running, execute the following to load data:
```bash
docker exec -it <container_id> python3 /app/repo/data_loader.py
```

## Graph Algorithms

### PageRank
The PageRank algorithm calculates the importance of each `Location` node based on incoming and outgoing `TRIP` relationships. Configuration includes:
- **Max Iterations**
- **Damping Factor**
- **Weight Property**: Optional weight for relationships (e.g., `distance`).

### Breadth-First Search (BFS)
The BFS algorithm searches the graph from a start node to multiple target nodes, identifying the shortest paths based on distance.

## Running Tests
The `tester.py` script verifies the implementation by:
1. Checking data loading with expected counts of nodes and relationships.
2. Testing **PageRank** and **BFS** methods against expected outputs.

To run the tests, use:
```bash
python3 tester.py
```

## Usage
With Neo4j exposed on port 7474, open a browser and navigate to `http://localhost:7474`. Here, you can interact with the data using Cypher queries, e.g.,:
- **View Schema**: `CALL db.schema.visualization();`
- **View Sample Data**: `MATCH (n) RETURN n LIMIT 25;`

## Troubleshooting
- **SSH Errors during Docker Build**: Verify SSH keys are correctly added to GitHub and accessible by Docker.
- **Database Connection Issues**: Ensure the Neo4j container is running and ports 7474 and 7687 are exposed.
- **Syntax Errors in Cypher Queries**: Confirm Cypher syntax compatibility with Neo4j 5.5.0.