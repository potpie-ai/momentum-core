import os

from crewai import Task
from langchain_community.tools.human.tool import HumanInputRun

from server.test_agent.agents import TestAgents
from server.test_agent.tools import CodeTools


class TestTasks:

    def __init__(self, reasoning_client, directory):
        self.reasoning_client = reasoning_client
        self.directory = directory

    #     def fixture_task(self):
    #         return Task(
    #             description="""1. **Identify Unique Fixture Needs**: Begin by identifying the specific needs for fixtures that were not addressed in the initial test data setup and mocking strategies. This includes database connection mocks, FastAPI application instances, and other application states critical for the tests. Clarify the purpose of each fixture, focusing on the unique aspect it brings to the test environment.

    # 2. **Efficient Setup and Teardown with @pytest.fixture**: Utilize the `@pytest.fixture` decorator to define functions for setting up and tearing down the required test environment states. Describe how these fixtures encapsulate the application state, including any database mocks or FastAPI TestClient instances, to provide a clean, isolated context for each test.

    # 3. **Optimize with Scope Parameters**: Implement scope parameters (`function`, `class`, `module`, `package`, `session`) to manage the lifecycle of fixtures efficiently. Discuss the reasoning behind choosing a specific scope for each fixture, aiming to balance resource utilization against test isolation and execution time. This step ensures that fixtures are instantiated only when necessary, reducing setup and teardown overhead.

    # 4. **Parametrized Fixtures for Enhanced Test Coverage**: Explore the implementation of parametrized fixtures to allow tests to run under various configurations or with different inputs. Explain the selection of parameters for each fixture, focusing on how they expand test coverage and robustness by simulating a wide range of scenarios and application states.

    # 5. **Database Mocks Setup**: Detail the process for setting up database mocks, ensuring tests interact with a controlled, predictable database environment. This includes mocking database connections and operations to test database interaction without affecting the actual database, essential for testing CRUD operations accurately.

    # 6. **FastAPI Application Mocks**: Outline the creation of FastAPI application mocks or instances using the FastAPI TestClient. This involves configuring the TestClient to simulate application behavior and responses, allowing for the testing of endpoint integrations and request handling in isolation from external services.

    # 7. **Integration with Test Suite**: Discuss the integration of these newly developed fixtures into the test suite, ensuring they are correctly utilized across relevant tests. This includes instructions on invoking fixtures in test functions and managing dependencies between fixtures to maintain test clarity and efficiency.

    # 8. **Review and Refinement**: Finally, encourage periodic review and refinement of fixture strategies to adapt to changes in application architecture and test requirements. This ongoing process ensures that fixtures remain effective and aligned with testing goals, supporting a robust, flexible test environment.
    # """,
    #             # description='Plan and write pytest fixtures for FastAPI tests based on test plan and backstory and endpoint code to be tested. Use the get code tool in order to get the code for the endpoint to be tested. ',
    #             expected_output="Properly formatted pytest fixture code for FastAPI tests",
    #             agent=TestAgents().fixtures_agent(),
    #             tools=[],
    #         )

    #     def get_input() -> str:
    #         print(
    #             "Insert your text. Enter 'q' or press Ctrl-D (or Ctrl-Z on Windows) to end."
    #         )
    #         contents = []
    #         while True:
    #             try:
    #                 line = input()
    #             except EOFError:
    #                 break
    #             if line == "q":
    #                 break
    #             contents.append(line)
    #         return "\n".join(contents)

    def get_pydantic_definition_task(self, identifier):
        return Task(
            description=f"""Endpoint identifier: {identifier} \n 
            Codebase directory: {self.directory} \n
            1. **Identify Pydantic Class Requirements**: Begin by identifying ALL the specific Pydantic classes required for the test data setup and mock response setup using the code under test. 
            2. Pydantic classes can include request and response models, data validation classes, any function definition parameters, and ANY other Pydantic structures used in the endpoint code. 
            3. DO NOT MAKE UP PYDANTIC DEFINITIONS: Call the get_pydantic_definitions_tool with a python list of classnames structured as a list ["classA","ClassB"] to get the definitions for all the classes you need. 
            4. If there are no pydantic objects REQUIRED for mock or test data setup, DO NOT create Pydantic definition for them.,
            5. Add the filename of the class as a comment in the pydantic definition. This is important for the get code tool to work properly.
            6. ALWAYS PROVIDE COMPLETE DEFINITIONS DO NOT LEAVE ANYTHING FOR THE USER TO IMPLEMENT """,
            expected_output=(
                "Properly formatted Pydantic class definition code"
            ),
            agent=TestAgents(
                self.reasoning_client, self.directory
            ).pydantic_definition_agent(),
            tools=[
                CodeTools().get_pydantic_definitions_tool,
                CodeTools().get_code,
            ],
        )


