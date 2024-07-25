<p align="center">
  <a href="https://momentum.sh?utm_source=github//#gh-dark-mode-only">
    <img src="https://github.com/getmomentum/momentum-core/assets/19893222/7b3212c0-2635-4a7c-a15d-fee488a0f471" width="318px" alt="Momentum logo" />
  </a>
  <a href="https://momentum.sh?utm_source=github//#gh-light-mode-only">
    <source media="(prefers-color-scheme: dark)">
    <img alt="Momentum Logo light" src="https://github.com/getmomentum/momentum-core/assets/19893222/285fe228-770e-43ed-9eb8-968d46eaafeb" width="318px"/>
  </a>
</p>

<br/>

<p align="center">
  <a href="https://pypi.org/project/momentum-cli/">
    <img src="https://img.shields.io/pypi/v/momentum-cli" alt="pypi package">
  </a>
  <a href="https://github.com/getmomentum/momentum-core/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/getmomentum/momentum-core" alt="Apache 2.0">
  </a>
</p>

<h1 align="center">
  The open-source integration testing tool for your backend code
</h1>

<div align="center">
  From git push to production-ready: See the unseen, test the untested
</div>

<p align="center">
  <br />
  <a href="https://docs.momentum.sh" rel="dofollow"><strong>Explore the docs »</strong></a>
  <br />

<br/>
  <a href="https://github.com/getmomentum/momentum-core/issues/new?assignees=&labels=type%3A+bug&template=bug_report.yml&title=%F0%9F%90%9B+Bug+Report%3A+">Report Bug</a>
  ·
  <a href="https://github.com/getmomentum/momentum-core/issues/new?assignees=&labels=feature&template=feature_request.yml&title=%F0%9F%9A%80+Feature%3A+">Request Feature</a>
  ·
<a href="https://discord.gg/z6tj9Ufc">Join Our Discord</a>
  ·
  <a href="https://roadmap.momentum.sh">Roadmap</a>
  ·
  <a href="https://twitter.com/momentumdotsh">X</a>
</p>

<div align="center"> 
  
  [![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/getmomentum/momentum-core)
</div>

Momentum is an open-source tool designed to generate and understand powerful insights into your codebase. It helps you understand changes and their impacts, generate test behaviours and integration test code and much more. 


## Table of Contents

- [Introduction](#introduction)
- [What is a behavior?](#what-is-a-behavior)
- [Here's how momentum can help you!](#heres-how-momentum-can-help-you)
- [Installation](#installation)
- [Build Instructions with docker](#build-instructions-with-docker)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

momentum analyses your codebase and understands intended code behavior and tests it at every git push to ensure the code is ready for production.
It generates visualisation and precise context for test plans and test cases for all entry points detected in the system.

## What is a behavior?
A behavior is defined as a task or functionality you were trying to create using your code. Examples could be deleting a document using a deleting API or creating a new user in the database. Behaviors can also be more complex sometimes where third-party dependencies are associated for example fetching data from a payment API to check the status. Behaviours must be independently executable tasks.

## Here's how momentum can help you!

<img title="blast radius" alt="blast radius" src="https://github.com/getmomentum/momentum-core/assets/19893222/195432e7-1444-4964-8a55-37410116897e">

- **Blast Radius**: This will be a list of endpoints that could potentially be affected by the changes you made in your code. This will also be a starting point to decide what parts of your code need to be tested before shipping to production..

<img title="dependency visualisation" alt="dependency visualisation" src="https://github.com/getmomentum/momentum-core/assets/19893222/7d4356be-2868-48e5-9f42-7a296a86d6f5">

- **Dependency Visualization**: Visualize code dependencies and relationships.
  
<img title="behaviuor detection" alt="behaviour detection" src="https://github.com/getmomentum/momentum-core/assets/19893222/f80469af-f16c-498f-97b9-c504a27242cd">

- **Behaviour identification**: Automatically identify behaviors written in your code and generate a plan to test their functionality

<img title="code generation" alt="code generation" src="https://github.com/getmomentum/momentum-core/assets/19893222/942dfcfd-6a35-4dca-af48-f14b9fcd0413">

- **Code generation to test functionality**: Generate code to test all behaviors identified and run it in your local environment through momentum

  <img title="code run" alt="code run" src="https://github.com/getmomentum/momentum-core/assets/19893222/6d935599-5475-4be9-a611-495e888875ad">
  
- **Run code in local dev environment**: No need for yet another yaml, our cli works with your existing dev environment to run code.

  <img title="code debugging" alt="code debugging" src="https://github.com/getmomentum/momentum-core/assets/19893222/2340a38f-c812-42e9-af56-e2684cf0722b">

- **Debug code**: Based on the stacktrace of the run, momentum can diagnose and propose a solution

## Installation

To get started with Momentum, follow these steps:

### Steps

1. **Clone the repository**:
    ```bash
    git clone https://github.com/getmomentum/momentum-core.git
    cd momentum-core
    ```

2. **Set up the virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
3. **Setup keys and .env**: 
   You will have to setup keys for services like firebase auth, github app, Open AI, portkey among others. 
   Follow the detailed instructions [here](https://docs.momentum.sh/getting-started/installation/cloud-integrations)
   
6. **Start the application**:
    ```bash
    ./start_momentum.sh
    ```

Note: You might need to make it an executable, do it by running chmod +x start_momentum.sh

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

We welcome contributions from the community. Contributions can be of the form: 
1. Documentation : Help improve our docs! If you fixed a problem, chances are others faced it too.
2. Code : Help us make improvements to existing features and build new features for momentum. 
3. Tests :  Help us make momentum resilient by contributing tests.

To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

Refer to the [Contributing Guide](https://docs.momentum.sh/introduction-to-momentum/contributing-to-momentum) for more details.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 💪 Thanks To All Contributors

Thanks a lot for spending your time helping build momentum. Keep rocking 🥂

<img src="https://contributors-img.web.app/image?repo=getmomentum/momentum-core" alt="Contributors"/>
