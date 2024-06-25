# Setting up database via docker

Now that you have the momentum repo cloned and the requirements installed in your activated virtual enviorment, you'll need to setup the required databases.

For the sake of making it easier and providing a standard / tested way of doing it - we have added a docker-compose in the momentum repo.

Do the following in the momentum repo / directory&#x20;

```
docker-compose up
```

This should bring up sandboxed postgresql and neo4j for you - with default username and passwords.
