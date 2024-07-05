from embedchain.loaders.postgres import PostgresLoader
from embedchain.pipeline import Pipeline as App
import os
import psycopg2

class KnowledgeGraph:
    _instance = None

    def __new__(cls, project_id):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.postgres_loader = PostgresLoader({"url":os.environ['POSTGRES_SERVER']})
            cls._instance.app = App()
        cls._instance.init_app(project_id)
        return cls._instance

    def init_app(self, project_id):
        self.app.add(f"SELECT key, explanation, inference FROM inference WHERE project_id={project_id};", data_type='postgres', loader=self.postgres_loader, metadata={"project_id": project_id})
        self.app.add(f"SELECT * FROM endpoints WHERE project_id={project_id};", data_type='postgres', loader=self.postgres_loader, metadata={"project_id": project_id})
        self.app.add(f"SELECT identifier, explanation FROM explanation WHERE project_id={project_id};", data_type='postgres', loader=self.postgres_loader, metadata={"project_id": project_id})
        self.app.add(f"SELECT * FROM pydantic WHERE project_id={project_id};", data_type='postgres', loader=self.postgres_loader, metadata={"project_id": project_id})

    def query(self, query, project_id):
        prefix = "Always INCLUDE ALL RELEVANT FILEPATH, FUNCTION NAME AND VARIABLE NAMES in your response. If you are asked about an API: ALWAYS include its HTTP verb and url path along with its identifier in the response: \n"
        return self.app.query(prefix+query, where={"project_id": project_id})