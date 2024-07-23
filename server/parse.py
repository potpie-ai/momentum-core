import ast
import io
import json
import logging
import os
import re

import psycopg2
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.exc import DetachedInstanceError
from tree_sitter_languages import get_language, get_parser
from tree_sitter import Node

from server.endpoint_detection import EndpointManager
from server.schemas import Project
from server.utils.github_helper import GithubService
from server.utils.graph_db_helper import Neo4jGraph
from server.utils.parse_helper import delete_folder

parser = get_parser("python")
codebase_map = f"/.momentum/momentum.db"
neo4j_graph = Neo4jGraph()

logger = logging.getLogger(__name__)

def add_codebase_map_path(directory):
    return f"{directory}{codebase_map}"


def add_node_safe(
    directory,
    file_path,
    function_name,
    node,
    parameters,
    start,
    end,
    project_id,
    response=None,
):
    function_identifier = (
        file_path.replace(directory, "") + ":" + function_name
    )
    try:
        neo4j_graph.upsert_node(
            function_identifier,
            {
                "type": "function",
                "file": file_path,
                "parameters": parameters,
                "start": start,
                "end": end,
                "response": response
            },
            project_id,
        )
    except psycopg2.IntegrityError:
        logging.error(f"project_id: {project_id}, Node with identifier {function_identifier} already exists. Skipping insert.")
    return function_identifier 


def add_class_node_safe(directory, file_path, class_name, start, end, project_id):
    function_identifier = file_path.replace(directory, '') + ":" + class_name
    try:
        neo4j_graph.upsert_node(
            function_identifier,
            {
                "type": "class",
                "file": file_path,
                "start": start,
                "class_name": class_name,
                "end": end
            },
            project_id,
        )
    except psycopg2.IntegrityError:
        logging.warn(f"project_id: {project_id}, Node with identifier {function_identifier} already exists. Skipping insert.")
    return function_identifier


def get_node_text(node, source_code):
    start_byte = node.start_byte
    end_byte = node.end_byte
    return source_code[start_byte:end_byte]


def is_pydantic_base_model(node, pydantic_class_list):
    return node.type == "identifier" and (
        node.text.decode("utf8") == "BaseModel"
        or node.text.decode("utf8") in pydantic_class_list
    )


def find_pydantic_class(node, pydantic_class_list, file_path):
    # Recursive function to walk the AST and find Pydantic models.
    if node.type == "class_definition":
        for child in node.children:
            if any(
                is_pydantic_base_model(n, pydantic_class_list)
                for n in child.children
            ):
                pydantic_class_list[
                    f"{node.children[1].text.decode('utf8')}"
                ] = (file_path, node.text.decode("utf8"))

    for child in node.children:
        pydantic_class_list = find_pydantic_class(
            child, pydantic_class_list, file_path
        )
    return pydantic_class_list


def extract_path_after_project(full_path):
    pattern = r'/projects/[^/]+(/.*)'
    match = re.search(pattern, full_path)
    if match:
        return match.group(1)
    else:
        return None

def extract_parent_class(value):
    # Split the string to find the parent class name
    parts = value.split("(")
    # Extract the parent class name
    parent_class = parts[1].split(")")[0].strip()
    return parent_class


# Function to recursively append parent class definitions
def append_parent_class(key, current_dict, original_dict, project_id, iteration=0):
    # Base cases
    if iteration >= 3 or key == "BaseModel":
        return current_dict[key][1]

    # Extract the parent class name
    parent_class = extract_parent_class(current_dict[key][1])

    # If parent class is BaseModel, return the current class definition
    if parent_class == "BaseModel":
        return current_dict[key][1]
    else:
        # Append parent class definition to the current class definition
        parent_classes = [cls.strip() for cls in parent_class.split(",")]
        for cls in parent_classes:
            parent_class_id = f"{extract_path_after_project(current_dict[key][0])}:{key}"
            base_class_id = f"{extract_path_after_project(current_dict[cls][0])}:{cls}"

            neo4j_graph.add_extends_relationship(base_class_id, parent_class_id, project_id)
            append_parent_class(
                cls.strip(), original_dict, original_dict, project_id, iteration + 1
            )


