# User Registration

<mark style="color:green;">`POST`</mark> `/`signup

This endpoint allows you to register an authenticated user in our local database. The user's details should be provided in the request payload. Upon successful registration, the user will be added to the local database, allowing for subsequent interactions with the app.

#### **Headers**

| Name         | Value              |
| ------------ | ------------------ |
| Content-Type | `application/json` |

**Body**

<table data-full-width="false"><thead><tr><th>Name</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td><code>uid</code></td><td>String</td><td>Unique identifier for the user</td></tr><tr><td><code>email</code></td><td>String</td><td>Email address of the user</td></tr><tr><td><code>displayName</code></td><td>String</td><td>Display name of the user</td></tr><tr><td><code>emailVerified</code></td><td>Boolean</td><td>Indicates if the email is verified</td></tr><tr><td><code>createdAt</code></td><td>DateTime</td><td>Account creation date and time (ISO 8601)</td></tr><tr><td><code>lastLoginAt</code></td><td>DateTime</td><td>Last login date and time (ISO 8601)</td></tr><tr><td><code>providerData</code></td><td>Array</td><td>Array of provider data objects</td></tr><tr><td>├─ <code>providerId</code></td><td>String</td><td>Identifier for the authentication provider</td></tr><tr><td>└─ <code>providerName</code></td><td>String</td><td>Name of the authentication provider</td></tr><tr><td><code>providerUsername</code></td><td>String</td><td>Username provided by the authentication provider</td></tr></tbody></table>

#### Sample Request

```bash
curl -X POST https://server-ip:port/signup \
-H "Content-Type: application/json" \
-H "Authorization: Bearer {token}" \
-d '{
  "uid": "12345",
  "email": "testaccount@gmail.com",
  "displayName": "Sample User",
  "emailVerified": true,
  "createdAt": "2024-06-19T12:34:56Z",
  "lastLoginAt": "2024-06-19T12:34:56Z",
  "providerData": [
    {
      "providerId": "google.com",
      "providerName": "Google"
    }
  ],
  "providerUsername": "testaccount"
}'
```



**Response**

{% tabs %}
{% tab title="200" %}
```json
{
  "uid": "12345",
}
```
{% endtab %}

{% tab title="400" %}
```json
{
  "error creating user"
}
```
{% endtab %}
{% endtabs %}

By following the above guidelines, you can seamlessly register users in the local database and proceed with further interactions within the app.
