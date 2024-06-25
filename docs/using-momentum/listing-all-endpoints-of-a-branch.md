# Listing all endpoints of a branch

<mark style="color:green;">`GET`</mark> `/endpoints/list`

This api will list all the detected endpoints for the codebase that was parsed by momentum.

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Query Param**

| Name         | Type   | Description                                                |
| ------------ | ------ | ---------------------------------------------------------- |
| `project_id` | string | Project id that was generated when the project was parsed. |

**Response**

{% tabs %}
{% tab title="200" %}
```json
{
    "/server.py": [
        {
            "entryPoint": "GET /",
            "identifier": "/server.py:index"
        },
        {
            "entryPoint": "GET /helloworld",
            "identifier": "/server.py:list"
        },
        {
            "entryPoint": "GET /search",
            "identifier": "/server.py:search"
        },
        {
            "entryPoint": "POST /add",
            "identifier": "/server.py:add"
        },
        {
            "entryPoint": "POST /delete",
            "identifier": "/server.py:delete"
        }
    ]
}
```
{% endtab %}

{% tab title="400" %}
```json
{
    "detail": "Project Details not found."
}
```
{% endtab %}
{% endtabs %}

{% hint style="info" %}
The success response will give an empty array in case the repo does not have any REST endpoints.
{% endhint %}