def map_user_defined_functions(directory, source_code, file_path, user_id, project_id):
    tree = parser.parse(bytes(source_code, "utf8"))
    root_node = tree.root_node

    user_defined_functions = {}
    class_definition = []
    class_nodes = []
    class_instances = {}
    file_imports = (
        []
    )  # Assuming this is defined somewhere above your provided code
    router_metadata = []
    for node in root_node.children:

        if (
            node.type == "import_from_statement"
            or node.type == "import_statement"
        ):
            base_module_parts = [
                child.text.decode("utf8")
                for child in node.children
                if child.type == "dotted_name"
                or child.type == "relative_import"
            ]
            counter = 1

            len_parts = len(base_module_parts)
            if len_parts >= 2:
                while counter < len_parts:
                    base_parts = []
                    base_parts.append(base_module_parts[0])
                    if not len_parts == counter:
                        base_parts.append(base_module_parts[counter])

                    base_module = ".".join(base_parts) if base_parts else ""
                    counter += 1
                    if base_module:
                        file_imports.append(
                            {"module": base_module, "alias": None}
                        )
                aliased_imports = [
                    child
                    for child in node.children
                    if child.type == "aliased_import"
                ]
                base_module = base_module_parts[0]
                for aliased_import in aliased_imports:

                    aliased_parts = aliased_import.text.decode("utf8").split(
                        " as "
                    )
                    if len(aliased_parts) == 2:
                        imported_object, alias = aliased_parts
                        imported_module = (
                            f"{base_module}.{imported_object}"
                            if base_module
                            else imported_object
                        )

                        file_imports.append(
                            {"module": imported_module, "alias": alias}
                        )
                    else:
                        imported_module = (
                            f"{base_module}.{aliased_parts[0]}"
                            if base_module
                            else aliased_parts[0]
                        )

                        file_imports.append(
                            {"module": imported_module, "alias": None}
                        )
            else:
                base_module = (
                    ".".join(base_module_parts) if base_module_parts else ""
                )
                aliased_imports = [
                    child
                    for child in node.children
                    if child.type == "aliased_import"
                ]
                for aliased_import in aliased_imports:
                    aliased_parts = aliased_import.text.decode("utf8").split(
                        " as "
                    )
                    if len(aliased_parts) == 2:
                        imported_object, alias = aliased_parts
                        imported_module = (
                            f"{base_module}.{imported_object}"
                            if base_module
                            else imported_object
                        )
                        file_imports.append(
                            {"module": imported_module, "alias": alias}
                        )
                    else:
                        imported_module = (
                            f"{base_module}.{aliased_parts[0]}"
                            if base_module
                            else aliased_parts[0]
                        )
                        file_imports.append(
                            {"module": imported_module, "alias": None}
                        )
                if not aliased_imports:
                    file_imports.append({"module": base_module, "alias": None})
        elif node.type == "expression_statement":
            for child in node.children:
                if child.type == "call":

                    extract_argument = False
                    for grandchild in child.children:
                        if grandchild.type == "attribute":
                            if "include_router" in grandchild.text.decode(
                                "utf8"
                            ):
                                extract_argument = True
                            else:
                                continue
                        if (
                            grandchild.type == "argument_list"
                            and extract_argument
                        ):

                            arguments = [
                                x.text.decode("utf8")
                                for x in grandchild.children
                                if x.type not in ["(", ")", ","]
                            ]

                            router, prefix = None, None
                            depends_function_names = []

                            for arg in arguments:
                                if arg.startswith("router") and "=" in arg:
                                    router = arg.split("=", 1)[1]
                                elif arg.startswith("prefix") and "=" in arg:
                                    prefix = arg.split("=", 1)[1]

                            if router is None:
                                router = arguments[0]
                            if prefix is None and len(arguments) >= 3:
                                prefix = arguments[2].strip('"')

                            depends_call = "Depends" in grandchild.text.decode(
                                "utf8"
                            )

                            if depends_call:
                                depends_text = grandchild.text.decode("utf8")
                                start_index = 0
                                while True:
                                    start_index = depends_text.find(
                                        "Depends(", start_index
                                    )
                                    if start_index == -1:
                                        break
                                    start_index += len("Depends(")
                                    end_index = depends_text.find(
                                        ")", start_index
                                    )
                                    depends_function_names.append(
                                        depends_text[start_index:end_index]
                                    )
                                    start_index = end_index

                            router_metadata.append({
                                "router": router,
                                "prefix": prefix,
                                "depends": depends_function_names,
                            })

                if child.type == "assignment":
                    instance_name = child.children[0].text.decode(
                        "utf8"
                    )  # Assuming the instance name is always the first child
                    assigned_value = child.children[-1]
                    if assigned_value.type == "call":
                        called_function = extract_called_function_name(
                            assigned_value
                        )
                        class_instances[instance_name] = called_function
        elif node.type == "class_definition":
            class_name = node.children[1].text.decode(
                "utf8"
            )  # Assuming the class name is always the second child
            class_context = class_name  # Set the current class context
            class_definition.append(class_name)
            add_class_node_safe(
                directory,
                file_path,
                class_name,
                node.start_point[0],
                node.end_point[0],
                project_id,
            )
            class_nodes.append(node)
            for class_child in node.children:
                if class_child.type == "block":
                    for child in class_child.children:
                        if child.type in [
                            "function_definition",
                            "decorated_definition",
                        ]:
                            (
                                function_name,
                                params,
                                start,
                                end,
                                response,
                            ) = extract_function_metadata(
                                child, [], class_context
                            )
                            if function_name:
                                add_node_safe(
                                    directory,
                                    file_path,
                                    function_name,
                                    node,
                                    params,
                                    start,
                                    end,
                                    project_id,
                                    response,
                                )
                                function_identifier = (
                                    file_path.replace(directory, "")
                                    + ":"
                                    + function_name
                                )
                                user_defined_functions[function_identifier] = (
                                    child
                                )

        elif (
            node.type == "function_definition"
            or node.type == "decorated_definition"
        ):
            function_name, params, start, end, response = (
                extract_function_metadata(node, [], None)
            )
            if function_name:
                add_node_safe(
                    directory,
                    file_path,
                    function_name,
                    node,
                    params,
                    start,
                    end,
                    project_id,
                    response,
                )
                function_identifier = (
                    file_path.replace(directory, "") + ":" + function_name
                )
                user_defined_functions[function_identifier] = node

    return (
        user_defined_functions,
        file_imports,
        class_instances,
        class_definition,
        class_nodes,
        router_metadata,
    )


