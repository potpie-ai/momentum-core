# Generating tests

<mark style="color:green;">`GET`</mark> `/test/generate`

Use momentum to generate tests for your&#x20;

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |



**Query Params**

| Name            | Type   | Description                                                                                               |
| --------------- | ------ | --------------------------------------------------------------------------------------------------------- |
| `project_id`    | number | The project id generated during parsing of the code                                                       |
| `identifier`    | string | The node id that points to the specific endpoint you want to generate tests for, ex : `/server.py:search` |
| `endpoint_path` | string | Complete path of the endpoint you want to test                                                            |



**Response**

{% tabs %}
{% tab title="200" %}
```json
Generated Tests Cases in form of python code
```
{% endtab %}

{% tab title="400" %}
```json
{
    "detail": "Project Details not found."
}
```
{% endtab %}

{% tab title="500" %}
{% code overflow="wrap" %}
```json
Internal Server Error //usually occours when the identifier is wrong
```
{% endcode %}
{% endtab %}
{% endtabs %}

You can use the generated tests from this endpoint to test relevant code.
