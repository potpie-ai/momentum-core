from server.utils.graph_db_helper import Neo4jGraph
from server.db.session import SessionManager
from server.schemas import Endpoint

neo4j_graph = Neo4jGraph()


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
    paths = {}
    with SessionManager() as db:
        for entry_point in entry_points:
            entry_point_dict = dict(entry_point)
            endpoint = db.query(Endpoint.path).filter(
                Endpoint.identifier == entry_point_dict['id'],
                Endpoint.project_id == project_id
            ).first()
            if endpoint:
                paths[entry_point_dict['id']] = endpoint.path
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

