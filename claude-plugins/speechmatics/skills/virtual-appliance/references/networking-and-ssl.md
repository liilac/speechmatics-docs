# Networking and SSL

Docs:

- https://docs.speechmatics.com/deployments/virtual-appliance/installation/network-config
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/networking
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/ssl-configuration
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/security#ports-and-protocols

## Contents

- [Network requirements](#network-requirements)
- [Firewall ports](#firewall-ports)
- [Network interface mapping](#network-interface-mapping)
- [IP configuration](#ip-configuration)
- [Proxies](#proxies)
- [HTTPS defaults](#https-defaults)
- [Use your own certificate](#use-your-own-certificate)
- [Disable HTTP access](#disable-http-access)
- [Reset SSL settings](#reset-ssl-settings)
- [Reset a forgotten admin password](#reset-a-forgotten-admin-password)
- [TLS versions and cipher suites](#tls-versions-and-cipher-suites)

## Network requirements

The appliance uses the k3s default subnets (https://docs.k3s.io/cli/server#networking):

| Setting | Value | Use |
| --- | --- | --- |
| `cluster-cidr` | `10.42.0.0/16` | Pod IPs |
| `service-cidr` | `10.43.0.0/16` | Service IPs |

Make sure your network has no IP address conflict with these ranges.

## Firewall ports

| Port/Protocol | Description |
| --- | --- |
| 22/TCP | SSH access |
| 80/TCP | Management API, and submitting jobs (jobs service is `batch` mode only) |
| 443/TCP | HTTPS for the above services |
| 9000/TCP | WebSocket connection to the Realtime transcription service (`realtime` mode only) |
| 9004/TCP | Secure WebSocket connection to the Realtime transcription service (`realtime` mode only) |
| 9001/TCP | Prometheus metrics |
| 3100/TCP | Loki logs endpoint |

With HTTPS set up, expose only port 443 for `batch` mode, and ports 443 and 9004 for `realtime` mode.

The docs table has its two footnotes swapped: the jobs row carries "Websocket service only available in `realtime` mode" and the WebSocket rows carry "Jobs service only available in `batch` mode". The table above uses the evident intent.

For a static IP, the administration page points to the Ubuntu manual network docs, while the installation page gives the netplan steps in [IP configuration](#ip-configuration).

The appliance has its own firewall that allows ingress only to the ports required for its Management, Monitoring and Speech APIs.

## Network interface mapping

While the appliance is powered off, map the virtual network adapter to the physical host adapter on which the appliance will be contacted.

### VMware ESXi

Nothing to configure. The network specified at import is used.

### VMware Workstation

Use bridged network mode, so the VM gets an IP address independent of the host:

1. Open VMware Workstation.
2. Right-click the appliance, for example `SM_App_01`, and select `Settings...`.
3. Select `Network Adapter` in the devices list.
4. Select `Bridged: Connected directly to the physical network`.
5. Click `OK`.

If networking performance is poor:

1. Select `Edit` -> `Virtual Network Editor...`.
2. Select `Change Settings`.
3. Select the network whose `Type` is `Bridged`.
4. In `VMnet Information`, set `Bridged to:` to a specific interface instead of `Automatic`.

### Proxmox VE

The import creates no network adapter. Add one before first boot:

```bash
qm set 123 --net0 model=virtio,bridge=vmbr0,firewall=1
```

## IP configuration

The appliance acquires an IP address with DHCP by default. For a static address, choose one of three methods.

### Manually specify the network configuration

Get terminal access through the console or SSH. Find the interface name:

```
$ ip link show | grep 'en.*:'
2: ens256: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
```

The interface here is `ens256`. It varies by hypervisor. Run the remaining commands as root:

```
sudo -i
```

Delete the cloud-init generated network config, if present:

```
rm -vf /etc/netplan/50-cloud-init.yaml
```

Stop cloud-init managing the network configuration, so the deleted file does not return at next boot:

```
echo 'network: {config: disabled}' > /etc/cloud/cloud.cfg.d/99_disable_network.cfg
```

Create `/etc/netplan/99-static.yaml`:

```yaml
network:
  version: 2
  ethernets:
    ens256:  # This MUST match the interface name you found earlier
      addresses:
        - 192.168.1.202/24  # Set your desired ip and subnet
      routes:
        - to: default
          via: 192.168.1.1  # Set your desired default gateway
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]  # A list of your desired dns servers
```

Reboot:

```
reboot
```

More detail: [Ubuntu network configuration](https://ubuntu.com/server/docs/configuring-networks), [Netplan YAML reference](https://netplan.readthedocs.io/en/latest/netplan-yaml/).

### Use cloud-init

Pass the netplan config above to the appliance boot process with cloud-init, so it applies at startup with no manual steps. The method depends on the hypervisor:

- [Cloud-init network config v2](https://cloudinit.readthedocs.io/en/latest/reference/network-config-format-v2.html)
- [VMware ESXi](https://knowledge.broadcom.com/external/article/311895/how-to-customize-virtual-machine-using-c.html)
- [Proxmox](https://pve.proxmox.com/wiki/Cloud-Init_Support)

### Use a DHCP reservation

A DHCP reservation gives a fixed address without changing the appliance. Get the MAC address of the primary interface from the hypervisor, or from the appliance:

```
$ ip link show | grep -A 1 'en.*:'
2: ens256: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 00:50:56:b9:4e:e4 brd ff:ff:ff:ff:ff:ff
```

Here the MAC address is `00:50:56:b9:4e:e4`. Create the reservation as your DHCP vendor documents.

## Proxies

If the appliance has no direct route to the internet, use a proxy server to reach the cloud-based usage reporting service. Set it with the `usagereporting` endpoint. See [licensing.md](licensing.md#use-a-proxy-server).

## HTTPS defaults

- The appliance allows HTTP by default: port 80 for the Management API and 9001 for the Monitoring API.
- Since appliance version 3.4.0, the same services are available over HTTPS on port 443. Change `http` to `https` and remove the port from the URL.
- The imported appliance contains a default self-signed certificate created by Speechmatics, not signed by any Certificate Authority (CA). Replace it with a certificate signed by your organization or a trusted third-party CA.

Management API over HTTP, then HTTPS:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/host/about"

curl -sSL -u admin:admin -X 'GET' \
  "https://${APPLIANCE_HOST}/v2/management/host/about"
```

With a self-signed certificate, curl reports:

```
curl: (60) SSL certificate problem: self signed certificate
```

Add `--insecure` to trust the self-signed certificate. Stop using it once you upload your own certificate and your system trusts it.

Jobs API over HTTPS:

```bash
curl --insecure -L -X 'GET' "https://${APPLIANCE_HOST}/v2/jobs/"
```

Secure WebSocket, using the Speechmatics Python client:

```bash
speechmatics transcribe --lang en ${PATH_TO_AUDIO_FILE} --url "wss://${APPLIANCE_HOST}:9004/v2/en" --ssl-mode insecure
```

## Use your own certificate

Upload both the certificate file and its private key file.

Private key:

- Normally has a `.key` extension.
- Looks like `-----BEGIN RSA PRIVATE KEY----- ... -----END RSA PRIVATE KEY-----`.
- Encrypted or password protected private key files are not supported.

Certificate:

- PEM encoded, normally with a `.crt` or `.pem` extension.
- Looks like `-----BEGIN CERTIFICATE----- ... -----END CERTIFICATE-----`.

Both files should be in PKCS8 format. For a certificate chain, concatenate the individual certificates in one file with your organization's certificate first.

### Upload

POST to `/v2/security/sslcertificate` with form fields `keyfile` and `certfile`:

```bash
curl --insecure -L -u admin:$PWD -X 'POST' "https://${APPLIANCE_HOST}/v2/security/sslcertificate" \
    -F "keyfile=@appliance.key" -F "certfile=@appliance.crt"
```

- Never upload these files over HTTP: you risk leaking the private key.
- A successful upload returns HTTP 200.
- The upload reconfigures the Kubernetes ingress, which takes around five seconds. Requests are still served with the old certificate during that time. Existing connections such as job uploads or WebSocket streams are not interrupted.
- The upload is also available in the Management web interface.

Check the certificate:

```bash
openssl s_client -connect ${APPLIANCE_HOST}:443
```

## Disable HTTP access

POST `{"enable_insecure_ports": false}` to `/v2/security/insecureports`. HTTP requests are then redirected to HTTPS:

```bash
curl -sSL -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/security/insecureports" \
  -H "Content-Type: application/json" \
  -d '{"enable_insecure_ports": false}'
```

A successful request returns HTTP 200. The web server takes around five seconds to restart. Afterwards:

```
curl -X 'GET' "http://${APPLIANCE_HOST}/v2/management/host/about"
< HTTP/1.1 301 Moved Permanently
< Location: https://${APPLIANCE_HOST}/v2/management/host/about
```

## Reset SSL settings

A DELETE to `/v2/security/reset` returns the appliance to the Speechmatics self-signed certificate and deletes any configured admin password. If HTTP access is disabled, you need the existing admin password:

```bash
curl -L -u "admin:$PWD" -X 'DELETE' "http://${APPLIANCE_HOST}/v2/security/reset"
```

## Reset a forgotten admin password

If you forgot the admin password and disabled HTTP access, you cannot reach the appliance over HTTP or HTTPS. Reset the password from the appliance console (through the hypervisor) or SSH:

```bash
# This command will open the vi editor
kubectl edit secret management-auth-secret
# Replace the line
# users: <base64 hash of the forgotten password>
# with
# users: YWRtaW46JDJ5JDA1JFExeFBVUFJyRG96LzQwWEZuN09aVHVtV1dzallUeWlhOHo1ZUkvWHpHRUhSUng0dXRyM2UyCg==

# Restart the management-api service
kubectl rollout restart deployment/management-api
```

This value resets the password to `admin`.

Setting the admin password is covered in [services-and-security.md](services-and-security.md#management-api-authentication).

## TLS versions and cipher suites

TLS 1.2 and TLS 1.3 are supported. Earlier TLS and SSL versions are not.

TLS 1.3 cipher suites, in server preferred order:

- `TLS_AES_128_GCM_SHA256`
- `TLS_AES_256_GCM_SHA384`
- `TLS_CHACHA20_POLY1305_SHA256`

Strong TLS 1.2 cipher suites, in server preferred order:

- `TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256`
- `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`
- `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`

Other TLS 1.2 cipher suites are available but considered weak. Select one of the suites above.
