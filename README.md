# Momentum

Momentum is an open-source tool designed to generate and understand powerful insights into your codebase. It helps you understand changes and impacts, generate test behaviours and test code and much more. 

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

momentum is a code auditor that analyses the necessary code behavior and tests it at every git push to ensure the code is ready for production.
It understands your backend codebase and generates visualisation and precise context for test plans and test cases for all entry points detected in the system.

## Features

<img title="momentum-features" alt="features" src="https://github.com/getmomentum/momentum-core/assets/19893222/b1d5164f-c348-4bf5-978d-6dbaf16c5cbd">

- **Blast Radius**: This will be a list of endpoints that could potentially be affected by the changes you made in your code. This will also be a starting point to decide what parts of your code need to be tested before shipping to production..
- **Dependency Visualization**: Visualize code dependencies and relationships.
- **Behaviour identification**: Automatically identify behaviors written in your code and generate a plan to test their functionality
- **Code generation to test functionality**: Generate code to test all behaviors identified and run it in your local environment through momentum



Code generation to test functionality

Debugging (using stack trace)

Self-healing (simple cases)

## Installation

To get started with Momentum, follow these steps:

### Steps

1. **Clone the repository**:
    ```bash
    git clone https://github.com/getmomentum/momentum-srv.git
    cd momentum-srv
    ```

2. **Set up the database via Docker**:
    ```bash
    docker-compose up
    ```

3. Set up environment: 
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Run migrations**:
   Create a .env inside `/server` based on .env.template
    ```bash
    alembic upgrade head
    ```

5. **Setup keys**: 
   You will have to setup keys for services like firebase auth, github app, Open AI, portkey among others. 
   Follow the detailed instructions [here](https://docs.momentum.sh/getting-started/installation/cloud-integrations)
   
6. **Start the application**:
    ```bash
    uvicorn server.main:app --host 0.0.0.0 --port 8001
    ```

## Build Instructions with docker

1. **Set Up the Environment:**
   Configure your environment variables by creating a `.env` file based on the `.env.template` provided in the repository. 
   This file should include all necessary configuration settings for the application.

2. **Google Cloud Authentication:**
   Log in to your Google Cloud account and set up Application Default Credentials (ADC). 
   You can find detailed instructions [here](https://cloud.google.com/docs/authentication/provide-credentials-adc#how-to).

3. **Build Docker Image:**
   Build the Docker image using the following command:
   ```bash
   docker build -t momentum .
   ```

4. **Bring the required infrastructure up:**
    ```bash
   docker-compose up
   ```
    
5. **Run migrations**:
   Ensure .env is correctly setup
    ```bash
    alembic upgrade head
    ```
    
6. **Run Momentum**
    ```bash
   ./run-momentum.sh
   ```
   Note: 
   (a) Read the shell script to modify google cloud credentials if needed
   (b) You might need to make it an executable, do it by running chmod +x run-momentum.sh

## Usage

After installation, you can access Momentum at `http://localhost:8001`. Key functionalities include:

- **User Authentication**
- **Parsing Codebase**
- **Listing Parsed Projects and Branches**
- **Generating Blast Radius**
- **Visualizing Dependencies and Flow Graphs**
- **Setting Preferences for Endpoints**
- **Generating and Setting Up Test Plans**


For detailed usage instructions, visit the [Momentum Documentation](https://docs.momentum.sh).

## Contributing

We welcome contributions from the community. To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

Refer to the [Contributing Guide](https://docs.momentum.sh/introduction-to-momentum/contributing-to-momentum) for more details.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
