# Installation

Docs:

- https://docs.speechmatics.com/deployments/virtual-appliance/installation/system-requirements
- https://docs.speechmatics.com/deployments/virtual-appliance/installation/download-and-import
- https://docs.speechmatics.com/deployments/virtual-appliance/installation/verify-and-go
- https://docs.speechmatics.com/deployments (feature availability by deployment)

## Contents

- [Supported hypervisors](#supported-hypervisors)
- [Batch appliance requirements](#batch-appliance-requirements)
- [Realtime appliance requirements](#realtime-appliance-requirements)
- [IOPS](#iops)
- [Host requirements](#host-requirements)
- [Download the OVA](#download-the-ova)
- [Default SSH credentials](#default-ssh-credentials)
- [VMware vSphere/ESXi](#vmware-vsphereesxi)
- [VMware Workstation](#vmware-workstation)
- [Amazon Web Services](#amazon-web-services)
- [Proxmox VE](#proxmox-ve)
- [Verify the appliance](#verify-the-appliance)
- [Feature availability on-prem](#feature-availability-on-prem)

## Supported hypervisors

- VMware ESXi v7.0 and greater
- VMware Workstation v16.0 and greater. It does not support PCI passthrough, so only CPU transcription is possible.
- AWS EC2
- Proxmox VE v8.0 and greater

## Batch appliance requirements

### CPU transcription

Minimum:

- 2 vCPUs
- 8GB RAM
- Up to 170GB hard disk space

Additional resources for each concurrent input stream, Standard model:

| Scaling mode | CPU | Memory (GB) |
| --- | --- | --- |
| `simple` | 1.0 | 1.60 - 2.00 |
| `adaptive` | 4.0 | 3.90 - 4.80 |

Enhanced model:

| Scaling mode | CPU | Memory (GB) |
| --- | --- | --- |
| `simple` | 1.0 | 2.10 - 2.30 |
| `adaptive` | 4.0 | 5.00 - 5.50 |

### GPU transcription

Minimum, enough to run at least one worker with the Standard or Enhanced model:

- 8 vCPUs
- 32GB RAM
- Up to 200GB hard disk space

Additional resources for each concurrent input stream, Standard model:

| Scaling mode | CPU | Memory (GB) |
| --- | --- | --- |
| `simple` | 0.9 - 1.3 | 1.30 - 1.80 |
| `adaptive` | 2.9 - 3.6 | 2.60 - 3.60 |

Enhanced model:

| Scaling mode | CPU | Memory (GB) |
| --- | --- | --- |
| `simple` | 0.8 - 1.1 | 2.70 - 3.60 |
| `adaptive` | 2.3 - 3.1 | 3.00 - 5.00 |

### Recommended

- 16 vCPUs
- 32GB RAM

A larger machine running more jobs in parallel gives more throughput, but several machines of the recommended size can suit some use cases better.

## Realtime appliance requirements

The Realtime appliance is in early access. CPU transcription is not supported.

GPU transcription minimum, enough to run at least one worker with the Standard or Enhanced model:

- 8 vCPUs
- 16GB RAM
- Up to 100GB hard disk space

Each additional input stream needs up to 0.2 vCPUs and 200MB of memory.

Recommended, which allows maximum GPU throughput on standard or enhanced:

- 16 vCPUs
- 32GB RAM
- Up to 100GB hard disk space

## IOPS

- Heavy use at scale can cause very high IO usage. If so, raise the maximum IOPS to between 8,000 and 12,000. This can help when you run more than 10 concurrent workers.
- Upgrade the root disk first. With even more workers, also upgrade the jobs disk.
- Higher IOPS costs more. On AWS, always set the volume type to `gp3`: it costs less and performs better than `gp2`.
- Low IOPS lengthens startup. If IOPS is too low, the first few transcription requests on a fresh VM may fail.
- Consider raising IOPS when you use close to the maximum number of workers for the appliance size, or when jobs are all long files with diarization.

Vendor guides: [AWS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/requesting-ebs-volume-modifications.html), [Microsoft Azure](https://docs.microsoft.com/en-us/azure/virtual-machines/disks-performance-tiers-portal), [VMware](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.resmgmt.doc/GUID-25C3D9FE-3A9D-4739-AC75-16A9E0A3D9F0.html).

## Host requirements

CPU:

- Use an AMD or Intel CPU with modern AVX instructions. The effect on speed varies by brand, generation, instruction sets, and resource allocation.
- Pass all AVX related instruction sets through to the VM.
- Allocate reserved memory and processors from the hypervisor to the appliance VM.

GPU: the same requirements as the GPU Speech to Text container. See `speechmatics:container-deployment` and https://docs.speechmatics.com/deployments/container/gpu-speech-to-text#system-requirements. Because the OVA is self-contained, consider only GPU memory, the driver version on the host, and the CUDA capability level.

### Host CPU info

```bash
curl -L -u admin:admin -X 'GET' "https://${APPLIANCE_HOST}/v2/management/cpuinfo"
```

```json
{
  "usage_percentage": 2.5,
  "architecture": "X86_64",
  "model_name": "Intel(R) Xeon(R) Silver 4116 CPU @ 2.10GHz",
  "cpus": "2",
  "vendor": "GenuineIntel",
  "hyperthreading": false,
  "flags": "3dnowprefetch abm adx aes apic arat arch_capabilities arch_perfmon avx avx2 avx512_vnni bmi1 bmi2 ..."
}
```

`flags` lists the instruction sets passed through by the hypervisor. Check for `avx` and `avx2`.

### Hypervisor guidance

- VMware: see "Performance Best Practices for VMware vSphere 7.0" and [Broadcom support](https://support.broadcom.com).
- Amazon EC2: [VM import guide](https://docs.aws.amazon.com/vm-import/latest/userguide/vmimport-image-import.html).
- Proxmox VE: [docs](https://pve.proxmox.com/pve-docs/).

## Download the OVA

Appliances are distributed as Open Virtual Appliance (OVA) files. An OVA is a tar archive holding the virtual disk images and a description of the VM.

1. Sign in to the [Support Portal](https://support.speechmatics.com). An account is required. If you have no account, or the virtual appliance section is not visible, contact Support.
2. Open the knowledge base and pick the area for the mode you need: `Batch` or `Realtime`.
3. Select the version, then the download link. The result is a file with an `.ova` extension.

## Default SSH credentials

The appliance accepts SSH with username `smadmin` and password `changeme`. Do one of:

- Disable password access and set up [SSH key access](https://help.ubuntu.com/community/SSH/OpenSSH/Keys).
- Block access to port 22.

## VMware vSphere/ESXi

The ESXi host web interface supports OVA/OVF import but is not recommended because of its file size limitations. The vCenter Server web interface is better, especially since 8.0 U1. [OVF Tool](https://developer.broadcom.com/tools/open-virtualization-format-ovf-tool/latest) gives the best results.

Install the OVF Tool binary for your operating system and vSphere version, then open a terminal in the directory holding the OVA. Use a fast network connection between the client and the vSphere machine.

Standalone ESXi host, with `USERNAME`, `PASSWORD` and `ESXI_HOST` set in advance:

```bash
ovftool --name=sm-appliance --datastore=datastore1 ./sm-batch-appliance-6.0.0-1214243.ova "vi://${USERNAME}:${PASSWORD}@${ESXI_HOST}"
```

vCenter Server Appliance:

```bash
ovftool --name=sm-appliance --datastore=tmp_LUN --vmFolder=testing ./sm-batch-appliance-6.0.0-1214243.ova "vi://${VC_USERNAME}:${VC_PASSWORD}@${VC_SERVER}/London/host/general-compute/"
```

The exact command varies with your vSphere environment. See the official OVF Tool user guide.

For GPU transcription, follow the [Broadcom passthrough guide](https://knowledge.broadcom.com/external/article?legacyId=1010789).

Network: nothing to configure. The network given at import is used.

## VMware Workstation

1. Open VMware Workstation.
2. Click `File` -> `Open`.
3. Navigate to the `.ova` file and click `Open`.
4. Name the VM, for example `sm-appliance-01`.
5. Click `Import`.

Then:

- Set bridged networking. See [networking-and-ssl.md](networking-and-ssl.md#vmware-workstation).
- Set CPU and memory for your workload before booting.
- On a Windows host, launch VMware Workstation with `Run as administrator` for best performance.
- Only CPU transcription is possible.

## Amazon Web Services

Import the OVA as an Amazon Machine Image (AMI) with AWS VM Import/Export, then launch instances from it. Full AWS process: https://docs.aws.amazon.com/vm-import/latest/userguide/vmimport-image-import.html

Prerequisite: the [AWS CLI](https://aws.amazon.com/cli/), configured as in its Getting Started guide.

### 1. Upload the OVA to S3

Use a bucket in the region where you want the AMI. Use S3 multipart upload because the OVA is large. Options:

- AWS SDKs that support multipart upload: Java, .NET, PHP, Python (Boto), Ruby, or the Multipart Upload API directly.
- UI tools such as S3 Browser or CloudBerry S3 Explorer.

### 2. Create the import service role

`trust-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": { "Service": "vmie.amazonaws.com" },
        "Action": "sts:AssumeRole",
        "Condition": {
          "StringEquals": {
            "sts:Externalid": "vmimport"
          }
        }
      }
    ]
}
```

```bash
aws iam create-role --role-name vmimport --assume-role-policy-document file://trust-policy.json
```

Keep the `file://` prefix on the filename.

### 3. Attach the role policy

`role-policy.json`. Replace `ova-bucket` with your bucket name:

```json
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetBucketLocation", "s3:GetObject", "s3:ListBucket"],
        "Resource": ["arn:aws:s3:::ova-bucket", "arn:aws:s3:::ova-bucket/*"]
      },
      {
        "Effect": "Allow",
        "Action": [
          "ec2:ModifySnapshotAttribute",
          "ec2:CopySnapshot",
          "ec2:RegisterImage",
          "ec2:Describe*"
        ],
        "Resource": "*"
      }
    ]
}
```

```bash
aws iam put-role-policy --role-name vmimport --policy-name vmimport --policy-document file://role-policy.json
```

### 4. Import the OVA

`containers.json`. Replace `ova-bucket` with your bucket name and `example-virtual-appliance.ova` with the OVA file name (for example `batch-appliance-<version>-maxi-<build-number>.ova` or `rt-appliance-<version>-maxi-<build-number>.ova`):

```json
[
    {
      "Description": "Virtual Appliance OVA",
      "Format": "ova",
      "UserBucket": {
        "S3Bucket": "ova-bucket",
        "S3Key": "example-virtual-appliance.ova"
      }
    }
]
```

```bash
aws ec2 import-image --description "Virtual Appliance OVA" --disk-containers file://containers.json
```

The output includes an `ImportTaskId`. Check the task:

```bash
aws ec2 describe-import-image-tasks --import-task-ids import-ami-abcd1234
```

The AMI is ready when the status is `completed`.

### 5. Security group

Open the ports listed in [networking-and-ssl.md](networking-and-ssl.md#firewall-ports). With HTTPS set up on a Batch appliance, expose only port 443. See the [AWS security groups documentation](https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_SecurityGroups.html).

### 6. Launch

1. In the AWS console, find the image under **EC2 Service | Images**.
2. Right-click the image and choose **Launch**.
3. Choose an instance type that meets the system requirements.
4. Choose **Review and Launch**, set up the key pair if required, and choose **Launch** again.

## Proxmox VE

Proxmox does not import OVA files directly. It imports the Open Virtualization Format (OVF) file contained in the OVA.

Prerequisites:

- The OVA and its sha512 checksum from the Support Portal.
- Web GUI access to the Proxmox VE server.
- Terminal access to run `qm`.

### Validate and extract

Copy the OVA and checksum into a new directory on the Proxmox server. You need free disk space of at least twice the OVA size. If the server lacks space, store the files remotely and mount them, for example with an NFS share or an sshfs mount.

```
root@pve:/mnt/sshfs/1214243# sha512sum -c sm-batch-appliance-6.0.0-1214243.ova.sha512.txt
sm-batch-appliance-6.0.0-1214243.ova: OK
```

```
root@pve:/mnt/sshfs/1214243# tar xfv sm-batch-appliance-6.0.0-1214243.ova --no-same-owner
sm-batch-appliance-6.0.0-1214243.ovf
sm-batch-appliance-6.0.0-1214243.mf
sm-batch-appliance-6.0.0-1214243-disk1.vmdk
sm-batch-appliance-6.0.0-1214243-disk2.vmdk
sm-batch-appliance-6.0.0-1214243-disk3.vmdk
sm-batch-appliance-6.0.0-1214243-file1.nvram
```

### Import the OVF

`123` is an example unused VM ID:

```
root@pve:/mnt/sshfs/1214243# qm importovf 123 sm-batch-appliance-6.0.0-1214243.ovf local-lvm --format qcow2
format 'qcow2' is not supported by the target storage - using 'raw' instead
  Logical volume "vm-123-disk-0" created.
transferred 0.0 B of 100.0 GiB (0.00%)
...
transferred 40.0 GiB of 40.0 GiB (100.00%)
```

The new VM is powered off. Before powering on, make these changes in the VM's `Hardware` tab or with `qm set`:

```bash
# High performance virtual SCSI controller
qm set 123 --scsihw virtio-scsi-single

# CPU type matching the host
qm set 123 --cpu host

# Network adapter (none is created by the import); adjust bridge and firewall
qm set 123 --net0 model=virtio,bridge=vmbr0,firewall=1

# Cores and memory (MiB); the default is 2 CPUs and 8GB RAM
qm set 123 -cores 6 -memory 24576
```

### GPU transcription on Proxmox

GPU transcription needs PCIe passthrough of a suitable graphics card. Use a q35 machine type with a UEFI BIOS:

```bash
qm set 123 -machine q35 -bios ovmf
```

In the web GUI, open the VM's `Hardware` tab, click `Add` -> `PCI Device`, and set:

- `Raw Device`: selected
- `Device`: the graphics card to use for transcription
- `All Functions`: ticked
- `Primary GPU`: not ticked
- `Advanced`: ticked
- `ROM-Bar`: ticked
- `PCI-Express`: ticked
- All `ID` boxes: left at `From Device`

Your hardware may need different values. See the [Proxmox PCI passthrough documentation](https://pve.proxmox.com/pve-docs/chapter-qm.html#qm_pci_passthrough).

### First boot on Proxmox

Open the `Console` page in the GUI and click `Start Now`. The login screen can take up to 4-5 minutes to appear.

The appliance does not ship with `qemu-guest-agent`, so the web GUI lists no IP addresses. Log in at the console with the default credentials and run:

```
smadmin@ubuntu:~$ ip addr show | grep -A 6 'en.*:'
2: ens18: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether bc:24:11:5c:d0:d6 brd ff:ff:ff:ff:ff:ff
    altname enp0s18
    inet 192.168.1.163/24 metric 100 brd 192.168.1.255 scope global dynamic ens18
       valid_lft 84651sec preferred_lft 84651sec
    inet6 fe80::be24:11ff:fe5c:d0d6/64 scope link
       valid_lft forever preferred_lft forever
```

Here the IP address is `192.168.1.163`. If no IP address is listed, or you want a static address, see [networking-and-ssl.md](networking-and-ssl.md#ip-configuration). If the command prints nothing, check that you added a network adapter, and run `ip addr show` on its own to debug.

With a GPU passed through, confirm the OS sees it:

```bash
sudo lshw -C display
nvidia-smi
```

## Verify the appliance

### Health endpoint

- Method: GET
- URL: `https://${APPLIANCE_HOST}/v2/management/health`

```bash
curl -X 'GET' "https://${APPLIANCE_HOST}/v2/management/health"
```

Realtime appliance example:

```json
{
  "status": "healthy",
  "database": { "status": "disabled" },
  "batch_inference": { "status": "disabled" },
  "monitoring": { "status": "healthy" },
  "storage": { "status": "healthy" },
  "realtime_inference": { "status": "healthy" },
  "gpu_inference": { "status": "healthy" }
}
```

Batch appliance example:

```json
{
  "status": "healthy",
  "database": { "status": "healthy" },
  "batch_inference": { "status": "healthy" },
  "monitoring": { "status": "healthy" },
  "storage": { "status": "healthy" },
  "realtime_inference": { "status": "disabled" },
  "gpu_inference": { "status": "disabled" }
}
```

| Field | Meaning |
| --- | --- |
| `status` | Overall appliance health |
| `database` | Internal jobs database |
| `batch_inference` | Batch inference service |
| `monitoring` | Monitoring services |
| `storage` | Mounted storage disks |
| `realtime_inference` | Realtime inference service |
| `gpu_inference` | GPU inference service, if enabled |

Components not required by the current configuration report `disabled`.

### Common health issues

Unhealthy Realtime inference:

```json
  "realtime_inference": {
    "status": "unhealthy",
    "errors": [
      "expected deployment: sm-transcriber-en to have 1 ready replicas have: 0"
    ]
  }
```

The transcriber needs a license before it can start. See [licensing.md](licensing.md).

Unhealthy storage: the expected disks must be mounted at the expected mount points for the mode.

| Mode | Mount points |
| --- | --- |
| `batch` | `/opt/speechmatics/jobs`, `/opt/speechmatics/monitoring` |
| `realtime` | `/opt/speechmatics/monitoring` |

### Batch smoke test

```bash
curl -s -L -X 'POST' \
   "http://${APPLIANCE_HOST}/v2/jobs/" \
   -F data_file=@{FILENAME} \
   -F 'config={ "type": "transcription",
         "transcription_config": { "language": "en" }
      }'
```

`FILENAME` is the path to a file containing English speech. Change `language` to match your audio. Use the returned job ID:

```bash
curl -s -L -X 'GET' "http://${APPLIANCE_HOST}/v2/jobs/${JOB_ID}/" \
   | jq

curl -s -L -X 'GET' "http://${APPLIANCE_HOST}/v2/jobs/${JOB_ID}/transcript" \
   | jq
```

Under normal conditions a job takes less than half the duration of the media file: a 60 minute MP3 should finish in under 30 minutes.

The jobs web UI at `https://${APPLIANCE_HOST}/v2/ui` lets you make the same POST requests in a browser.

For job config and output formats, see `speechmatics:batch-transcription`.

### Realtime smoke test

```bash
speechmatics transcribe --lang en ${PATH_TO_AUDIO_FILE} --url "ws://${APPLIANCE_HOST}:9000/v2/en" --ssl-mode none
```

Transcribed text prints to the console on success. For session config and messages, see `speechmatics:realtime-transcription`.

## Feature availability on-prem

From the deployments overview. "On-prem" applies to the Batch and Realtime modes only; agent STT is SaaS only. This table covers on-prem deployments in general, not the appliance specifically; appliance features also depend on the license (see [licensing.md](licensing.md#license-feature-codes)).

| Feature | Modes | Deployments |
| --- | --- | --- |
| Multilingual Speech to Text | Batch, Realtime | SaaS, on-prem |
| Alignment | Batch | SaaS |
| Audio events | Batch, Realtime | SaaS, on-prem |
| Audio filtering | Batch, Realtime | SaaS, on-prem |
| Auto chapters | Batch | SaaS |
| Custom dictionary | Batch, Realtime, agent STT | SaaS, on-prem |
| Diarization | Batch, Realtime, agent STT (speaker diarization only) | SaaS, on-prem |
| Disfluencies and word replacement | Batch, Realtime, agent STT | SaaS, on-prem |
| Entity Detection | Batch | SaaS |
| Feature discovery | Batch, Realtime | SaaS |
| Fetch URL | Batch | SaaS, on-prem |
| Language identification | Batch | SaaS |
| Notifications | Batch | SaaS, on-prem |
| PII Redaction | Batch | SaaS |
| Punctuation settings | Batch, Realtime | SaaS, on-prem |
| Sentiment analysis | Batch | SaaS, on-prem |
| Smart formatting | Batch, Realtime | SaaS, on-prem |
| Speaker identification | Batch, Realtime, agent STT | SaaS, on-prem (batch requires the GPU Speech to Text container; Realtime works on CPU and GPU containers) |
| Summarization | Batch | SaaS |
| Topic detection | Batch | SaaS |
| Tracking | Batch, Realtime | SaaS, on-prem |
| Translation | Batch, Realtime | SaaS, on-prem |
| Turn detection | Realtime | SaaS, on-prem |

The overview lists Language identification as SaaS only, but the appliance docs describe enabling it on a Batch appliance. See [scaling-and-gpu.md](scaling-and-gpu.md#language-identification). The license feature list marks Translation and Realtime transcription as currently not available in appliances.
