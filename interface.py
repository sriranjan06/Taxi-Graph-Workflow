from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()

    def check_and_drop_graph(self, graph_name):
        with self._driver.session() as session:
            check_query = """
                CALL gds.graph.exists($graph_name) YIELD exists
                RETURN exists
            """
            exists = session.run(check_query, graph_name=graph_name).single()["exists"]

            if exists:
                print(f"Graph '{graph_name}' exists. Dropping it...")
                drop_query = "CALL gds.graph.drop($graph_name) YIELD graphName"
                session.run(drop_query, graph_name=graph_name)
                print(f"Graph '{graph_name}' dropped successfully.")
            else:
                print(f"Graph '{graph_name}' does not exist, proceeding with graph creation.")

    def create_graph_projection(self, graph_name):
        with self._driver.session() as session:
            projection_query = """
                CALL gds.graph.project(
                    $graph_name,
                    {
                        Location: {
                            properties: ['name']  /* Ensures 'name' is properly projected */
                        }
                    },
                    {
                        TRIP: {
                            type: 'TRIP',
                            orientation: 'NATURAL',
                            properties: {
                                distance: {
                                    property: 'distance',
                                    defaultValue: 1.0
                                }
                            }
                        }
                    }
                )
                YIELD graphName, nodeCount, relationshipCount
            """
            result = session.run(projection_query, graph_name=graph_name).single()
            if result:
                print(f"Graph '{result['graphName']}' created with {result['nodeCount']} nodes and {result['relationshipCount']} relationships.")
            else:
                print("Graph projection failed.")

    def initialize_graph(self, graph_name):
        """
        Ensure the graph is set up by dropping and recreating it.
        """
        self.check_and_drop_graph(graph_name)
        self.create_graph_projection(graph_name)

    def get_node_id(self, node_name):
        """
        Retrieve the node ID for a node with the given name.
        """
        with self._driver.session() as session:
            node_id_query = """
                MATCH (n:Location {name: $node_name})
                RETURN id(n) AS node_id
            """
            result = session.run(node_id_query, node_name=node_name).single()
            return result["node_id"] if result else None

    def pagerank(self, max_iterations=20, weight_property="distance"):
        """
        Calculate PageRank scores and return nodes with the highest and lowest scores.
        """
        graph_name = "bfs_graph"  # Default graph name

        # Initialize the graph to ensure the projection is up to date
        self.initialize_graph(graph_name)

        with self._driver.session() as session:
            pagerank_query = f"""
                CALL gds.pageRank.stream('{graph_name}', {{
                    maxIterations: $max_iterations,
                    dampingFactor: 0.85,
                    relationshipWeightProperty: $weight_property
                }})
                YIELD nodeId, score
                RETURN gds.util.nodeProperty('{graph_name}', nodeId, 'name', 'Location') AS name, score
                ORDER BY score DESC
            """
            results = session.run(
                pagerank_query,
                max_iterations=max_iterations,
                weight_property=weight_property
            ).data()

            # Debugging: Print the results to understand its structure
            print("PageRank Results:", results)

            # Ensure results have the expected structure before accessing
            if not results:
                print("No PageRank results found.")
                return []

            # Return results in a list format expected by tester.py
            return [results[0], results[-1]]  # Highest and lowest PageRank nodes


    def bfs(self, start_node, target_nodes):
        """
        Perform a Breadth-First Search (BFS) using the GDS library.
        """
        graph_name = "bfs_graph"  # Default graph name

        # Initialize the graph to ensure the projection is up to date
        self.initialize_graph(graph_name)

        # Ensure target_nodes is a list, even if a single integer is passed
        if isinstance(target_nodes, int):
            target_nodes = [target_nodes]

        start_node_id = self.get_node_id(start_node)
        target_node_ids = [self.get_node_id(node) for node in target_nodes if self.get_node_id(node)]

        if start_node_id is None:
            print(f"Start node '{start_node}' not found.")
            return []

        with self._driver.session() as session:
            bfs_query = f"""
                UNWIND $target_node_ids AS target
                CALL gds.shortestPath.dijkstra.stream('{graph_name}', {{
                    sourceNode: $start_node_id,
                    targetNode: target,
                    relationshipWeightProperty: 'distance'
                }})
                YIELD nodeIds, totalCost
                RETURN [nodeId IN nodeIds | {{
                            name: gds.util.nodeProperty('{graph_name}', nodeId, 'name', 'Location'),
                            id: nodeId
                        }}] AS path_nodes,
                    totalCost AS total_distance
            """

            result = session.run(
                bfs_query,
                start_node_id=start_node_id,
                target_node_ids=target_node_ids
            )

            paths = []
            for record in result:
                path_info = {
                    "path": record["path_nodes"],
                    "total_distance": record["total_distance"]
                }
                paths.append(path_info)

            return paths



