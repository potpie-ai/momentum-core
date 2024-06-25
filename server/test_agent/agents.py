from crewai import Agent
from server.test_agent.tools import CodeTools


class TestAgents:

    def __init__(self, openai_client, directory):

        self.openai_client = openai_client
        self.directory = directory

    #     def testing_agent(self, identifier, test_plan):
    #         return Agent(
    #             role="FastAPI Software Developer in Test",
    #             goal="Write meaningful integration tests for FastAPI endpoints using Pytest framework",
    #             backstory=f"""You're a software developer in test at a software company building with FastAPI.
    #     You're responsible for reading the test plan and code under test and writing the necessary integration tests for the FastAPI endpoints using PyTest.
    #     You're also responsible for integrating and utilising any provided necessary fixtures for the tests.
    #     Request code definitions wherever needed using the tools provided.
    #     Endpoint identifier : {identifier},
    #     {test_plan}
    #   """,
    #             tools=[CodeTools().get_code],
    #             max_iter=10,
    #             max_rpm=10,
    #             verbose=True,
    #             allow_delegation=False,
    #             llm=openai_client
    #         )

    #     def fixtures_agent(self):
    #         return Agent(
    #             role="Pytest fixtures expert for writing good integration tests",
    #             goal="Write meaningful pytest fixtures for integration tests for FastAPI endpoints using Pytest framework",
    #             backstory=f"""You're a software developer specialist in test at a fast-growing startup working with FastAPI.
    #             you are responsible for writing the necessary fixtures for the tests.
    #     Request code definitions wherever needed using the tools provided.
    #   """,
    #             tools=[CodeTools().get_code],
    #             max_iter=10,
    #             max_rpm=10,
    #             verbose=True,
    #             allow_delegation=True,
    #             llm=openai_client
    #         )

    #     def mocking_agent(self,identifier, test_plan):
    #         return Agent(
    #             role="FastAPI Software Developer in Test",
    #             goal="Write meaningful integration tests for FastAPI endpoints using Pytest framework",
    #             backstory=f"""You're a software developer in test at a software startup working with FastAPI.
    #     You're responsible for reading the test plan and code under test and writing the necessary integration tests for the FastAPI endpoints using PyTest.
    #     You're also responsible for writing the necessary fixtures for the tests.
    #     Request code definitions wherever needed using the tools provided.
    #     Endpoint identifier : {identifier},
    #     {test_plan}
    #   """,
    #             tools=[CodeTools().get_code],
    #             max_iter=10,
    #             max_rpm=10,
    #             verbose=True,
    #             allow_delegation=True,
    #             llm=openai_client
    #         )

    #     def get_input() -> str:
    #         print("Insert your text. Enter 'q' or press Ctrl-D (or Ctrl-Z on Windows) to end.")
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

    #     def data_setup_agent(self, identifier, test_plan):
    #         return Agent(
    #             role="Test data setup agent",
    #             goal="Plan the test data setup required for the test scenarios, and write the necessary pydantic objects for the test data setup",
    #             backstory=f"""You're a software developer in test at a fast-growing startup working with FastAPI.
    #     You're responsible for reading the test plan and code under test and creating the test data required for the the necessary integration tests for the FastAPI endpoints using PyTest.
    #     This includes creating the necessary pydantic objects for the test data setup.
    #     Request pydantic class definitions wherever needed using the get pydantic definition tool provided.
    #     Use the get code tool if you require the code under test.
    #     Use human input if you cannot generate meaningful test data , for example, if you need an s3 bucket name or a user id.
    #     Create fixtures for test data setup and cleanup where needed.
    #     Endpoint identifier : {identifier},
    #     Test plan : {test_plan}
    #   """,
    #             tools=[CodeTools().get_code, CodeTools().get_pydantic_definition, HumanInputRun(input_func=self.get_input) ],
    #             max_iter=10,
    #             max_rpm=10,
    #             verbose=True,
    #             allow_delegation=True,
    #             llm=openai_client
    #         )

    def pydantic_definition_agent(self):
        return Agent(
            role=(
                "Get the COMPLETE pydantic definitions required for data"
                " setup."
            ),
            goal=(
                "Fetch the COMPLETE pydantic definitions for data setup"
                " required for the test scenarios."
            ),
            backstory="""You are a software developer in test working with FastAPI and Pydantic. Your main responsibilities include:
* Reading and understanding the code under test.
* Determining the necessary pydantic models required for setting up integration tests.
* Creating pydantic objects for the test data setup.

To effectively carry out these tasks, please follow these guidelines:
* ALWAYS use the "get code" tool first with the provided identifier as input. Analyzing the code under test is crucial for understanding the pydantic models required for the test data setup. Do not attempt to work from memory or assumptions.
* ALWAYS use the "get pydantic definition" tool provided to get pydantic class definitions. Input to the tool is a simple list of pydantic classnames derived from the code under test. It is CRUCIAL that you DO NOT make up pydantic class definitions.
* When you receive a response from either the "get pydantic definitions" or "get code" tool, do not modify the response unless it is an error message. Altering the response could lead to incorrect test setups and invalid results.
* If you encounter any error messages or unclear outputs from the tools, carefully review the error and attempt to resolve it. If the error persists or you are unsure how to proceed, seek assistance from your team lead or a senior developer.
* When setting up test data using pydantic objects, consider edge cases, boundary values, and potential error scenarios. Ensure your test data covers a wide range of possible inputs to thoroughly test the functionality of the code under test.""",
            tools=[
                CodeTools().get_code,
                CodeTools().get_pydantic_definitions_tool,
            ],
            max_iter=10,
            max_rpm=10,
            verbose=True,
            allow_delegation=True,
            llm=self.openai_client,
        )
