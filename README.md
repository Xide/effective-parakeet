# Low-cost-kube

## Components

- Cluster autoscaler (external)
- [DrainIO](https://github.com/planetlabs/draino) or [k8s-spot-rescheduler](https://github.com/pusher/k8s-spot-rescheduler)
- [k8s-spot-termination-handler](https://github.com/pusher/k8s-spot-termination-handler) <- We might use DrainIO for this use case too,  we will need to disable sleep-time for this particular instance

## Price analysis

### price_analysis

Price comparaisons sandbox.
Explorations of tricks to pick instance with the best cost-efficiency.

As of now, absolute cost per vCPU and RAM have been considered :

1. Gather specs and spot pricing of all the sizings for selected types
2. Compute each instance (hourly price / resource unit) -> "efficiency"
3. Rank each instance type by efficiency for all the resources (vCPU, RAM)
4. Invert of the sum of an instance rank on all the resources gives an instance global "fitness" (the closest of 0, the better !)

TODO: weighted sum on the dimension rank depending on a defined workload.

```sh
pip install -r price_analysis/requirements.txt

# Tested on 3.7.3
python price_analysis/main.py
```

### Makefile

| Command | Usage |
| `make data/instance_types.txt` | List of AWS instances types and sizings referenced in the AWS Pricing API |
| `make data/locations.txt` | human friendly locations |
