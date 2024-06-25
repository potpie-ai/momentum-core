# Setting up the test plan

<mark style="color:green;">`PUT`</mark> `/test/plan`

Once the test plan is ready and you're good to go forward with it, it is time to let momentum set it up for execution.

**Headers**

| Name          | Value              |
| ------------- | ------------------ |
| Content-Type  | `application/json` |
| Authorization | `Bearer <token>`   |

**Body**

| Name         | Type                                                     | Description                                                                                          |
| ------------ | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `plan`       | Object of arrays, containing happy\_path and edge\_cases | The plans generated in the last step                                                                 |
| `project_id` | number                                                   | The project id generated during parsing of the code                                                  |
| `identifier` | string                                                   | The  id that points to the specific endpoint you want to set test plan for, ex : `/server.py:search` |

**Response**

{% tabs %}
{% tab title="200" %}
{% code overflow="wrap" %}
```json
null //empty response with 200 success code indicating the test plan has been set up
```
{% endcode %}
{% endtab %}

{% tab title="400" %}
{% code overflow="wrap" %}
```json
{  // Usually happens with invalid parameters
    "status_code": 400,
    "detail": "Project Details not found." 
}
```
{% endcode %}
{% endtab %}
{% endtabs %}
