import re
from tree_sitter_languages import get_parser
import os
import logging

# Load Python grammar for Tree-sitter
parser = get_parser("python")

def _parse_diff_detail(patch_details, repo_path):
    changed_files = {}
    for filename, patch in patch_details.items():
        lines = patch.split('\n')
        current_file = os.path.normpath(os.path.join(repo_path, filename))
        changed_files[current_file] = set()
        current_line_number = None
        for line in lines:
            if line.startswith('@@'):
                parts = line.split()
                try:
                    add_start_info = parts[2][1:]  
                    if ',' in add_start_info:
                        add_start_line, add_num_lines = map(int, add_start_info.split(','))
                    else:
                        add_start_line = int(add_start_info)
                        add_num_lines = 1
                    current_line_number = add_start_line
                except ValueError as e:
                    current_line_number = None
            elif line.startswith('+') and current_line_number is not None:
                changed_files[current_file].add(current_line_number)
                current_line_number += 1
            elif not line.startswith('-') and current_line_number is not None:
                current_line_number += 1
    return changed_files


def extract_file_name(repo_name, branch_name, path):
    try:
        pattern = get_pattern(repo_name, branch_name)
        match = re.search(pattern, path)
        if match:
            file_path = match.group(1)
            return file_path
        else:
            return None
    except ValueError as e:
        logging.error(f"Exception {e}")
        return None


def get_pattern(repo_name, branch_name):
    posix_pattern = re.escape(f"{repo_name}-{branch_name}") + r"-\w+\/(.+)"
    windows_pattern = re.escape(f"{repo_name}-{branch_name}") + r"-\w+\\(.+)"
    
    if os.name == 'posix':
        pattern = posix_pattern
    elif os.name == 'nt':
        pattern = windows_pattern
    else:
        raise ValueError("Unsupported operating system")
    
    return pattern

def _parse_functions_from_file(file_path, repo_details, branch_name):
    if isinstance(repo_details, dict):
        # Local repository handling
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    else:
        # GitHub repository handling
        file_path_extracted = extract_file_name(repo_details.name, branch_name, file_path)
        content = repo_details.get_contents(file_path_extracted, ref=branch_name).decoded_content.decode('utf-8')
    
    tree = parser.parse(bytes(content, 'utf-8'))
    root_node = tree.root_node
    functions = {}

    def extract_functions(node, class_name=None):
        if node.type == 'function_definition':
            function_name = next((child for child in node.children if child.type == 'identifier'), None)
            if function_name:
                function_name = function_name.text.decode('utf-8')
                full_name = f"{class_name}.{function_name}" if class_name else function_name
                functions[full_name] = (node.start_point[0] + 1, node.end_point[0] + 1)
        elif node.type == 'class_definition':
            class_name = next((child for child in node.children if child.type == 'identifier'), None)
            if class_name:
                class_name = class_name.text.decode('utf-8')
                for child in node.children:
                    extract_functions(child, class_name)
        else:
            for child in node.children:
                extract_functions(child, class_name)

    extract_functions(root_node)
    return functions


def _find_changed_functions(changed_files, repo_path, repo_details, branch_name):
    result = []
    for file_path, lines in changed_files.items():
        try:
            functions = _parse_functions_from_file(file_path, repo_details, branch_name)
            for full_name, (start_line, end_line) in functions.items():
                if any(start_line <= line <= end_line for line in lines):
                    internal_path = os.path.relpath(file_path, start=repo_path)
                    if not internal_path.startswith(os.sep):
                        internal_path = os.sep + internal_path
                    result.append(f"{internal_path}:{full_name}")
        except Exception as e:
            logging.error(f"Exception {e}")
    return result


def get_updated_function_list(patch_details, repo_path, repo_details, branch_name):
    changed_files = _parse_diff_detail(patch_details, repo_path)
    return _find_changed_functions(changed_files, repo_path, repo_details, branch_name)
