# Getting list of all parsed projects

## Listing all parsed repos of a user

<mark style="color:green;">`GET`</mark> `/projects/list`

Get the list of all parsed repos of authenticated user.

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Response**

{% tabs %}
{% tab title="200" %}
```json
[
    {
        "project_id": 2,
        "branch_name": "main",
        "repo_name": "vineetshar/distributed-id-generator",
        "last_updated_at": "2024-06-19T14:27:03.599554",
        "is_default": true,
        "project_status": "ready"
    },
    {
        "project_id": 3,
        "branch_name": "main",
        "repo_name": "vineetshar/python-simple-rest-api-cline",
        "last_updated_at": "2024-06-20T08:48:09.417632",
        "is_default": true,
        "project_status": "ready"
    }
]
```
{% endtab %}

{% tab title="401" %}
{% code overflow="wrap" %}
```json
{
    "detail": "Invalid authentication from Firebase. Invalid base64-encoded string: number of data characters (101) cannot be 1 more than a multiple of 4"
}
```
{% endcode %}
{% endtab %}
{% endtabs %}
