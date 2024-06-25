# Logging in

<mark style="color:green;">`POST`</mark> `/login`

This endpoint allows users to log in to the app using their email and password. The user must first be created in Firebase Authentication. Upon successful login, a token is returned, which is necessary for authentication in subsequent requests.

#### Steps to Create User in Firebase Authentication

1. **Go to your Firebase project.**
2. **Navigate to Authentication.**
3. **Click on "Add User".**
4. **Provide the email and password.**
5. **Add the user.**

#### **Headers**

| Name         | Value              |
| ------------ | ------------------ |
| Content-Type | `application/json` |

**Body**

| Name       | Type   | Description          |
| ---------- | ------ | -------------------- |
| `email`    | string | Email of the user    |
| `password` | string | Password of the user |

**Response**

{% tabs %}
{% tab title="200" %}
```json
{
  "token":"bearertoken"
}
```
{% endtab %}

{% tab title="400" %}
{% code overflow="wrap" %}
```json
{
    "error": "ERROR: {'error': {'code': 400, 'message': 'INVALID_LOGIN_CREDENTIALS', 'errors': [{'message': 'INVALID_LOGIN_CREDENTIALS', 'domain': 'global', 'reason': 'invalid'}]}}"
}
```
{% endcode %}
{% endtab %}
{% endtabs %}

### Notes

* Ensure that the email and password provided are correct and match the credentials used in Firebase Authentication.
* The token returned in the response is necessary for all subsequent requests to the API. Store it securely and include it in the `Authorization` header as `Bearer <token>` for authenticated endpoints.
