import os
import random
import re
import string

from crewai import Crew
from crewai.process import Process

from server.parse import get_code_flow_by_id
from server.plan import Plan
from server.test_agent.agents import TestAgents
from server.test_agent.tasks import TestTasks

from server.utils.test_detail_handler import UserTestDetailsManager
from server.utils.ai_helper import get_llm_client


class GenerateTest:

    def __init__(
        self,
        identifier: str,
        endpoint_path: str,
        test_plan: dict,
        user_id: str,
        directory: str,
    ):
        self.directory = directory
        self.user_id = user_id
        
        self.openai_client = get_llm_client(
            user_id,
            "gpt-3.5-turbo-0125",
        )
        self.reasoning_client = get_llm_client(
            user_id,
            os.environ["OPENAI_MODEL_REASONING"],
        )
        self.test_plan = test_plan
        self.identifier = identifier
        self.endpoint_path = endpoint_path
        self.pydantic_definition_task = TestTasks(
            self.reasoning_client, self.directory
        ).get_pydantic_definition_task(identifier)
        self.pydantic_definition_agent = TestAgents(
            self.reasoning_client, self.directory
        ).pydantic_definition_agent()
        self.pydantic_crew = Crew(
            agents=[self.pydantic_definition_agent],
            tasks=[self.pydantic_definition_task],
            process=Process.sequential,
            llm=self.openai_client,
        )
        self.user_detail_manager = UserTestDetailsManager()


    def extract_code_blocks(self, text):
        if "```python" in text:
            code_blocks = re.findall(r"```python(.*?)```", text, re.DOTALL)
        else:
            code_blocks = text
        return code_blocks

    async def get_pydantic_definition(self, identifier: str):
        self.pydantic_crew.kickoff()
        return self.pydantic_definition_task.output.exported_output

    async def write_tests(self, identifier: str, preferences: dict,
                          no_of_test_generated: int, project_details: list, user_id: str):
        print(identifier)
        project_id = project_details[2]
        repo_name = project_details[3]
        branch_name = project_details[4]
        func = get_code_flow_by_id(identifier, self.directory)
        pydantic_classes = await self.get_pydantic_definition(identifier)
        result = await Plan(self.user_id).generate_tests(
            self.test_plan,
            func,
            pydantic_classes,
            preferences,
            self.endpoint_path,
        )
        print(result)
        self.user_detail_manager.send_user_test_details(
            project_id=project_id,
            user_id=user_id,
            number_of_tests_generated=no_of_test_generated,
            repo_name=repo_name,
            branch_name=branch_name
        )
        return result


async def create_temp_test_file(identifier, result, directory):

    temp_file_id = "".join(
        random.choice(string.ascii_letters) for _ in range(8)
    )
    if not os.path.exists(f"{directory}/tests"):
        os.mkdir(f"{directory}/tests")

    filename = (
        f"{directory}/tests/test_{identifier.split(':')[-1]}_{temp_file_id}.py"
    )

    with open(filename, "w") as file:
        # Write the string to the file
        file.write(result)
    return filename
