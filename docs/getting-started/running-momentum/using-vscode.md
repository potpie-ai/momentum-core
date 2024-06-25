# Using VSCode

To run using vscode, add the following launch.json to .vscode&#x20;

```
{

    "version": "0.2.0",
    "configurations": [
    
        {
            "name": "Python Debugger: main",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "server.main:app",
                "--host", "0.0.0.0",
                "--port", "8001"
            ],
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/server",
                "OPENAI_API_KEY": "",
                "OPENAI_MODEL_REASONING": "gpt-4o",
                "GITHUB_PRIVATE_KEY":"",
                "GITHUB_APP_ID":"", 
                "GCP_PROJECT":"",
                "POSTGRES_DB": "dbname",
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "mysecretpassword",
                "POSTGRES_SERVER": "postgresql://postgres:mysecretpassword@localhost:5432/dbname",
                "POSTGRES_HOST":"localhost",
                "POSTGRES_PORT":"5432",
                "NEO4J_URI": "bolt://localhost:7687",
                "NEO4J_USERNAME": "neo4j",
                "NEO4J_PASSWORD": "mysecretpassword",
                "PORTKEY_API_KEY": "",
                "ENV":"development"
                    }
                }
    ]
}
```

Ensure you replace the openapi key, github app key and id, database config and portkey api key with correct credentials.

Once this is in place , simply go to run and debug tab, and click on the green play button to start the app.
