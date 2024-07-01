from server.utils.ai_helper import llm_call, print_messages, get_llm_client
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai.chat_models import ChatOpenAI
import os

from server.utils.github_helper import GithubService
from server.utils.graph_db_helper import Neo4jGraph
from server.parse import get_node, get_flow

neo4j_graph = Neo4jGraph()

db_path = ".momentum/momentum.db"

class Dependencies:
    def __init__(self, user_id):
        self.user_id = user_id
        self.neo4j_graph = Neo4jGraph()
        self.openai_client = get_llm_client(user_id, "gpt-3.5-turbo-0125")
        self.user_pref_openai_client = get_llm_client(user_id, os.environ['OPENAI_MODEL_REASONING'])
        self.plan_client = self.user_pref_openai_client
        self.detect_client = self.openai_client
        self.generate_test_client = self.user_pref_openai_client
        
    def add_codebase_map_path(self, directory):
        return f"{directory}/{db_path}"


    async def dependencies_from_function(self, project_details, function_identifier: str,
        function_to_test: str, 
        flow: list,
        print_text: bool = True,  # optionally prints text; helpful for understanding the function & debugging
    ) -> str:
        calls = self.neo4j_graph.fetch_first_order_neighbors(function_identifier, project_details[2])

        # Step 1: Generate an explanation of the function
        detect_system_message = SystemMessage(
            content="You are a world-class Python unit testing expert with a keen ability to identify dependencies that can be mocked. You meticulously analyze code to determine which classes, functions, or third-party SDKs/libraries are called.",
        )
        
        
        detect_user_message = HumanMessage(
            content=f"""Please analyze the following Python function to identify its dependencies. List all classes, third-party SDKs/libraries called by this function, which could potentially be mocked for testing purposes. 
        
            DO NOT HALLUCINATE any new function or class names. You output should match the entities in the below code.

        Function to test: 
        ```python
        {function_to_test}
        ```

        List of user defined function calls from the above function: 
        ``` 
        {calls}
        ```
        DO NOT INCLUDE THE FOLLOWING functions in your output as they are accounted for: 
        {flow}
        ```
        Adhere to the following filtering RULES:
        * Pydantic classes are not dependencies. IDENTIFY possible pydantic classname references in function parameters and DO NOT INCLUDE them.
        * DO NOT include file names and paths as they cannot be mocked. 
        * ONLY include the names of the classes, functions, or third-party SDKs/libraries.
        * 'async' and 'await' are not dependencies.
        * Structure your output in a comma separated list format WITHOUT any additional text or spacing. 
            For example: 
            function1,classA,importB
        
        """
        ,
            )

        detect_messages = [detect_system_message, detect_user_message]
        if print_text:
            print_messages(detect_messages)


        explanation = await llm_call(self.detect_client, detect_messages)
        return [x.strip() for x in explanation.content.split(",") if x.strip() != ""]


    async def get_dependencies(self, project_details, function_identifier):
        flow = get_flow(function_identifier, project_details[2])
        flow_trimmed = [x.split(':')[1] for x in flow if x != function_identifier]
        output = []
        for function in flow:
            node = get_node(function, project_details)
            code = GithubService.fetch_method_from_repo(node)
            output += ( await self.dependencies_from_function(project_details, function, code, flow_trimmed))
        return output+flow_trimmed