#     def data_setup_task(self, identifier, test_plan, get_pydantic_definition_task):
#         return Task(
#             description=""" You are responsible for creating all the test data necessary for testing the different scenarios included in the test plan for the function.
#            1.  This includes creating the necessary pydantic objects for the test data setup.
#     2. Request pydantic class definitions wherever needed using the get pydantic definition tool provided. DO NOT MAKE UP PYDANTIC DEFINITIONS. Call the tool multiple times to get the definitions for all the classes you need.
#     3. Use the get code tool if you require the code under test.
#     4. Use human input if you cannot generate meaningful test data , for example, if you need an s3 bucket name or a user id.
#     5. Create pytest fixtures for test data setup and cleanup where needed.
#     6. Use pytest-mocks to create mocks for the different scenarios included in the test plan. Ask the human for input if you need advice on whether to mock a certain class.
# """,
#             # description='based on the test plan and the code for the endpoint to be tested, evaluate what kind of data setup is needed for each test scenario. Use the pydantic definition tool in order to understand the input structure of each endpoint and create relevant pydantic object initialized with relevant datat from it to be used in the next test creation step. ',
#             expected_output="Input test data for each test scenario in the form of pydantic objects",
#             agent=TestAgents().data_setup_agent(identifier, test_plan),
#             context=[get_pydantic_definition_task],
#             tools=[CodeTools().get_pydantic_definition, CodeTools().get_code],
#         )

#     def mocking_task(self, identifier, test_plan):
#         return Task(
#             description="""1. **Define the Mocking Scope**: Begin by identifying which external dependencies or services need to be mocked. This includes third-party APIs, databases, or internal services not under test. Clearly articulate the reasons for mocking these components, focusing on the need to isolate the system under test from external interactions.

# 2. **Mocking Strategies**: Decide between using `pytest-mock` or `unittest.mock` based on the test framework and specific needs of the test suite. Outline the criteria for this choice, such as compatibility with the testing framework, ease of use, and available features.

# 3. **Direct Mocking vs. Fixtures**: Evaluate the test scenarios to determine if direct mocking within individual tests or the use of fixtures for shared mocked instances is more appropriate. Explain the rationale behind this decision, considering factors like test isolation, reusability of mock objects, and the complexity of setup and teardown processes.

# 4. **Scenario-Based Mocking**: For each external dependency being mocked, describe the different scenarios to be tested. These scenarios should cover normal operation, error conditions, timeouts, and unexpected responses. Detail the steps to configure the mock objects to simulate these conditions and the expected outcomes of the tests.

# 5. **Implementing Mocks**: Provide a step-by-step guide for implementing mocks in the test suite. This includes creating mock objects, configuring return values or side effects, and integrating mocks into the tests. Emphasize best practices for ensuring that mocks accurately reflect the behavior of the real dependencies they replace.

# 6. **Verifying Mock Interactions**: Outline methods for verifying that the system under test interacts with the mocks as expected. This includes checking that the correct methods are called with the expected arguments and that the system under test properly handles the mocked responses.

# 7. **Cleanup and Teardown**: Finally, detail the process for cleaning up mock objects after tests to prevent side effects on subsequent tests. This might involve resetting mock objects, removing any temporary data, or restoring original states if necessary.
# """,
#             expected_output="Mocks for each test scenario in the form of json objects objects",
#             agent=TestAgents().mocking_agent(identifier, test_plan),
#             tools=[CodeTools().get_code],
#         )

#     def test_task(
#         self, identifier, test_plan, fixture_task, data_setup_task, mocking_task
#     ):
#         return Task(
#             description="""

# Using Python and the pytest and pytest-mocks package, write a suite of integration tests. Following the test plan above, personalise your tests for the code flow defined for the identifier. You can fetch the code flow using the get code tool if needed.
# 1. Use to the output of the data setup task to utilise the fixtures where possible to avoid duplication of code and easy test data setup and cleanup.
# 2. Detail the rationale behind assertions, including status codes, data integrity, and application state, with examples of complex assertions for enhanced understanding.

# 3. Ensure tests are designed for independence and parallel execution, discussing patterns for shared setup/teardown while maintaining isolation. Mention tools that support these practices.

# 4. Address error handling and validation, with strategies for testing expected failures and asserting error messages.
# 5. Use FastAPI features for testing like the TestClient and create Pydantic objects for request body and response validation where required. Pydantic definitions of models can be looked up using the get pydantic definition tool.

# 5. Respond only with a python code block, do not respond with any other text. Format your output as follows:
# Reply only with complete code, do not reply with any other text, formatted as follows:
#         ```python
#         # imports
#         import pytest  # used for our integration tests
#         #insert other imports as needed
#         #fixtures

#         # integration tests
#         #insert integration test code here
#         ```
#         6. Always refer the API path from the code to ensure that you do not get 404 errors.
#         """,
#             expected_output="Properly formatted pytest test code for FastAPI",
#             agent=TestAgents().testing_agent(identifier, test_plan),
#             context=[data_setup_task],
#             tools=[CodeTools().get_code],
#         )
