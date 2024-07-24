import os

from crewai import Task
from langchain_community.tools.human.tool import HumanInputRun

from server.test_agent.agents import TestAgents
from server.test_agent.tools import CodeTools


class TestTasks:

    def __init__(self, reasoning_client, directory):
        self.reasoning_client = reasoning_client
        self.directory = directory

    
    def get_pydantic_definition_task(self, identifier , project_id):
            return Task(
                description=f"""Endpoint identifier: {identifier} \n  Project id: {project_id} \n
                Codebase directory: {self.directory} \n
                1. **Identify Pydantic Class Requirements**: Begin by identifying ALL the specific Pydantic classes required for the test data setup and mock response setup using the code under test. 
                2. Pydantic classes can include request and response models, data validation classes, any function definition parameters, and ANY other Pydantic structures used in the endpoint code. 
                3. DO NOT MAKE UP PYDANTIC DEFINITIONS: Call the get_pydantic_definitions_tool with a python list of classnames structured as a list ["classA","ClassB"] to get the definitions for all the classes you need. 
                4. If there are no pydantic objects REQUIRED for mock or test data setup, DO NOT create Pydantic definition for them.,
                5. Add the filename of the class as a comment in the pydantic definition. This is important for the get code tool to work properly.
                6. ALWAYS PROVIDE COMPLETE DEFINITIONS DO NOT LEAVE ANYTHING FOR THE USER TO IMPLEMENT 
                7. Use the exact provided project id for tools and do not create new project ids """,
                expected_output="Properly formatted Pydantic class definition code",
                agent=TestAgents(self.reasoning_client, self.directory).pydantic_definition_agent(),
                tools=[CodeTools().get_pydantic_definitions_tool, CodeTools().get_code],
                async_execution=True,
            )

    def query_knowledge_graph(self, identifier, project_id):
        return Task(
            description=f""" Endpoint identifier: {identifier} \n  Project id: {project_id} \n 
            1. **Formulate a Clear Query**: Begin by formulating a clear and specific natural language query to retrieve the desired information from the knowledge graph along with project id. Consider the various aspects of the codebase you want to explore, such as API endpoints, code explanations, relationships between code elements, or pydantic definitions.
            2. **Analyze Query Results**: Once you receive the query results, carefully analyze them to understand the relationships and dependencies between different code elements. Look for insights that can help you gain a deeper understanding of the codebase and its functionality.
            3. **Utilize Code Explanations**: Pay attention to the code explanations and inferred knowledge provided in the query results. These explanations can offer valuable insights into the purpose and functionality of specific code segments, helping you make informed decisions during the testing process.
            4. **Leverage Pydantic Definitions**: If your query involves pydantic models, make sure to examine the pydantic definitions using the get pydantic definitions tool. Understanding the data models and schemas used in the project is crucial for creating accurate and comprehensive tests. Incude the definitions is final output AS IS.
            5. **Refine Queries if Needed**: If the initial query results are unclear or insufficient, don't hesitate to refine your queries and seek additional information from the knowledge graph. Iterative querying can help you gather all the necessary details to thoroughly understand the codebase.
            6. **Apply Insights to Testing**: Finally, apply the insights gained from the knowledge graph to enhance the quality and effectiveness of your tests. Use the information to make informed decisions, identify potential edge cases, and ensure that your tests cover a wide range of scenarios relevant to the codebase.
            7. **Plan imports for test file**: The test file should always import functions and classes from the correct path and not a made up path. """,
            expected_output="""1. Relevant insights and information from the code knowledge graph to aid in understanding the codebase and creating effective tests.,
            2.INCLUDE EXACT PYDANTIC DEFINITIONS OF REQUESTED CLASSES WITH NO MODIFICATIONS IN OUTPUT.
            3.ALWAYS INCLUDE the accurate path for classes or functions that need to be imported in the test file.""",

            agent=TestAgents(self.reasoning_client, self.directory).code_analysis_agent(identifier, project_id),
            tools=[CodeTools().ask_knowledge_graph, CodeTools.get_code, CodeTools.get_pydantic_definitions_tool],
            async_execution=True,
        )
        
    def test_task(
        self, identifier, test_plan,  endpoint_path, code_analysis_task, pydantic_definition_task,
            project_id, preferences, configuration
    ):
        return Task(
            description= f"""Test Plan {test_plan} for identifier {identifier} and project id {project_id}
    Using Python and ONLY the pytest package along with pytest-mocks for mocking, write a suite of integration tests - one each for every scenario in the test plan above, personalise your tests for the flow defined by the function that can be fetched using the get_code tool. 
    The complete path of the endpoint is {endpoint_path}. It is important to use this complete path in the test API call because the code might not contain prefixes.
    Consider the following points while writing the integration tests:
    You can fetch the code under test using the get code tool with correct identifier and project id in order to write correct mocks and function/ class imports.
    Talk to knowledge graph using the ask knowledge graph tool to answer any setup questions.
    ALWAYS use the pydantic definitions tool to get the accurate file paths of the pydantic classes you want to import.     
    * Analyze the provided function code and identify the key components, such as dependencies, database connections, and external API calls, that need to be mocked or set up for testing.
    * Review the provided test plan and understand the different test scenarios that need to be covered. Consider edge cases, error handling, and potential variations in input data.
    * Use the provided context and pydantic classes from the output of the code analysis task to create the necessary pydantic objects for the test data and mock test data setup. This ensures that the tests align with the expected data structures used in the function.
    * Pay attention to the preferences provided: ({preferences}). If a list of entities (functions, classes, databases, etc.) is specified to be mocked, strictly follow these preferences. If the preferences are empty, use your judgment to determine which components should be mocked, such as the database and any external API calls.
    * The test cases should have the input in this format: ({configuration["test_input"]}). Create the test cases keeping this in mind. Change the values for the fields present in the object in order to create happy cases and edge cases. If the test input do not fit the criteria to be API inputs, ignore them.
    * Utilize FastAPI testing features like TestClient and dependency overrides to set up the test environment. Create fixtures to minimize code duplication and improve test maintainability.
    * ALWAYS create a new FastAPI app in the test client and INCLUDE THE RELEVANT ROUTERS IN THE APP in it for testing. DO NOT ASSUME where the main FastAPI app is defined. DO NOT REWRITE ROUTERS in the test file.
    * When setting up mocks, use the pytest-mock library. Check if the output structure is defined in the code and use that to create the expected output response data for the test cases. If not defined, infer the expected output based on the test plan outcomes and the provided code under test.
    * When defining the target using pytest mocks, ensure that the target path is the path of the call and not the path of the definition.
    * For a func_a defined at src.utils.helper and imported in code as from src.utils.helper import func_a, the mock would look like : mocker.patch('src.pipeline.node_1.func_a', return_value="some_value")
    * Write clear and concise test case names that reflect the scenario being tested. Use assertions to validate the expected behavior and handle potential exceptions gracefully.
    * Consider the performance implications of the tests and optimize them where possible. Use appropriate setup and teardown methods to manage test resources efficiently.
    * Provide meaningful error messages and logging statements to aid in debugging and troubleshooting failed tests.
    * Reply only with complete code, formatted as follows (DO NOT INCLUDE ANYTHING OTHER THAN CODE, NOT EVEN MARKDOWN, JUST PYTHON CODE):
        # imports
        # Any required fixtures can be defined here
        #insert integration test code here
    ```
    """,
            expected_output="Properly formatted pytest test code for FastAPI",
            agent=TestAgents(self.reasoning_client, self.directory).testing_agent(identifier, test_plan),
            context=[code_analysis_task],
            tools=[CodeTools().get_code, CodeTools().ask_knowledge_graph, CodeTools.get_pydantic_definitions_tool],
        )
