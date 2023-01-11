# GKE Management HowTos

- Add More nodes to node pool

```
gcloud container clusters resize CLUSTER_NAME￼ \
    --node-pool POOL_NAME￼ \
    --num-nodes NUM_NODES
```

# Initial Setup

1. Setup a project in google cloud console

2. Enable a billing account to it 

3. Enable APIs 

4. Enable Google Compute Engine API

5. delete key.json if exists

6. enable gcloud container registry
