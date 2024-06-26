# Setting up Github App

We need to enable login via github, for that, we will create a github app. To do that,

1. Visit this url : [https://github.com/settings/apps/new](https://github.com/settings/apps/new)
2. Name your app in context of momentum (suggestion) , can be anything - for example momentum-auth.
3. We need to give the app following permissions:\
   (a) Repository permissions - **Contents** (Read Only), **Metadata** (Read Only), **Pull Requests** (Read and write), **Secrets** (Read Only), **Webhook** (Read only)\
   (b) Organisation permissions - None\
   (c) Account permissions - **Email Address** (Read Only)
4. Generate a private key of your github app, once downloaded and add it to launch.json in GITHUB\_PRIVATE\_KEY, add your app id to GITHUB\_APP\_ID sections.
5. Now from the left sidebar , select install app, and install it next to your org/ user account.
