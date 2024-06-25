# Get Flow Graph

<mark style="color:green;">`GET`</mark> `/endpoints/flow/graph`

This endpoint helps you understand the flow from the endpoint to further neighbours in code in a parent - child relationship.

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Query Params**

| Name          | Type   | Description                                                                              |
| ------------- | ------ | ---------------------------------------------------------------------------------------- |
| `project_id`  | string | The project id generated during parsing of the code                                      |
| `endpoint_id` | string | The endpoint identifier that points to the specific node you want to generate graph from |

**Response**

{% tabs %}
{% tab title="200" %}
```json
[
    {
        "function": "/server.py:list", //the function that was hit by the endpoint
        "params": "[{\"identifier\": \"_\", \"type\": null}]", // the parameters of the function
        "response_object": "", // response object attached to the function
        "children": [ //further nodes and flow
            {
                "function": "/server.py:API.get",
                "params": "[{\"identifier\": \"self\", \"type\": null}, {\"identifier\": \"path\", \"type\": null}]",
                "response_object": "",
                "children": []
            }
        ]
    }
]
```
{% endtab %}

{% tab title="400" %}
```json
{
    "status_code": 400,
    "detail": "Project Details not found."
}
```
{% endtab %}
{% endtabs %}
