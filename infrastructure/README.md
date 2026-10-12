# RootPilot Test Infrastructure

RootPilot uses the OpenTelemetry Demo as a third-party
microservices application for generating realistic
observability data.

## Upstream Project

Repository:
https://github.com/open-telemetry/opentelemetry-demo

The OpenTelemetry Demo is maintained by the
OpenTelemetry community.

RootPilot does not claim ownership of this project.

## Purpose

The demo provides:

- Distributed microservices
- Application logs
- Metrics
- Distributed traces
- Realistic service dependencies

RootPilot uses this telemetry to investigate
operational incidents.

## Deployment

The demo is deployed separately on a VM.

RootPilot accesses OpenSearch and Prometheus
through configured endpoints.