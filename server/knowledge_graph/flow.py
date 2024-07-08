import json
from typing import List, Dict
import os
from server.utils.ai_helper import get_llm_client, llm_call, print_messages
from langchain.schema import SystemMessage, HumanMessage
import hashlib
from server.db.session import SessionManager
from server.schemas import Inference, Explanation, Project, Endpoint, Explanation, Pydantic
from server.utils.github_helper import GithubService
from server.utils.graph_db_helper import Neo4jGraph

neo4j_graph = Neo4jGraph()

class FlowQuery:
    def __init__(self, query: str):
        self.query = query

class FlowInference:
    def __init__(self, project_id: str, directory: str, user_id: str):
        self.project_id = project_id
        self.directory = directory
        self.user_id = user_id
        self.explain_client = get_llm_client(user_id, "gpt-3.5-turbo-0125")

    def insert_inference(self, key: str, inference: str, project_id: str, overall_explanation: str, hash: str):
        with SessionManager() as db:
            inference_entry =  Inference(key=key, inference=inference, hash=hash, explanation=overall_explanation, project_id=project_id)
            db.add(inference_entry)
            db.commit()

    def _get_code_for_node(self, node):
        return GithubService.fetch_method_from_repo(node)

    def get_flow(self, endpoint_id, project_id):
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

    def get_code_flow_by_id(self, endpoint_id):
        code = ""
        nodes = self.get_flow(endpoint_id, self.project_id)
        for node in nodes:
            node = self.get_node(node)
            code += (
                "\n"
                + GithubService.fetch_method_from_repo(node)
                + "\n code: \n"
                + self._get_code_for_node(node)
            )
        return code

    def get_node(self, function_identifier):
        return neo4j_graph.get_node_by_id(function_identifier, self.project_id)

    def get_endpoints(self):
        with SessionManager() as db:
            endpoints = db.query(Endpoint.path, Endpoint.identifier).filter(
                Endpoint.project_id == self.project_id
            ).all()
            return [{"path": endpoint.path, "identifier": endpoint.identifier} for endpoint in endpoints]

    async def explanation_from_function(self, function_to_test: str) -> str:
        print(function_to_test)
        """Returns a integration test for a given Python function, using a 3-step GPT prompt."""

        # Step 1: Generate an explanation of the function
        explain_system_message = SystemMessage(
            content="You are a world-class Python developer with an eagle eye for unintended bugs and edge cases. You carefully explain code with great detail and accuracy. You organize your explanations in markdown-formatted, bulleted lists.",
        )
        explain_user_message = HumanMessage(
            content=f"""Please explain the following Python function. Review what each element of the function is doing precisely and what the author's intentions may have been. Organize your explanation as a markdown-formatted, bulleted list.

        ```python
        {function_to_test}
        ```""",
        )

        explain_messages = [explain_system_message, explain_user_message]
        print_messages(explain_messages)

        explanation = await llm_call(self.explain_client, explain_messages)
        return explanation.content

    async def _get_explanation_for_function(self, function_identifier, node):
        with SessionManager() as db:
            if "code" in node:
                code_hash = hashlib.sha256(node["code"].encode('utf-8')).hexdigest()
                explanation = db.query(Explanation.explanation).filter(
                    Explanation.identifier == function_identifier,
                    Explanation.hash == code_hash
                ).first()

                if not explanation:
                    explanation_text = await self.explanation_from_function(node["code"])
                    explanation = Explanation(identifier=function_identifier, hash=code_hash, explanation=explanation_text)
                    db.add(explanation)
                    db.commit()
                else:
                    explanation_text = explanation.explanation

        return explanation_text

    async def generate_overall_explanation(self, endpoint: Dict) -> str:
        with SessionManager() as db:
            code = self.get_code_flow_by_id(endpoint["identifier"])
            if code != '':
                code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
                inference = db.query(Inference.inference).filter(
                    Inference.key == endpoint["path"],
                    Inference.hash == code_hash
                ).first()
                if inference:
                    return inference.inference, code_hash
                else:
                    result = await self.generate_explanation(code), code_hash
                    return result

        return None, None

    async def generate_explanation(self, code: str) -> str:
        explain_system_message = SystemMessage(
            content="You are a world-class Python developer with an eagle eye for unintended bugs and edge cases. You carefully explain code with great detail and accuracy. You organize your explanations in markdown-formatted, bulleted lists.",
        )
        explain_user_message = HumanMessage(
            content=f"""Please analyse the following Python functions. Review what each element of the function is doing precisely and what the author's intentions may have been. Return the overall intent of the API call. Organize your explanation as a markdown-formatted, bulleted list.
```python
{code}
```
""")
        explain_messages = [explain_system_message, explain_user_message]
        explanation = await llm_call(self.explain_client, explain_messages)
        return explanation.content

    async def get_intent_from_explanation(self, explanations: str) -> str:
        explain_system_message = SystemMessage(
            content="You are a world-class Python developer with an eagle eye for unintended bugs and edge cases. You carefully explain code with great detail and accuracy. You organize your explanations in markdown-formatted, bulleted lists.",
        )
        explain_user_message = HumanMessage(
            content=f"""You are provided the following explanation of a series of Python functions in the call stack of a given API. From this explanation, extract the intent of the API call. Return only the intent, nothing else.
```
{explanations}
```
""")
        explain_messages = [explain_system_message, explain_user_message]
        explanation = await llm_call(self.explain_client, explain_messages)
        return explanation.content

    def get_inferences(self) -> List[Dict]:
        with SessionManager() as db:
            inferences = db.query(Inference.key).filter(
                Inference.project_id == self.project_id
            ).all()
            return [inference.key for inference in inferences]

    async def infer_flows(self) -> Dict[str, str]:
        endpoints = self.get_endpoints()
        inferred_flows = self.get_inferences()
        flow_explanations = {}

        for endpoint in endpoints:
            if endpoint["path"] not in inferred_flows:
                overall_explanation, code_hash = await self.generate_overall_explanation(endpoint)
                if overall_explanation is not None:
                    flow_explanations[endpoint["path"]] = (await self.get_intent_from_explanation(overall_explanation), overall_explanation, code_hash)

        return flow_explanations

async def understand_flows(project_id, directory, user_id):
    flow_inference = FlowInference(project_id, directory, user_id)
    flow_explanations = await flow_inference.infer_flows()
    with SessionManager() as db:
        for key, inference in flow_explanations.items():
            inference_entry = Inference(key=key, inference=inference[0], explanation=inference[1], hash=inference[2], project_id=project_id)
            db.add(inference_entry)
        db.commit()
    from server.knowledge_graph.knowledge_graph import KnowledgeGraph
    KnowledgeGraph(project_id)