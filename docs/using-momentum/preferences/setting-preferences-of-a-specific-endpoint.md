# Setting preferences of a specific endpoint

<mark style="color:green;">`PUT`</mark> `/endpoints/preferences`

Set preferences / custom instructions for test generation.

**Headers**

| Name          | Value              |
| ------------- | ------------------ |
| Content-Type  | `application/json` |
| Authorization | `Bearer <token>`   |

**Body**

<table><thead><tr><th width="249">Name</th><th width="212">Type</th><th>Description</th></tr></thead><tbody><tr><td><code>identifier</code></td><td>string</td><td>The node id that points to the specific endpoint you want to target tests for, ex : <code>/server.py:search</code></td></tr><tr><td><code>project_id</code></td><td>number</td><td>Project id</td></tr><tr><td><code>preference</code></td><td>string</td><td>Test customisation / preferences  that you'd like the system to adhere to.</td></tr></tbody></table>

**Response**

**Response**

{% tabs %}
{% tab title="200" %}
```json
null //the test preferences were saved to the database
```
{% endtab %}

{% tab title="400" %}
```json
{ //invalid project id
    "detail": "Project Details not found."
}
```
{% endtab %}
{% endtabs %}