# Process Function Calls and Update Edges
def process_function_calls(
    directory,
    user_defined_functions,
    source_code,
    file_path,
    file_index,
    project_id,
):
    for function_identifier, node in file_index[file_path][
        "functions"
    ].items():
        function_ref = function_identifier.split(":")[1]
        class_context = (
            function_ref.split(".")[0] if "." in function_ref else None
        )
        traverse_node(
            directory,
            node,
            function_identifier,
            user_defined_functions,
            file_path,
            file_index,
            project_id,
            class_context,
        )


def traverse_node(
    directory,
    node,
    parent_function,
    user_defined_functions,
    file_path,
    file_index,
    project_id,
    class_context=None,
):
    depends_call = (
        node.type == "default_parameter"
        and "Depends" in node.text.decode("utf8")
    )

    if depends_call:
        depends_text = node.text.decode("utf8")
        depends_function_names = []
        start_index = 0
        while True:
            start_index = depends_text.find("Depends(", start_index)
            if start_index == -1:
                break
            start_index += len("Depends(")
            end_index = depends_text.find(")", start_index)
            depends_function_names.append(depends_text[start_index:end_index])
            start_index = end_index
        for functions in depends_function_names:
            connect_nodes(
                parent_function,
                functions,
                user_defined_functions,
                directory,
                file_path,
                file_index,
                project_id,
            )

    if node.type == "call":
        called_function = extract_called_function_name(node, class_context)
        if called_function:
            # Logic to handle method calls within the class context
            connect_nodes(
                parent_function,
                called_function,
                user_defined_functions,
                directory,
                file_path,
                file_index,
                project_id,
            )

    for child in node.children:
        traverse_node(
            directory,
            child,
            parent_function,
            user_defined_functions,
            file_path,
            file_index,
            project_id,
            class_context,
        )


