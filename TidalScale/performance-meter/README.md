# Performance Meter

## Running Postgres locally

1. Pull and start container

```
docker pull postgres
docker run --name postgresql -e postgres_PASSWORD=admin -d postgres
docker run --name postgresql -p 5432:5432 -e postgres_PASSWORD=admin -d postgres
```

2. Login

```
psql -h localhost -U postgres
```

3. Execute Queries from Bash cmd line

```
export PGPASSWORD='admin'
psql -h localhost -U postgres -d tidalscale -c 'select * from configurations  order by (taskmanagers, cpu);'

```

4. Export PG PAssword

```
export PGPASSWORD=admin
```


## Running Postgresql in Helm

PostgreSQL can be accessed via port 5432 on the following DNS names from within your cluster:

    my-postgresql.default.svc.cluster.local - Read/Write connection

To get the password for "postgres" run:

    export postgres_PASSWORD=$(kubectl get secret --namespace default my-postgresql -o jsonpath="{.data.postgres-password}" | base64 -d)

To connect to your database run the following command:

    kubectl run my-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:15.1.0-debian-11-r12 --env="PGPASSWORD=$postgres_PASSWORD" \
      --command -- psql --host my-postgresql -U postgres -d postgres -p 5432

    > NOTE: If you access the container using bash, make sure that you execute "/opt/bitnami/scripts/postgresql/entrypoint.sh /bin/bash" in order to avoid the error "psql: local user with ID 1001} does not exist"

To connect to your database from outside the cluster execute the following commands:

    kubectl port-forward --namespace default svc/my-postgresql 5432:5432 &
    PGPASSWORD="$postgres_PASSWORD" psql --host 127.0.0.1 -U postgres -d postgres -p 5432
