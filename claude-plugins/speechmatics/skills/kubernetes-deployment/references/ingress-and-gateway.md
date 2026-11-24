# Ingress, Gateway API and request IDs

Docs: https://docs.speechmatics.com/deployments/kubernetes/prerequisites#ingress-setup

The chart exposes `proxy-service`, the entry point for Realtime sessions, through either Gateway API or a Kubernetes `Ingress`. Configure one. The gateway or ingress controller must support WebSocket connections.

For new deployments use Gateway API. It is the successor to `Ingress`, and the `ingress-nginx` controller that the default chart values target is retired.

## Contents

- Gateway API with NGINX Gateway Fabric
- ListenerSet
- Preventing session loss during gateway upgrades
- ingress-nginx
- Other ingress controllers
- Request ID

## Gateway API (recommended)

The chart creates an `HTTPRoute` for `proxy-service`. You need:

- Gateway API CRDs (v1 or later) on the cluster
- A gateway controller, for example [NGINX Gateway Fabric](https://docs.nginx.com/nginx-gateway-fabric/)
- A `Gateway` resource. The chart does not create it; manage it separately

### Set up NGINX Gateway Fabric

Skip if you already run a gateway controller.

1. Install the Gateway API CRDs:

```bash
kubectl kustomize "https://github.com/nginx/nginx-gateway-fabric/config/crd/gateway-api/standard?ref=v2.8.1" | kubectl apply -f -
```

2. Create `ngf.values.yaml`:

```yaml
nginxGateway:
  snippets:
    # Needed for the SnippetsPolicy that keeps sessions alive during upgrades
    enable: true

nginx:
  service:
    # This is needed to preserve the source IP of the client
    externalTrafficPolicy: Local

  pod:
    # Used to prevent nginx pods being terminated for 24h while there are active sessions
    terminationGracePeriodSeconds: 86400
```

3. Install the NGINX Gateway Fabric chart:

```bash
helm install ngf oci://ghcr.io/nginx/charts/nginx-gateway-fabric \
  --version 2.8.1 \
  --create-namespace -n nginx-gateway \
  -f ngf.values.yaml
```

4. Create a `Gateway` with an HTTPS listener, and a `SnippetsPolicy` that lets active sessions finish when nginx reloads or shuts down. The TLS secret must be in the same namespace as the `Gateway`. Save as `gateway.yaml` and apply:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: my-gateway
  namespace: nginx-gateway
spec:
  gatewayClassName: nginx
  listeners:
    - name: https
      port: 443
      protocol: HTTPS
      hostname: speechmatics.example.com
      tls:
        mode: Terminate
        certificateRefs:
          - kind: Secret
            name: tls-secret
      allowedRoutes:
        namespaces:
          from: All
---
apiVersion: gateway.nginx.org/v1alpha1
kind: SnippetsPolicy
metadata:
  name: graceful-shutdown
  namespace: nginx-gateway
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: Gateway
      name: my-gateway
  snippets:
    # This prevents nginx worker processes from shutting down for 24h in case of active sessions
    - context: main
      value: worker_shutdown_timeout 86400s;
```

With another gateway controller, set `gatewayClassName` to its class.

### Enable the HTTPRoute in the chart

Disable the default `Ingress` and enable the `HTTPRoute`. Set `parentRefs` to the `Gateway` that serves traffic for the route:

```yaml
proxy:
  ingress:
    # Disable the default Ingress
    enabled: false

  httproute:
    enabled: true

    # Hostname to match
    hostname: speechmatics.example.com

    # Gateway that accepts traffic for this route
    parentRefs:
      - name: my-gateway
        namespace: nginx-gateway
        sectionName: https
```

## ListenerSet

Instead of declaring the proxy listener on a shared `Gateway`, the chart can create a [`ListenerSet`](https://gateway-api.sigs.k8s.io/geps/gep-1713/) that attaches its own HTTPS listener and TLS configuration to the `Gateway`.

- Requires a Gateway API version and gateway controller that support `ListenerSet`.
- `ListenerSet` is in the Gateway API experimental channel. With the NGINX Gateway Fabric steps above, install the CRDs from `experimental` instead of `standard`.
- TLS secrets referenced by a listener must be in the same namespace as the `ListenerSet`.

```yaml
proxy:
  ingress:
    enabled: false

  httproute:
    enabled: true
    hostname: speechmatics.example.com
    parentRefs:
      # Attach the route to the ListenerSet created by the chart
      - group: gateway.networking.k8s.io
        kind: ListenerSet
        name: proxy
        sectionName: https

  listenerset:
    enabled: true
    parentRef:
      group: gateway.networking.k8s.io
      kind: Gateway
      name: my-gateway
      namespace: nginx-gateway
    listeners:
      https:
        port: 443
        protocol: HTTPS
        hostname: speechmatics.example.com
        tls:
          mode: Terminate
          certificateRefs:
            - group: ""
              kind: Secret
              name: tls-secret
        allowedRoutes:
          namespaces:
            from: Same
```

## Preventing session loss during gateway upgrades

Restarting the gateway data plane pods, or reloading their configuration, ends active WebSocket sessions. The NGINX Gateway Fabric steps above handle this. With another gateway controller, configure graceful shutdown on the data plane:

- Set the nginx `worker_shutdown_timeout` directive, or the equivalent for your controller.
- Set a `preStop` lifecycle hook and `terminationGracePeriodSeconds` on the data plane pods to match your maximum session duration.

## ingress-nginx

By default the chart creates a Kubernetes `Ingress` for `proxy-service` with `ingressClassName: nginx`. The default values are written for the [`ingress-nginx`](https://kubernetes.github.io/ingress-nginx/) controller.

`ingress-nginx` is retired. Maintenance ended in March 2026, and the project no longer publishes releases, bug fixes or security patches. Existing installations keep working. For new deployments use Gateway API.

If you are not already running `ingress-nginx`:

1. Create `nginx.values.yaml`:

```yaml
controller:
  service:
    # This is needed to preserve the source IP of the client
    # See: https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/#preserving-the-client-source-ip
    externalTrafficPolicy: Local

    # This should be set to the IP address used to access services on your cluster
    loadBalancerIP: $CLUSTER_INGRESS_IP

  config:
    # This prevents nginx worker process from shutting down for 24h in case of active sessions
    worker-shutdown-timeout: 86400s

  extraArgs:
    # Needed to support annotations added by the chart ingresses
    annotations-prefix: nginx.ingress.kubernetes.io

    # This prevents nginx main process from shutting down for 24h in case of active sessions
    shutdown-grace-period: 86400

  # Used to prevent nginx pods being terminated for 24h while there are active sessions
  terminationGracePeriodSeconds: 86400
```

2. Install the chart:

```bash
helm repo add nginx https://kubernetes.github.io/ingress-nginx
helm install nginx nginx/ingress-nginx --version 4.15.1 -f nginx.values.yaml
```

Then set the hostname in the Speechmatics chart values:

```yaml
proxy:
  ingress:
    hostname: speechmatics.example.com
```

## Other ingress controllers

Any ingress controller that supports WebSocket connections works. Set `proxy.ingress.ingressClassName` to its ingress class:

```yaml
proxy:
  ingress:
    ingressClassName: my-ingress-class
```

- The default `proxy.ingress.annotations` are specific to `ingress-nginx`. Add any annotations your controller needs.
- The default `proxy.ingress.path` is a regular expression. Enable regular expression path matching on your controller, or set a path it supports.
- Sessions require no additional request headers.

## Request ID

Each session is tagged with a request ID. It appears in the `proxy-service` logs and traces a session across components.

- If the incoming request has an `X-Request-Id` header, `proxy-service` uses it.
- Otherwise `proxy-service` generates a random request ID.

Request ID headers are optional. To correlate sessions with gateway or ingress logs, have the controller set `X-Request-Id` on the request. To let clients see the ID, for example to quote it when reporting an issue, have the controller return it in a `Request-Id` response header.

### NGINX Gateway Fabric

Set and return the request ID with `filters` on the `HTTPRoute`:

```yaml
proxy:
  httproute:
    filters:
      # Pass the gateway-generated request ID to proxy-service
      - type: RequestHeaderModifier
        requestHeaderModifier:
          set:
            - name: X-Request-Id
              value: $request_id
      # Return the request ID in the response, so the client can see it
      - type: ResponseHeaderModifier
        responseHeaderModifier:
          add:
            - name: Request-Id
              value: $request_id
```

The `$request_id` variable is specific to NGINX Gateway Fabric. For other gateway controllers, refer to the controller's documentation.

### ingress-nginx

Add the `Request-Id` response header with a snippet annotation:

```yaml
proxy:
  ingress:
    annotations:
      nginx.ingress.kubernetes.io/use-regex: "true"
      # Add the request ID to the response, so the client can see it
      nginx.ingress.kubernetes.io/configuration-snippet: |+
        more_set_headers "Request-Id: $req_id";
```

Snippet annotations must be enabled on `ingress-nginx`, otherwise it rejects the `Ingress`. From controller version 1.12, `configuration-snippet` is also classed as a `Critical` risk annotation, so the annotation risk level must be raised. Add to `nginx.values.yaml`:

```yaml
controller:
  allowSnippetAnnotations: true
  config:
    annotations-risk-level: Critical
```

Check both settings on the cluster:

```bash
# No output means the defaults apply: snippets disabled and risk level High
kubectl get cm -o yaml -l app.kubernetes.io/instance=nginx | grep -E 'allow-snippet-annotations|annotations-risk-level'
```

From chart 1.5.0 the default `Ingress` no longer adds a `Request-Id` response header, so `ingress-nginx` no longer needs snippet annotations enabled unless you add the header as above.
