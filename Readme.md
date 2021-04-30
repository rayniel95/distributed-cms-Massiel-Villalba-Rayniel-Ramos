# About

The Distributed CMS was my final project in my Distributed Systems course. The
idea was implement a crash fault tolerant system, this is solved using a Chord
distributed hash table. I used the Chord original paper and modified some algorithms, for example, one adventage of my modified algorithms is that we only need one node for create a chord ring, of course, a problem with this is the high traffic in the network. I try to solve the partition network problem for two partitions saveing the new neighbors nodes in a special list and asking if the actual node is not in the ring of that neighbor, a very simple algorithm. Because the system is crash fault tolerant you can add new nodes, add data to the system, deleting node, but the data will be remain in the system (if it have at least one node).

## More

See in this repository:

- `cms-compartido.pdf`
- `chord.pdf`
- `1502.06461.pdf`

# Requirements

## Docker compose network

docker

docker-compose

## Kubernetes cluster

# How to execute

## Docker compose execution

Execute `sudo docker-compose up`

## Kubernetes cluster execution

# How to use

TODO - add images