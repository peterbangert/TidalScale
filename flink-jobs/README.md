# Flink Jobs

> Directory containing Flink Stream processing applications and instructions how to package them

## Quick Start

- Visit any directory and run `mvn clean package`

- A fat `.jar` file should exist in the `/target` directory


## Docker Commands

1. Build Image

```
docker build -t eu.gcr.io/project-name/quickstart .

```

1. Push Image

```
docker push eu.gcr.io/project-name/quickstart

```

