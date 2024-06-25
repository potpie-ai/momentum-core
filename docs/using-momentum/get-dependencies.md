# Get Dependencies

<mark style="color:green;">`GET`</mark> `/endpoints/dependencies`

This helps you get list of all the dependencies of parsed code of a specific endpoint.&#x20;

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Query Params**

| Name          | Type   | Description                                                 |
| ------------- | ------ | ----------------------------------------------------------- |
| `project_id`  | number | The project id generated during parsing of the code         |
| `endpoint_id` | string | The endpoint identifier you need to list dependencies from. |

**Response**

{% tabs %}
{% tab title="200" %}
```json
[ //array of dependencies of the endpoint
    "API.get"
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
