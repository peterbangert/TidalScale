# Real Trace Traffic Generator


## Quick Start

1. Build container image

```
docker build -t eu.gcr.io/msc-thesis-354309/real-trace-generator .
```

2. Push to Google Container Registry

```
docker push eu.gcr.io/msc-thesis-354309/real-trace-generator
```

3. Deploy via k8s

```
kubectl apply -f real-trace-generator-deployment.yaml
```

4. Redeploy when new image is created/pushed

```
kubectl rollout restart deployment/real-trace-generator-deployment
```
