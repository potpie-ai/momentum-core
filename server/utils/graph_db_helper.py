import json
from neo4j import GraphDatabase
from server.utils.config import neo4j_config

class Neo4jDriverSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GraphDatabase.driver(
                neo4j_config['uri'],
                auth=(neo4j_config['username'], neo4j_config['password'])
            )
        return cls._instance
    
class Neo4jGraph:

    def __init__(self):
        self.driver = Neo4jDriverSingleton.get_instance()

    def close(self):
        # No need to close the driver here, as it's managed by the singleton
        pass

    def upsert_node(self, function_identifier, properties, project_id):
        properties['project_id'] = project_id
        with self.driver.session() as session:
            session.write_transaction(self._upsert_node, function_identifier, project_id, properties)

    def add_edge(self, node1_id, node2_id, relationship_type):
        with self.driver.session() as session:
            session.write_transaction(self._add_edge, node1_id, node2_id, relationship_type)

    def connect_nodes(self, parent_function, called_function_identifier, project_id, relationship_properties):
        with self.driver.session() as session:
            session.write_transaction(self._connect_nodes, parent_function, called_function_identifier,
                                      project_id, relationship_properties)

    def find_outbound_neighbors(self, endpoint_id, project_id, with_bodies=False, outbound=True, inbound=False):
        with self.driver.session() as session:
            return session.read_transaction(self._find_outbound_neighbors, endpoint_id, project_id, with_bodies, outbound, inbound)

    def get_node_by_id(self, node_id, project_id):
        with self.driver.session() as session:
            return session.read_transaction(self._get_node_by_id, node_id, project_id)

    def find_inbound_neighbors(self, with_bodies=False):
        if with_bodies:
            return """
            MATCH (start:Function {id: $identifier, project_id: $project_id})
            OPTIONAL MATCH (neighbor:Function {project_id: $project_id})-[:CALLS]->(start)
            RETURN start, collect({neighbor: neighbor, body: neighbor.body}) AS neighbors
            """
        else:
            return """
            MATCH (start:Function {id: $identifier, project_id: $project_id})
            OPTIONAL MATCH (neighbor:Function {project_id: $project_id})-[:CALLS]->(start)
            RETURN start, collect(neighbor) AS neighbors
            """

    def fetch_first_order_neighbors(self, node_id, project_id):
        with self.driver.session() as session:
            return session.read_transaction(self._fetch_first_order_neighbors, node_id, project_id)

    def traverse(self, identifier, project_id, neighbors_fn):
        neighbors_query = neighbors_fn(with_bodies=False)
        with self.driver.session() as session:
            return session.read_transaction(self._traverse, identifier, project_id, neighbors_query)

    def get_node_file_property(self, identifier, project_id):
        with self.driver.session() as session:
            return session.read_transaction(self._get_node_file_property, identifier, project_id)

    @staticmethod
    def _delete_nodes_by_project_id(tx, project_id):
        try:
            query = """
            MATCH (n {project_id: $project_id})
            DETACH DELETE n
            """
            tx.run(query, project_id=project_id)
        except Exception as e:
            raise RuntimeError(f"Failed to delete nodes with project_id {project_id}: {str(e)}")
    
    def delete_nodes_by_project_id(self, project_id):
        with self.driver.session() as session:
            session.write_transaction(self._delete_nodes_by_project_id, project_id)
            
    @staticmethod
    def _upsert_node(tx, function_identifier,  project_id, properties):
        # Serialize complex properties to strings if needed
        serialized_properties = {
            key: (json.dumps(value) if isinstance(value, (dict, list)) else value)
            for key, value in properties.items()
        }

        query = (
            "MERGE (n:Function {id: $function_identifier, project_id: $project_id}) "
            "SET n += $properties "
            "RETURN n"
        )
        tx.run(query, function_identifier=function_identifier, properties=serialized_properties,
               project_id= project_id)

    @staticmethod
    def _connect_nodes(tx, parent_function, called_function_identifier, project_id, relationship_properties):
        query = (
            "MATCH (a:Function {id: $parent_function, project_id: $project_id}), (b:Function {id: $called_function_identifier, project_id: $project_id}) "
            "MERGE (a)-[r:CALLS]->(b) "
            "SET r += $relationship_properties "
            "RETURN r"
        )
        tx.run(query, parent_function=parent_function, called_function_identifier=called_function_identifier,
               relationship_properties=relationship_properties, project_id= project_id)

    @staticmethod
    def _add_edge(tx, node1_id, node2_id, relationship_type):
        query = (
            "MATCH (a:Function {id: $node1_id, project_id: $project_id}), (b:Function {id: $node2_id, project_id: $project_id}) "
            "MERGE (a)-[r:%s]->(b) "
            "RETURN r" % relationship_type
        )
        tx.run(query, node1_id=node1_id, node2_id=node2_id)

    @staticmethod
    def _find_outbound_neighbors(tx, endpoint_id, project_id, with_bodies, outbound, inbound):
        match_clause = "MATCH (start:Function {id: $endpoint_id, project_id: $project_id})"
        recursive_match = ""

        if outbound and inbound:
            recursive_match = "MATCH (start)-[:CALLS*]-(neighbor:Function {project_id: $project_id})"
        elif outbound:
            recursive_match = "MATCH (start)-[:CALLS*]->(neighbor:Function {project_id: $project_id})"
        elif inbound:
            recursive_match = "MATCH (start)<-[:CALLS*]-(neighbor:Function {project_id: $project_id})"

        if with_bodies:
            return_clause = "RETURN start, collect({neighbor: neighbor, body: neighbor.body}) AS neighbors"
            query = f"""
                {match_clause}
                CALL {{
                    WITH start
                    {recursive_match}
                    RETURN neighbor, neighbor.body AS body
                }}
                {return_clause}
                """
        else:
            return_clause = "RETURN start, collect(neighbor) AS neighbors"
            query = f"""
                {match_clause}
                CALL {{
                    WITH start
                    {recursive_match}
                    RETURN neighbor
                }}
                {return_clause}
                """

        result = tx.run(query, endpoint_id=endpoint_id, project_id=project_id)
        record = result.single()
        if not record:
            return []

        start_node = dict(record["start"])
        neighbors = record["neighbors"]
        combined = [start_node] + neighbors if neighbors else [start_node]
        return combined

    @staticmethod
    def _get_node_by_id(tx, node_id, project_id):
        query = "MATCH (n:Function {id: $node_id, project_id: $project_id}) RETURN n"
        result = tx.run(query, node_id=node_id, project_id=project_id)
        record = result.single()
        if record:
            return dict(record["n"])
        return None

    @staticmethod
    def _find_inbound_neighbors(tx, endpoint_id, project_id, with_bodies):
        query = f"""
        MATCH (start:Function {{id: $endpoint_id, project_id: $project_id}})
        CALL {{
            WITH start
            MATCH (neighbor:Function {{project_id: $project_id}})-[:CALLS*]->(start)
            RETURN neighbor{', neighbor.body AS body' if with_bodies else ''}
        }}
        RETURN start, collect({{neighbor: neighbor{', body: neighbor.body' if with_bodies else ''}}}) AS neighbors
        """
        result = tx.run(query, endpoint_id=endpoint_id, project_id=project_id)
        record = result.single()
        if not record:
            return []

        start_node = dict(record["start"])
        neighbors = record["neighbors"]
        combined = [start_node] + neighbors if neighbors else [start_node]
        return combined

    @staticmethod
    def _fetch_first_order_neighbors(tx, node_id, project_id):
        query = """
            MATCH (n:Function {id: $node_id, project_id: $project_id})-[:CALLS]->(neighbor:Function)
            RETURN neighbor
            """
        print(query)
        result = tx.run(query, node_id=node_id, project_id=project_id)
        return [dict(record["neighbor"]) for record in result]


    @staticmethod
    def _get_node_file_property(tx, identifier, project_id):
        query = """
        MATCH (n:Function {id: $identifier, project_id: $project_id})
        RETURN n.file AS file
        """
        result = tx.run(query, identifier=identifier, project_id=project_id)
        record = result.single()
        if record:
            return record["file"]
        return None

    @staticmethod
    def _traverse(tx, identifier, project_id, neighbors_query):
        query = f"""
        {neighbors_query}
        """
        result = tx.run(query, identifier=identifier, project_id=project_id)
        record = result.single()
        if not record:
            return []

        start_node = dict(record["start"])
        neighbors = [dict(neighbor) for neighbor in record["neighbors"]]
        combined = [start_node] + neighbors if neighbors else [start_node]
        return combined
 

    @staticmethod
    def _find_neighbors(tx, identifier, project_id, with_bodies, outbound, inbound):
        match_clause = f"MATCH (start:Function {{id: $identifier, project_id: $project_id}})"
        recursive_match = ""

        if outbound and inbound:
            recursive_match = "MATCH (start)-[:CALLS*]-(neighbor:Function {project_id: $project_id})"
        elif outbound:
            recursive_match = "MATCH (start)-[:CALLS*]->(neighbor:Function {project_id: $project_id})"
        elif inbound:
            recursive_match = "MATCH (start)<-[:CALLS*]-(neighbor:Function {project_id: $project_id})"

        if with_bodies:
            return_clause = "RETURN start, collect({neighbor: neighbor, body: neighbor.body}) AS neighbors"
        else:
            return_clause = "RETURN start, collect(neighbor) AS neighbors"

        query = f"""
            {match_clause}
            {recursive_match}
            {return_clause}
        """
        result = tx.run(query, identifier=identifier, project_id=project_id)
        record = result.single()
        if not record:
            return []

        start_node = dict(record["start"])
        neighbors = [dict(neighbor) for neighbor in record["neighbors"]]
        combined = [start_node] + neighbors if neighbors else [start_node]
        return combined

    def atomic_transaction(self, operations):
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                try:
                    for operation in operations:
                        operation(tx)
                    tx.commit()
                except Exception as e:
                    tx.rollback()
                    raise e