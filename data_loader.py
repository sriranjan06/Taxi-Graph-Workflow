import pyarrow.parquet as pq
import pandas as pd
from neo4j import GraphDatabase
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DataLoader:
    def __init__(self, uri, user, password):
        """
        Initialize connection to Neo4j database.
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self.driver.verify_connectivity()
        logging.info("Connected to Neo4j database.")

    def close(self):
        """
        Close the Neo4j database connection.
        """
        self.driver.close()
        logging.info("Neo4j connection closed.")

    def load_transform_file(self, file_path):
        """
        Load and filter the Parquet file, then save it as a CSV.
        """
        # Read the Parquet file and filter relevant columns
        trips = pq.read_table(file_path).to_pandas()
        trips = trips[['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID', 'trip_distance', 'fare_amount']]
        
        # Filter for Bronx trips and valid trip data
        bronx = [3, 18, 20, 31, 32, 46, 47, 51, 58, 59, 60, 69, 78, 81, 94, 119, 126, 136, 147, 159, 167, 168, 169, 174, 182, 183, 184, 185, 199, 200, 208, 212, 213, 220, 235, 240, 241, 242, 247, 248, 250, 254, 259]
        trips = trips[trips['PULocationID'].isin(bronx) & trips['DOLocationID'].isin(bronx)]
        trips = trips[trips['trip_distance'] > 0.1]
        trips = trips[trips['fare_amount'] > 2.5]

        # Convert datetime columns to a format compatible with Neo4j
        trips['tpep_pickup_datetime'] = pd.to_datetime(trips['tpep_pickup_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')
        trips['tpep_dropoff_datetime'] = pd.to_datetime(trips['tpep_dropoff_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')

        # Save the filtered data as a CSV
        save_loc = "/var/lib/neo4j/import/yellow_tripdata_2022-03.csv"
        trips.to_csv(save_loc, index=False)
        logging.info(f"CSV file saved at {save_loc}")

    def load_data_to_neo4j(self, csv_file_path):
        """
        Load data from CSV into Neo4j as nodes and relationships.
        """
        logging.info("Starting data load into Neo4j.")
        with self.driver.session() as session:
            # Create Location nodes
            logging.info("Creating Location nodes...")
            session.run("""
                CALL {
                    LOAD CSV WITH HEADERS FROM 'file:///yellow_tripdata_2022-03.csv' AS row
                    MERGE (p:Location {name: toInteger(row.PULocationID)})
                    MERGE (d:Location {name: toInteger(row.DOLocationID)})
                } IN TRANSACTIONS;
            """)
            logging.info("Location nodes created.")

            # Create TRIP relationships
            logging.info("Creating TRIP relationships...")
            session.run("""
                CALL {
                    LOAD CSV WITH HEADERS FROM 'file:///yellow_tripdata_2022-03.csv' AS row
                    MATCH (p:Location {name: toInteger(row.PULocationID)}),
                          (d:Location {name: toInteger(row.DOLocationID)})
                    CREATE (p)-[:TRIP {
                        distance: toFloat(row.trip_distance),
                        fare: toFloat(row.fare_amount),
                        pickup_dt: datetime(row.tpep_pickup_datetime),
                        dropoff_dt: datetime(row.tpep_dropoff_datetime)
                    }]->(d)
                } IN TRANSACTIONS;
            """)
            logging.info("TRIP relationships created.")

def main():
    attempts = 10
    attempt = 0
    while attempt < attempts:
        try:
            # Initialize DataLoader and load data
            data_loader = DataLoader("neo4j://localhost:7687", "neo4j", "project1phase1")
            data_loader.load_transform_file("/app/data/yellow_tripdata_2022-03.parquet")
            data_loader.load_data_to_neo4j("/var/lib/neo4j/import/yellow_tripdata_2022-03.csv")
            data_loader.close()
            attempt = attempts
        except Exception as e:
            logging.error(f"(Attempt {attempt+1}/{attempts}) Error: {e}")
            attempt += 1
            time.sleep(10)

if __name__ == "__main__":
    main()
