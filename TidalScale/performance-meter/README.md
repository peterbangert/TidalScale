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

1. PostgreSQL can be accessed via port 5432 on the following DNS names from within your cluster:

```
my-postgresql.default.svc.cluster.local - Read/Write connection
```

2. To get the password for "postgres" run:

```
export PGPASSWORD=$(kubectl get secret --namespace default tidalscale-postgresql -o jsonpath="{.data.postgres-password}" | base64 -d)
```

3. Connect to database from outside the cluster:

```    
kubectl port-forward --namespace default svc/tidalscale-postgresql 5432:5432
```

4. Drop and Restore table

```
psql --host localhost -U postgres -d postgres -p 5432 -d tidalscale -c 'drop table configurations;'; psql --host localhost -U postgres -d postgres -p 5432 -d tidalscale < pg_backup/221222_17-07-25_backup.psql
```
