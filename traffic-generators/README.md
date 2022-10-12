# Traffic Generators

> Simulators for creating accurate real time data sources

## Quick Start

1. Deploy [real-trace-generator](./real-trace-generator/)

```
cd real-trace-generator
make deploy
```

## Description

The three currently available traffic generators serve different formats of data and therefore require different flink-jobs to be deployed. 

The real-trace-generator varies from the aforementioned traffic generators in that it can be configured to produce any format of data, given that it is provided in a readable file format, and can produce this data at any rate, given that a trace file of the desired production rate is given in CSV format with <timestamp, int> as the proper format.
