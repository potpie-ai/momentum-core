import logging
import os
import random
import re
import string

from crewai import Crew
from crewai.process import Process
import re
import random
import string
from server.utils.ai_helper import get_llm_client
import asyncio
from server.test_agent.agents import TestAgents
from server.test_agent.tasks import TestTasks

from server.utils.test_detail_handler import UserTestDetailsManager


class GenerateTest:
  
  def __init__(self, identifier: str, endpoint_path: str, test_plan: dict, user_id: str, directory: str,
               project_id: str, preferences: dict, configuration: dict):
    self.directory = directory
    self.user_id = user_id
    self.openai_client = get_llm_client(user_id, "gpt-3.5-turbo-0125")
    self.reasoning_client = get_llm_client(user_id, os.environ['OPENAI_MODEL_REASONING'])
    self.test_plan = test_plan 
    self.identifier = identifier
    self.endpoint_path = endpoint_path
    self.pydantic_definition_task = TestTasks(self.reasoning_client,self.directory).get_pydantic_definition_task(identifier, project_id)
    self.pydantic_definition_agent = TestAgents(self.openai_client, self.directory).pydantic_definition_agent()
    self.code_analysis_agent = TestAgents(self.openai_client,self.directory).code_analysis_agent(identifier, project_id)
    self.knowledge_graph_query_task = TestTasks(self.reasoning_client, self.directory).query_knowledge_graph(identifier, project_id)
    self.test_task = TestTasks(self.reasoning_client, self.directory ).test_task(identifier , self.test_plan, self.endpoint_path,self.knowledge_graph_query_task, self.pydantic_definition_task, project_id, preferences, configuration)
    self.testing_agent = TestAgents(self.openai_client, self.directory).testing_agent(identifier, self.test_plan)
    self.test_crew = Crew(agents=[self.pydantic_definition_agent, self.code_analysis_agent, self.testing_agent], tasks=[self.pydantic_definition_task, self.knowledge_graph_query_task, self.test_task], process=Process.sequential, llm=self.openai_client)
    self.user_detail_manager = UserTestDetailsManager()
    
  def extract_code_blocks(self, text):
    if "```python" in text:
      code_blocks = re.findall(r'```python(.*?)```', text, re.DOTALL)
    else:
      code_blocks = text
    return code_blocks


  async def write_tests(self, identifier: str,
                        no_of_test_generated: int, project_details: dict, user_id: str):
    logging.info(f"project_id: {project_details['id']}, write_tests - identifier: {identifier}")
    project_id = project_details["id"]
    repo_name = project_details["repo_name"]
    branch_name = project_details["branch_name"]
    result = await asyncio.to_thread(self.test_crew.kickoff, None)
    logging.info(f"project_id: {project_id}, write_tests - result: {result}")
    self.user_detail_manager.send_user_test_details(
        project_id=project_id,
        user_id=user_id,
        number_of_tests_generated=no_of_test_generated,
        repo_name=repo_name,
        branch_name=branch_name
    )

    return self.extract_code_blocks(result)[0]

  @staticmethod
  async def create_temp_test_file( identifier, result, directory):
      
      temp_file_id = ''.join(random.choice(string.ascii_letters) for _ in range(8))
      if not os.path.exists(f"{directory}/tests"):
        os.mkdir(f"{directory}/tests")
    
      filename = f"{directory}/tests/test_{identifier.split(':')[-1]}_{temp_file_id}.py"

 

      with open(filename, 'w') as file:
        # Write the string to the file
          file.write(result)
      return filename
