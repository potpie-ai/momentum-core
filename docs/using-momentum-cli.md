# Using Momentum CLI

Momentum CLI is used in combination with **Momentum Pro / Enterprise** to run tests on your local IDE. \
\
This makes the flow of test planning -> test generation -> test integration -> test running really a matter of few simple clicks enhancing developer experience.&#x20;

#### Installing the cli&#x20;

```
pip3 install momentum-cli
```

#### Setting up the cli

Once the CLI is installed, for you to use it - there are some steps you'd need to take. The first thing is running the command to initialise it.

```
momentum init
```

When you run this command, this will ask you for two inputs : \
\
**(a) Path of virtual env** : Please enter the absolute path of your created virtual env at this point, for example "./users/fatman/projects/momentum/.venv"\
\
**(b) Path of directory where you want the tests to be generated** : Please provide the absolute path for the directory where you want the tests to be stored and run from. Ideally this is a subfolder inside your codebase which is called something like "tests", but you can customise this. For example the path could look like : "/users/fatman/projects/momentum/tests"\
\
Once you provide these inputs, the cli will automatically setup everything else and run momentum for you to interact with (via momentum pro / enterprise).

#### Stopping the cli

```
momentum stop
```

When you're done with momentum, simply stop the cli with this command.

#### Reconfiguring the variables

In case you want to reconfigure your virtual env / test directory path - you can run the following command which should help you with that.&#x20;

```
momentum config
```

Once the reconfiguration is done, go ahead and run momentum with this command :&#x20;

```
momentum run
```

Once your cli is correctly configured and running, momentum (pro/enterprise) can connect and run, modify, regenerate, fix & verify tests with your codebase easily.