def connect_nodes(
    parent_function: str,
    called_function: str,
    user_defined_functions: dict,
    directory: str,
    file_path: str,
    file_index: dict,
    project_id,
):
    called_function_identifier = (
        f"{file_path.replace(directory, '')}:{called_function}"
    )
    if called_function_identifier in user_defined_functions:
        neo4j_graph.connect_nodes(
            parent_function,
            called_function_identifier,
            project_id,
            {"action": "calls"},
        )
    else:
        file_path, called_function = resolve_called_function_name(
            called_function, file_path, file_index, directory
        )
        if called_function:
            called_function_identifier = (
                f"{file_path.replace(directory, '')}:{called_function}"
            )
            if called_function_identifier in user_defined_functions:
                neo4j_graph.connect_nodes(
                    parent_function,
                    called_function_identifier,
                    project_id,
                    {"action": "calls"},
                )


def find_py_files_with_substring(dir_path, substring):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            path = os.path.join(root, file)
            if (
                substring in path
                and file.endswith(".py")
                and not file.startswith("test")
            ):
                yield os.path.join(root, file)


def resolve_called_function_name(name, file_path, file_index, directory):
    # handle DEPENDS later
    if len(name.split(".")) >= 2:
        instance = name.split(".")[0]

        function = ".".join(name.split(".")[1:])
    elif "." not in name:
        function = name
        instance = name
    else:
        return file_path, None
    if instance in file_index[file_path]["class_instances"].keys():
        class_context = file_index[file_path]["class_instances"][instance]
        if class_context in file_index[file_path]["class_definition"]:
            return file_path, class_context + "." + function
        module_value = None
        for import_entry in file_index[file_path]["imports"]:
            if import_entry.get("alias") == class_context:
                module_value = import_entry.get("module")
                break
            elif class_context in import_entry.get("module"):
                module_value = import_entry.get("module")
                break
        if module_value:
            if module_value.startswith("."):
                num_up_dirs = len(module_value) - len(
                    module_value.lstrip(".")
                )  # Count the number of leading dots to determine relative depth
                file_path_parts = file_path.split("/")[
                    :-1
                ]  # Remove the filename
                # Use the last num_up_dirs elements from file_path_parts if num_up_dirs is not more than the length of file_path_parts
                base_path_parts = (
                    file_path_parts[-num_up_dirs:]
                    if num_up_dirs <= len(file_path_parts)
                    else []
                )
                module_parts = module_value.lstrip(".").split(
                    "."
                )  # Remove leading dots and split
                potential_module = "/".join(
                    base_path_parts + module_parts[:-1]
                )  # Combine the paths
            else:
                module_parts = module_value.split(".")
                potential_module = (
                    "/".join(module_parts[:-1])
                    if len(module_parts) > 1
                    else ""
                )
            potential_class_or_instance = module_parts[-1]

            candidate_files = list(
                find_py_files_with_substring(directory, potential_module)
            )
            for candidate_file in candidate_files:
                candidate_path = os.path.join(directory, candidate_file)
                if candidate_path in file_index:
                    # Check if it's a class definition
                    if (
                        potential_class_or_instance
                        in file_index[candidate_path]["class_definition"]
                    ):
                        return (
                            candidate_path,
                            potential_class_or_instance + "." + function,
                        )
                    # Check if it's a class instance
                    elif (
                        potential_class_or_instance
                        in file_index[candidate_path]["class_instances"].keys()
                    ):
                        return (
                            candidate_path,
                            file_index[candidate_path]["class_instances"][
                                potential_class_or_instance
                            ]
                            + "."
                            + function,
                        )
        # TODO DEDUP   # If no class or instance match, return with the function appended
    module_value = None
    for import_entry in file_index[file_path]["imports"]:
        if import_entry.get("alias") == instance:
            module_value = import_entry.get("module")
            break
        elif instance in import_entry.get("module"):
            module_value = import_entry.get("module")
            break
    if module_value:
        if module_value.startswith("."):
            num_up_dirs = len(module_value) - len(
                module_value.lstrip(".")
            )  # Count the number of leading dots to determine relative depth
            file_path_parts = file_path.split("/")[:-1]  # Remove the filename
            # Use the last num_up_dirs elements from file_path_parts if num_up_dirs is not more than the length of file_path_parts
            base_path_parts = (
                file_path_parts[-num_up_dirs:]
                if num_up_dirs <= len(file_path_parts)
                else []
            )
            module_parts = module_value.lstrip(".").split(
                "."
            )  # Remove leading dots and split
            potential_module = "/".join(
                base_path_parts + module_parts[:-1]
            )  # Combine the paths
        else:
            module_parts = module_value.split(".")
            potential_module = (
                "/".join(module_parts[:-1]) if len(module_parts) > 1 else ""
            )
        potential_class_or_instance = module_parts[-1]

        candidate_files = list(
            find_py_files_with_substring(directory, potential_module)
        )
        for candidate_file in candidate_files:
            candidate_path = os.path.join(directory, candidate_file)
            if candidate_path in file_index:
                # Check if it's a class definition
                if (
                    potential_class_or_instance
                    in file_index[candidate_path]["class_definition"]
                ):
                    return (
                        candidate_path,
                        potential_class_or_instance + "." + function,
                    )
                # Check if it's a class instance
                elif (
                    potential_class_or_instance
                    in file_index[candidate_path]["class_instances"].keys()
                ):
                    return (
                        candidate_path,
                        file_index[candidate_path]["class_instances"][
                            potential_class_or_instance
                        ]
                        + "."
                        + function,
                    )
                elif potential_class_or_instance in [
                    key.split(":")[-1]
                    for key in file_index[candidate_path]["functions"].keys()
                ]:
                    return candidate_path, potential_class_or_instance
        # If no class or instance match, return with the function appended
    return file_path, None


