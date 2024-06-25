from typing import List

from langchain.tools import tool

from server.parse import (
    get_code_flow_by_id,
    get_pydantic_class,
    get_pydantic_classes,
)


class CodeTools:
    """
    A class that provides code tools for generating code for endpoint identifiers.
    """

    # Annotate the function with the tool decorator from LangChain
    @tool("Get accurate code context for given endpoint identifier")
    def get_code(identifier, directory):
        """
        Get the code for the specified endpoint identifier.

        Parameters:
        - identifier: The identifier of the endpoint.
        - directory: The directory of the codebase.

        Returns:
        - The code for the specified endpoint identifier.
        """
        return get_code_flow_by_id(identifier, directory)

    @tool("Get pydantic class definition for a single class name")
    def get_pydantic_definition(classname, directory):
        """
        Get the pydantic class definition for given class name

        Parameters:
        - classname: The name of a class.
        - directory: The directory of the codebase.

        Returns:
        - The code definition for the specified pydantic class.
        """
        print("pyd inp: " + classname)

        return get_pydantic_class(classname, directory)

    @tool("Get the pydantic class definition for list of class names")
    def get_pydantic_definitions_tool(classnames: List[str], directory):
        """
        Get the pydantic class definition for list of class names

        Parameters:
        - classnames: The list of the names of pydantic classes.
        - directory: The directory of the codebase.

        Returns:
        - The code definitions for the specified pydantic classes.
        """
        definitions = ""
        try:
            definitions = get_pydantic_classes(classnames, directory)
        except Exception as e:
            print(
                "something went wrong during fetching definition for"
                f" {classnames}",
                e,
            )
        return definitions
