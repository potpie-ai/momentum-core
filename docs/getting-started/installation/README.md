# Installation

**Step 1: Clone the Repository**

First, clone our repository to your local machine using Git:

```bash
git clone https://github.com/getmomentum/momentum-core
cd momentum-core
```

**Step 2: Create a virutal enviorment**

We strongly recommend running the app in a virtual enviorment, if you want to have a look at multiple reasons of why that is the case, read this [reddit](https://www.reddit.com/r/learnpython/comments/15nuehj/why\_do\_i\_need\_a\_virtual\_environment/) thread.

How to create virtual enviorment

```
python3 -m venv venv
```

And activate it

```
source venv/bin/activate
```

If you replace the venv with any other folder name, please add it in .gitignore

**Step 3: Install the dependencies from requirements**

```
pip install requirements.txt
```

If you face any challenges here, check out [known-bugs-and-fixes.md](../known-bugs-and-fixes.md "mention") and [troubleshooting-and-feedback.md](../../introduction-to-momentum/troubleshooting-and-feedback.md "mention")
