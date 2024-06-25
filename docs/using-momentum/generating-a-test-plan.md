# Generating a test plan

<mark style="color:green;">`GET`</mark> `/test/plan`

Get the test plan of a specific node in the parsed codebase.

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Query Params**

| Name         | Type   | Description                                                                                              |
| ------------ | ------ | -------------------------------------------------------------------------------------------------------- |
| `project_id` | number | The project id generated during parsing of the code                                                      |
| `identifier` | string | The node id that points to the specific endpoint you want to get test plan for, ex : `/server.py:search` |

**Response**

{% tabs %}
{% tab title="200" %}
```json
{
    "happy_path": [
        "Search for a common term that matches multiple items",
        "Search for a unique term that matches exactly one item",
        "Search for a term that matches items with varying case sensitivity"
    ],
    "edge_case": [
        "Search with an empty string as the query",
        "Search with a query that matches no items",
        "Search with special characters in the query"
    ]
}
```
{% endtab %}

{% tab title="500" %}
```json
{
  Internal Server Error  //occours on incorrect query params value
}
```
{% endtab %}
{% endtabs %}