def extract_called_function_name(call_node, class_context=None):
    # Extract the function name from the call expression
    for child in call_node.children:
        if child.type == "identifier":

            return child.text.decode("utf8")
        if child.type == "attribute":
            name = None
            for subchild in child.children:
                if subchild.type == "call":
                    name = subchild.text.decode("utf8").split("(")[0]
                if subchild.type == "identifier":
                    if name:
                        name = name + "." + subchild.text.decode("utf8")
                    else:
                        name = subchild.text.decode("utf8")
            if class_context:
                return name.replace("self.", class_context + ".")
            return name

    return None


def extract_function_metadata(node, parameters=[], class_context=None):
    # This function now accepts an additional parameter `class_context` which is the name of the class if the function is a method.
    function_name = None
    response = ""

    if node.type == "decorated_definition":
        # Find the actual function_definition node
        for child in node.children:
            if child.type == "function_definition":
                function_name, params, start, end, response = (
                    extract_function_metadata(child, parameters, class_context)
                )

    for child in node.children:
        if child.type == "identifier" and function_name is None:
            function_name = child.text.decode("utf8")
            if class_context:
                # Prefix the function name with the class name for methods
                function_name = f"{class_context}.{function_name}"
        elif child.type == "parameters":

            for param in child.children:
                if param.type == "identifier":
                    parameters.append(
                        {"identifier": param.text.decode("utf8"), "type": None}
                    )
                elif param.type == "typed_parameter":
                    param_identifier = None
                    param_type = None
                    for subchild in param.children:
                        if subchild.type == "identifier":
                            param_identifier = subchild.text.decode("utf8")
                        elif subchild.type == "type":
                            param_type = subchild.text.decode("utf8")
                    parameters.append(
                        {"identifier": param_identifier, "type": param_type}
                    )
        elif child.type == "type":
            response = child.text.decode("utf8")

    start, _ = node.start_point
    end, _ = node.end_point

    return function_name, parameters, start, end, response


