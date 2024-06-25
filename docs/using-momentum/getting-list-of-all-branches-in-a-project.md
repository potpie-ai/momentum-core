# Getting list of all branches in a project

<mark style="color:green;">`GET`</mark> `/get-branch-list`

Use this endpoint to get list of all the available branches in a parsed repo

**Headers**

| Name          | Value            |
| ------------- | ---------------- |
| Authorization | `Bearer <token>` |

**Query Param**

| Name         | Type   | Description          |
| ------------ | ------ | -------------------- |
| repo\_`name` | string | username/branch-name |

**Response**

{% tabs %}
{% tab title="200" %}
```json
{
    "branches": [
        "branch1",
        "main",
        "branch2"
    ]
}
```
{% endtab %}

{% tab title="404" %}
{% code overflow="wrap" %}
```json
{
    "detail": "Repository not found or error fetching branches: 400: Failed to get installation ID"
}
```
{% endcode %}
{% endtab %}
{% endtabs %}

{% hint style="info" %}
404 in this case would ususally mean that we do not have access to the codebase / github repo or it doesn't exist.
{% endhint %}
