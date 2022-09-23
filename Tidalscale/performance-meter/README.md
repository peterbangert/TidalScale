# Performance Meter

## Running Postgres locally

1. Pull and start container

```
docker pull postgres
docker run --name postgresql -e POSTGRES_PASSWORD=admin -d postgres
docker run --name postgresql -p 5432:5432 -e POSTGRES_PASSWORD=admin -d postgres
```

2. Login

```
psql -h localhost -U postgres
```

3. Execute Queries from Bash cmd line

```
export PGPASSWORD='admin'
psql -U postgres -d tidalscale -c 'select * from configurations;'

```