def parse_config(content: str) -> dict:
    try:
        # Use StringIO to create a file-like object from the string
        config_io = io.StringIO(content)
        return toml.load(config_io)
    except toml.TomlDecodeError as e:
        raise ValueError(f"Invalid TOML: {str(e)}")

def print_tree(node, depth=0):
    print(f"{'  ' * depth}{node.type}: {node.text.decode('utf-8')}")
    for child in node.children:
        print_tree(child, depth + 1)


# todo: optimise for single run
async def analyze_directory(directory, user_id, project_id):
    user_defined_functions = {}
    file_index = {}
    all_class_definitions = []
    pydantic_classes = {}
    for subdir, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and not file.startswith("test"):

                file_path = os.path.join(subdir, file)
                with open(file_path, "r") as source_file:
                    try:
                        source_code = source_file.read()
                    except Exception as e:
                        raise e
                    (
                        defined_functions,
                        file_imports,
                        class_instances,
                        class_definition,
                        class_nodes,
                        router_prefixes,
                    ) = map_user_defined_functions(
                        directory, source_code, file_path, user_id, project_id
                    )
                    user_defined_functions.update(defined_functions)
                    file_index[file_path] = {
                        "imports": file_imports,
                        "class_instances": class_instances,
                        "class_definition": class_definition,
                        "functions": defined_functions,
                        "router_prefixes": router_prefixes,
                    }
                    for class_def in class_nodes:
                        all_class_definitions.append((file_path, class_def))

    pydantic_class_list = {}
    depth = 4
    while depth >= 0:
        for file_path, cl_def in all_class_definitions:
            if cl_def.text.decode("utf8") not in pydantic_class_list:
                pydantic_classes = find_pydantic_class(
                    cl_def, pydantic_class_list, file_path
                )
        depth -= 1

    for key, value in pydantic_classes.items():
        append_parent_class(
            key, pydantic_classes, pydantic_classes, project_id
        )
    router_metadata_file_mapping = {}
    for subdir, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and not file.startswith("test"):
                file_path = os.path.join(subdir, file)
                with open(file_path, "r") as source_file:
                    source_code = source_file.read()
                    process_function_calls(
                        directory,
                        user_defined_functions,
                        source_code,
                        file_path,
                        file_index,
                        project_id,
                    )
                for router_prefix in file_index[file_path]["router_prefixes"]:
                    if not router_prefix == []:
                        router = router_prefix["router"]
                        prefix = router_prefix["prefix"]
                        depends = router_prefix["depends"]
                        router_name = resolve_called_function_name(
                            router, file_path, file_index, directory
                        )
                        if router_name:
                            router_file = router_name[0].replace(directory, "")
                            router_dependencies = {}
                            if router_name[0] not in router_dependencies:
                                router_dependencies[router_name[0]] = []
                            if not depends == []:
                                for dependency in depends:
                                    called_function_identifier = (
                                        f"{file_path.replace(directory, '')}:{dependency}"
                                    )
                                    if (
                                        called_function_identifier
                                        in user_defined_functions
                                    ):
                                        router_dependencies[
                                            router_name[0]
                                        ].append(called_function_identifier)
                                    else:
                                        path, name = (
                                            resolve_called_function_name(
                                                dependency,
                                                file_path,
                                                file_index,
                                                directory,
                                            )
                                        )
                                        function_identifier = (
                                            f"{path.replace(directory, '')}:{name}"
                                        )
                                        if name:
                                            router_dependencies[
                                                router_name[0]
                                            ].append(function_identifier)
                            dep = (
                                router_dependencies[router_name[0]]
                                if router_name[0] in router_dependencies
                                else []
                            )
                            router_metadata_file_mapping[router_file] = {
                                "prefix": prefix,
                                "depends": dep,
                            }

    (
        await EndpointManager(
             directory, router_metadata_file_mapping, file_index
        ).analyse_endpoints(project_id, user_id)
    )
    delete_folder(directory)


