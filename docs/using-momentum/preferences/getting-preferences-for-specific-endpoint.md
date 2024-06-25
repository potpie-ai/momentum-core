# Getting preferences for specific endpoint

<mark style="color:green;">`GET`</mark> `/endpoints/preferences`

Check the configured preferences for a given endpoint

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Query Params**

| Name         | Type   | Description                                                                                                    |
| ------------ | ------ | -------------------------------------------------------------------------------------------------------------- |
| `project_id` | number | Project id                                                                                                     |
| `identifier` | string | The node id that points to the specific endpoint you want to confirm preferences for, ex : `/server.py:search` |

**Response**

{% tabs %}
{% tab title="200" %}
```json
Custom Instructions / Preferences instructions
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
