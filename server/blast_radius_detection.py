import os

import psycopg2

from server.utils.graph_db_helper import Neo4jGraph
from server.utils.config import neo4j_config

codebase_map = f'/.momentum/momentum.db'
neo4j_graph = Neo4jGraph()


def add_codebase_map_path(directory):
    return f"{directory}{codebase_map}"

def find_entry_points(identifiers, directory, project_id):
    all_inbound_nodes = set()

    for identifier in identifiers:
        traversal_result = neo4j_graph.traverse(identifier=identifier,
                                                project_id=project_id, neighbors_fn=neo4j_graph.find_inbound_neighbors)
        for item in traversal_result:
            if isinstance(item, dict):
                all_inbound_nodes.update([frozenset(item.items())])

    entry_points = set()
    for node in all_inbound_nodes:
        node_dict = dict(node)
        traversal_result = neo4j_graph.traverse(identifier=node_dict['id'],
                                                project_id=project_id, neighbors_fn=neo4j_graph.find_inbound_neighbors)
        if len(traversal_result) == 1:
            entry_points.add(node)

    return entry_points


def find_paths(entry_points, project_id):
    # Connect to the endpoints database
    conn_endpoints = psycopg2.connect(os.getenv("POSTGRES_SERVER"))
    endpoints_cursor = conn_endpoints.cursor()

    paths = {}

    for entry_point in entry_points:
        entry_point_dict = dict(entry_point)
        endpoints_cursor.execute("SELECT path FROM endpoints WHERE identifier = %s and project_id = %s",
                                 (entry_point_dict['id'], project_id, ))
        path = endpoints_cursor.fetchone()
        if path:
            paths[entry_point_dict['id']] = path[0]

    conn_endpoints.close()
    return paths


def get_paths_from_identifiers(identifiers, directory, project_id):
    entry_points = find_entry_points(identifiers, directory, project_id)
    paths = find_paths(entry_points, project_id)
    grouped_by_filename = {}
    for entry_point, path in paths.items():
        file, function = entry_point.split(':')
        if file not in grouped_by_filename:
            grouped_by_filename[file] = []
        grouped_by_filename[file].append({"entryPoint": path, "identifier": entry_point})
    return grouped_by_filename