def get_code_flow_by_id(endpoint_id, project_id):
    dir = os.getcwd()
    code = ""
    nodes_pro = neo4j_graph.find_outbound_neighbors(
        endpoint_id, project_id, with_bodies=True
    )
    for node in nodes_pro:
        if "file" in json.loads(node[2]):
            code += (
                    f"File: {json.loads(node[2])['file'].replace(dir, '')}\n"
                )
            code += GithubService.fetch_method_from_repo(node[2]) + "\n"
    return code


def traverse_and_build_structure(
    node_id, directory, structure, project_id, depth=1
):
    node_details = neo4j_graph.get_node_by_id(node_id, project_id)
    if node_details:
        parameters = node_details["parameters"] if "parameters" in node_details else []
        response = node_details["response"] if "response" in node_details else []
        structure.append({
            "function": node_id,
            "params": parameters,
            "response_object": response,
            "children": [],
        })
        if depth > 0:
            first_order_neighbors = neo4j_graph.fetch_first_order_neighbors(
                node_id, project_id
            )
            for neighbor in first_order_neighbors:
                if neighbor not in [
                    child["function"] for child in structure[-1]["children"]
                ]:
                    traverse_and_build_structure(
                        neighbor["id"],
                        directory,
                        structure[-1]["children"],
                        project_id,
                        depth - 1,
                    )
    return structure


def get_graphical_flow_structure(endpoint_id, directory, project_id):
    flow_structure = traverse_and_build_structure(
        endpoint_id, directory, [], project_id, depth=4
    )  # Adjust depth as needed to fetch further connections
    return flow_structure


def get_flow(endpoint_id, project_id):
    flow = ()
    nodes_pro = neo4j_graph.find_outbound_neighbors(
        endpoint_id=endpoint_id, project_id=project_id, with_bodies=True
    )
    for node in nodes_pro:
        if "id" in node:
            flow += (node["id"],)
        elif "neighbor" in node:
            flow += (node["neighbor"]["id"],)
    return flow


def get_code_for_function(function_identifier):
    node = neo4j_graph.get_node_by_id(function_identifier, project_id="")
    return GithubService.fetch_method_from_repo(node)


def get_node(function_identifier, project_details):
    return neo4j_graph.get_node_by_id(function_identifier, project_details["id"])

def get_node_by_id(node_id, project_id):
    return neo4j_graph.get_node_by_id(node_id, project_id)


def model_to_dict(model, max_depth=1, current_depth=0):
    if model is None or current_depth > max_depth:
        return None

    result = {}

    try:
        mapper = class_mapper(model.__class__)
    except:
        # If it's not a SQLAlchemy model class, return the object as is
        return model

    for key in mapper.column_attrs.keys():
        result[key] = getattr(model, key)

    # Handle relationships
    for rel_name, rel_attr in mapper.relationships.items():
        try:
            related_obj = getattr(model, rel_name)
            if related_obj is not None:
                if isinstance(related_obj, list):
                    result[rel_name] = [model_to_dict(item, max_depth, current_depth + 1) for item in related_obj if
                                        item is not None]
                else:
                    result[rel_name] = model_to_dict(related_obj, max_depth, current_depth + 1)
        except DetachedInstanceError:
            # Skip this relationship if it's not loaded
            pass

    return result


def get_values(repo_branch, project_manager, user_id):
    repo_name = repo_branch.repo_name.split("/")[-1]
    branch_name = repo_branch.branch_name
    project_details = project_manager.get_project_from_db(
        f"{repo_name}-{branch_name}", user_id
    )
    project_deleted = None
    if project_details:
        project_deleted = project_details.is_deleted
    return repo_name, branch_name, project_deleted, model_to_dict(project_details)
