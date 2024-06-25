# Known bugs & fixes

If you encounter **psycopg2** related errors, particularly on macOS, it is typically due to the absence of PostgreSQL in the local system, which causes the driver to malfunction. For further reference, please consult the relevant Stack Overflow thread [here](https://stackoverflow.com/questions/33866695/error-installing-psycopg2-on-macos-10-9-5).

The recommended solution for now is to execute the following command to install PostgreSQL:

```
brew install postgresql
```

{% hint style="info" %}
With our ongoing efforts to streamline the setup process, we are working towards integrating Docker solutions. This enhancement is scheduled for inclusion in upcoming releases.
{% endhint %}

