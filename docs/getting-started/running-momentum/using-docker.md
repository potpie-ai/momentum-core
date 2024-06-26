# Using Docker

1. **Set Up the Environment:** Configure your environment variables by creating a `.env` file based on the `.env.template` provided in the repository. This file should include all necessary configuration settings for the application.
2. **Google Cloud Authentication:** Log in to your Google Cloud account and set up Application Default Credentials (ADC). You can find detailed instructions [here](https://cloud.google.com/docs/authentication/provide-credentials-adc#how-to).
3.  **Build Docker Image:** Build the Docker image using the following command:

    ```
    docker build -t momentum .
    ```
4.  **Bring the required infrastructure up:**

    ```
    docker-compose up
    ```
5.  **Run migrations**: Ensure .env is correctly setup

    ```
    alembic upgrade head
    ```
6.  **Run Momentum**

    ```
    ./run-momentum.sh
    ```

{% hint style="info" %}
(a) Read the shell script to modify google cloud credentials if needed.\
(b) You might need to make it an executable, do it by running chmod +x run-momentum.sh.
{% endhint %}
