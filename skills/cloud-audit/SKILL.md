---
name: cloud-audit
description: Cloud and container security auditing workflow using prowler, trivy, kube-hunter, and docker-bench for AWS, GCP, Azure, Kubernetes, and container images
---

# cloud-audit

Cloud and container security auditing workflow for NyxStrike. Use this skill when a user wants to audit AWS/Azure/GCP configurations, scan container images for CVEs, assess a Kubernetes cluster, or check Docker host security.

## Workflow

### AWS / Azure / GCP audit (prowler)

Prowler runs hundreds of compliance checks against cloud provider APIs.

**AWS (default profile):**

```
run_tool(tool="prowler", provider="aws", profile="default")
```

**AWS with specific region and checks:**

```
run_tool(tool="prowler", provider="aws",
         profile="default",
         region="us-east-1",
         checks="s3,iam,ec2")
```

**Azure:**

```
run_tool(tool="prowler", provider="azure",
         additional_args="--az-cli-auth")
```

**GCP:**

```
run_tool(tool="prowler", provider="gcp",
         additional_args="--project-id <gcp_project_id>")
```

Key prowler check categories:

| Category | Checks |
|---|---|
| `iam` | Overprivileged roles, unused access keys, MFA |
| `s3` | Public buckets, encryption, logging |
| `ec2` | Security groups, IMDSv2, public snapshots |
| `rds` | Encryption, public access, backups |
| `cloudtrail` | Logging enabled, log validation |
| `guardduty` | Threat detection enabled |

### Container image vulnerability scan (trivy)

Scan a container image for CVEs, secrets, and misconfigurations:

```
# Scan a Docker image
run_tool(tool="trivy", target="<image>:<tag>", scan_type="image")

# Filter by severity
run_tool(tool="trivy", target="nginx:latest",
         scan_type="image",
         severity="HIGH,CRITICAL")

# Scan a local filesystem
run_tool(tool="trivy", target="/path/to/project", scan_type="fs")

# Scan a running container
run_tool(tool="trivy", target="<container_id>", scan_type="image")
```

### Docker host security benchmark (docker_bench)

Check the Docker host and daemon configuration against CIS Docker Benchmark:

```
run_tool(tool="docker_bench")
```

Focus areas:
- Docker daemon configuration
- Container runtime settings
- Image security (no root, minimal base images)
- Network and logging configuration

### Kubernetes penetration testing (kube-hunter)

Assess a Kubernetes cluster for known attack vectors:

```
# Passive discovery (safe, no exploit attempts)
run_tool(tool="kube-hunter", additional_args="--remote <k8s_api_ip>")

# Active testing (attempts exploitation)
run_tool(tool="kube-hunter", additional_args="--remote <k8s_api_ip> --active")
```

Kube-hunter checks for:
- Unauthenticated API server access
- Exposed kubelet ports (10250/10255)
- RBAC misconfigurations
- Container escape vulnerabilities
- etcd exposure

## Cloud security priorities by risk

| Finding | Severity | Tool |
|---|---|---|
| Public S3 bucket | Critical | prowler (s3) |
| Root account has access keys | Critical | prowler (iam) |
| Critical CVE in container image | Critical | trivy |
| K8s API server unauthenticated | Critical | kube-hunter |
| MFA not enabled | High | prowler (iam) |
| Overprivileged IAM role | High | prowler (iam) |
| Container running as root | High | trivy, docker_bench |
| RDS publicly accessible | High | prowler (rds) |
| CloudTrail not enabled | Medium | prowler (cloudtrail) |

## Typical engagement flow

```
1. prowler (cloud config audit)
   → identify misconfigurations and overprivileged IAM

2. trivy (container/image scan)
   → identify CVEs in deployed images

3. docker_bench (if Docker host access)
   → CIS benchmark gaps

4. kube-hunter (if Kubernetes)
   → runtime cluster attack surface
```

## Tips

- Prowler requires cloud credentials configured (`aws configure`, `az login`, etc.) before running.
- Trivy `CRITICAL` findings should always be addressed before deployment — use it in CI/CD pipelines.
- Kube-hunter `--active` mode actually attempts exploits — only use with explicit authorisation.
- Run trivy against base images as well as final images — vulnerabilities often come from upstream layers.

## NyxStrike Tool Reference

| Tool | Use case |
|---|---|
| `prowler` | AWS/Azure/GCP compliance and security audit |
| `trivy` | Container image / filesystem CVE scan |
| `docker_bench` | Docker CIS benchmark assessment |
| `kube-hunter` | Kubernetes cluster penetration testing |
