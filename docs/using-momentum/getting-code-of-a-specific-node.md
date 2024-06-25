# Getting code of a specific node

<mark style="color:green;">`GET`</mark> `/code/node`

Get the code of a specific node in the parsed codebase. These nodes are typically your endpoints or their child functions that were listed as part of flow graph.

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Query Params**

| Name         | Type   | Description                                                          |
| ------------ | ------ | -------------------------------------------------------------------- |
| `project_id` | number | The project id generated during parsing of the code                  |
| `node_id`    | string | The node id that points to the specific node you want to get code of |

**Response**

{% tabs %}
{% tab title="200" %}
{% code overflow="wrap" %}
```json
{
    "code": "@api.get(\"/search\")\ndef search(args):\n    q = args.get(\"q\", None)\n\n    if q is None:\n        return { \"error\": \"q parameter required\" }\n    else:\n        results = []\n        for item in example_data[\"items\"]:\n            if item[\"name\"].count(q) > 0:\n                results.append(item)\n        return { \"count\": len(results), \"items\": results }",
    "file": "local-file-path/filename.py",
    "project_id": 4,
    "response": "",
    "start": 55,
    "end": 66,
    "id": "/server.py:search",
    "type": "function",
    "parameters": "[{\"identifier\": \"args\", \"type\": null}]"
}
```
{% endcode %}
{% endtab %}

{% tab title="200" %}
<pre class="language-json" data-overflow="wrap"><code class="lang-json"><strong>null //in case no node was found 
</strong></code></pre>
{% endtab %}

{% tab title="400" %}
```json
{
    "status_code": 400,
    "detail": "Project Details not found." //the project id is incorrect
}
```
{% endtab %}
{% endtabs %}
