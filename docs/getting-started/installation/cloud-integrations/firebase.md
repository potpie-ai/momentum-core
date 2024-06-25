# Firebase

You will need a firebase project, add one from here : [https://console.firebase.google.com/](https://console.firebase.google.com/u/0/)

Once a project is created, do the following.\
\
1\.  Click on Project overview from the sidebar.\
2\. Open Service accounts tab. \
3\. You will see the option to generate a new private key in the firebase admin sdk sub-section. Click on that.\
4\. Read the warning, and then generate the key. Rename the downloaded key to - firebase\_service\_account.json and move it to server folder in the root of momentum source code. \


{% hint style="info" %}
Note: The file name 'firebase\_service\_account.json' is already part of .gitignore and should be safe to use. It never goes on git. But in case you loose it, you'll need a new one. So keep it secure and safe. (Repeating the warning that google gave you during key generation)&#x20;
{% endhint %}
