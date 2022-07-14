# GKE Management HowTos

- Add More nodes to node pool

```
gcloud container clusters resize CLUSTER_NAME￼ \
    --node-pool POOL_NAME￼ \
    --num-nodes NUM_NODES
```