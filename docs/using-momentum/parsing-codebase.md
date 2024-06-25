# Parsing codebase

{% hint style="info" %}
Reminder: The github app we created earlier will need access to the repo.

#### Steps to Grant Access to Repositories

1. **Go to your GitHub account.**
2. **Navigate to the GitHub app installation settings.**
3. **Select the app you created.**
4. **Update the repository access permission to repository you want to parse.**
{% endhint %}

<mark style="color:green;">`POST`</mark> `/parse`

This endpoint allows you to parse the codebases that the GitHub app has access to. Ensure the app has the necessary permissions to access the repositories you want to parse. You can update the app's access permissions through the GitHub app installation settings.

**Headers**

| Name          | Value              |
| ------------- | ------------------ |
| Content-Type  | `application/json` |
| Authorization | `Bearer <token>`   |

**Body**

| Name          | Type   | Sample             |
| ------------- | ------ | ------------------ |
| `repo_name`   | string | username/repo-name |
| `branch_name` | string | feature            |

**Response**

{% tabs %}
{% tab title="200" %}
```json
{
  "status": "success",
  "message": "The project has been parsed successfully"
}
```
{% endtab %}

{% tab title="400" %}
```json
{
    "detail": "Invalid authentication from Firebase. Token expired, 1718882208 < 1718886290"
}
```
{% endtab %}

{% tab title="400" %}
{% code overflow="wrap" %}
```json
{"detail":"Failed to get installation ID"}
```
{% endcode %}
{% endtab %}

{% tab title="500" %}
{% code overflow="wrap" %}
```json
{"detail":"404 Client Error: Not Found for url"}
```
{% endcode %}
{% endtab %}
{% endtabs %}

### Notes

* Ensure that the `Authorization` header contains a valid token obtained during the login process.
* The `repo_name` should be in the format `username/repo-name` , do not use a complete url.
* The `branch_name` should be a valid branch in the specified repository.
