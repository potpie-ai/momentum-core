# Generating Blast Radius

<mark style="color:green;">`GET`</mark> endpoints/blast

Now that you'd like to compare the changes and understand the blast radius of the changes, between the main/master branch and the branch you're planning to merge - we use this endpoint.

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Query Params**

| Name          | Type   | Description                       |
| ------------- | ------ | --------------------------------- |
| `project_id`  | number | Generated project id during parse |
| `base_branch` | string | base branch name                  |

**Response**

{% tabs %}
{% tab title="200" %}
```json
{
    "/server.py": [ //signifies the file in which it found the endpoint
        {
            "entryPoint": "GET /",
            "identifier": "/server.py:index"
        }
    ]
}
```
{% endtab %}

{% tab title="400" %}
```json
{
    "detail": "Project Details not found." //project id is incorrect
}
```
{% endtab %}
{% endtabs %}
