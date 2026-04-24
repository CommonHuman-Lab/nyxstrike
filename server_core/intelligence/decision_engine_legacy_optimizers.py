import os
from typing import Any, Dict

from shared.target_profile import TargetProfile
from shared.target_types import TargetType, TechnologyStack


class LegacyParameterOptimizers:
    def _optimize_nmap_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Nmap parameters."""
        params = {"target": profile.target}

        if profile.target_type == TargetType.WEB_APPLICATION:
            params["scan_type"] = "-sV -sC"
            params["ports"] = "80,443,8080,8443,8000,9000"
        elif profile.target_type == TargetType.NETWORK_HOST:
            params["scan_type"] = "-sS -O"
            params["additional_args"] = "--top-ports 1000"

        if context.get("stealth", False):
            params["additional_args"] = params.get("additional_args", "") + " -T2"
        else:
            params["additional_args"] = params.get("additional_args", "") + " -T4"

        return params

    def _optimize_gobuster_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Gobuster parameters."""
        params = {"url": profile.target, "mode": "dir"}

        if TechnologyStack.PHP in profile.technologies:
            params["additional_args"] = "-x php,html,txt,xml"
        elif TechnologyStack.DOTNET in profile.technologies:
            params["additional_args"] = "-x asp,aspx,html,txt"
        elif TechnologyStack.JAVA in profile.technologies:
            params["additional_args"] = "-x jsp,html,txt,xml"
        else:
            params["additional_args"] = "-x html,php,txt,js"

        if context.get("aggressive", False):
            params["additional_args"] += " -t 50"
        else:
            params["additional_args"] += " -t 20"

        return params

    def _optimize_nuclei_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Nuclei parameters."""
        params = {"target": profile.target}

        if context.get("quick", False):
            params["severity"] = "critical,high"
        else:
            params["severity"] = "critical,high,medium"

        tags = []
        for tech in profile.technologies:
            if tech == TechnologyStack.WORDPRESS:
                tags.append("wordpress")
            elif tech == TechnologyStack.DRUPAL:
                tags.append("drupal")
            elif tech == TechnologyStack.JOOMLA:
                tags.append("joomla")

        if tags:
            params["tags"] = ",".join(tags)

        return params

    def _optimize_sqlmap_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize SQLMap parameters."""
        params = {"url": profile.target}

        if TechnologyStack.PHP in profile.technologies:
            params["additional_args"] = "--dbms=mysql --batch"
        elif TechnologyStack.DOTNET in profile.technologies:
            params["additional_args"] = "--dbms=mssql --batch"
        else:
            params["additional_args"] = "--batch"

        if context.get("aggressive", False):
            params["additional_args"] += " --level=3 --risk=2"

        return params

    def _optimize_ffuf_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize FFuf parameters."""
        params = {"url": profile.target}

        if profile.target_type == TargetType.API_ENDPOINT:
            params["match_codes"] = "200,201,202,204,301,302,401,403"
        else:
            params["match_codes"] = "200,204,301,302,307,401,403"

        if context.get("stealth", False):
            params["additional_args"] = "-t 10 -p 1"
        else:
            params["additional_args"] = "-t 40"

        return params

    def _optimize_hydra_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Hydra parameters."""
        params = {"target": profile.target}

        if 22 in profile.open_ports:
            params["service"] = "ssh"
        elif 21 in profile.open_ports:
            params["service"] = "ftp"
        elif 80 in profile.open_ports or 443 in profile.open_ports:
            params["service"] = "http-get"
        else:
            params["service"] = "ssh"

        params["additional_args"] = "-t 4 -w 30"
        return params

    def _optimize_rustscan_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Rustscan parameters."""
        params = {"target": profile.target}

        if context.get("stealth", False):
            params["ulimit"] = 1000
            params["batch_size"] = 500
            params["timeout"] = 3000
        elif context.get("aggressive", False):
            params["ulimit"] = 10000
            params["batch_size"] = 8000
            params["timeout"] = 800
        else:
            params["ulimit"] = 5000
            params["batch_size"] = 4500
            params["timeout"] = 1500

        if context.get("objective", "normal") == "comprehensive":
            params["scripts"] = True

        return params

    def _optimize_masscan_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Masscan parameters."""
        params = {"target": profile.target}

        if context.get("stealth", False):
            params["rate"] = 100
        elif context.get("aggressive", False):
            params["rate"] = 10000
        else:
            params["rate"] = 1000

        if context.get("service_detection", True):
            params["banners"] = True

        return params

    def _optimize_nmap_advanced_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize advanced Nmap parameters."""
        params = {"target": profile.target}

        if context.get("stealth", False):
            params["scan_type"] = "-sS"
            params["timing"] = "T2"
            params["stealth"] = True
        elif context.get("aggressive", False):
            params["scan_type"] = "-sS"
            params["timing"] = "T4"
            params["aggressive"] = True
        else:
            params["scan_type"] = "-sS"
            params["timing"] = "T4"
            params["os_detection"] = True
            params["version_detection"] = True

        if profile.target_type == TargetType.WEB_APPLICATION:
            params["nse_scripts"] = "ssl-cert,http-title,http-headers"
        elif profile.target_type == TargetType.NETWORK_HOST:
            params["nse_scripts"] = "default"

        return params

    def _optimize_enum4linux_ng_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Enum4linux-ng parameters."""
        params = {"target": profile.target}

        params["shares"] = True
        params["users"] = True
        params["groups"] = True
        params["policy"] = True

        if context.get("username"):
            params["username"] = context["username"]
        if context.get("password"):
            params["password"] = context["password"]
        if context.get("domain"):
            params["domain"] = context["domain"]

        return params

    def _optimize_autorecon_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize AutoRecon parameters."""
        params = {"target": profile.target}

        if context.get("quick", False):
            params["port_scans"] = "top-100-ports"
            params["timeout"] = 180
        elif context.get("comprehensive", True):
            params["port_scans"] = "top-1000-ports"
            params["timeout"] = 600

        params["output_dir"] = f"/tmp/autorecon_{profile.target.replace('.', '_')}"
        return params

    def _optimize_ghidra_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Ghidra parameters."""
        params = {"binary": profile.target}

        if context.get("quick", False):
            params["analysis_timeout"] = 120
        elif context.get("comprehensive", True):
            params["analysis_timeout"] = 600
        else:
            params["analysis_timeout"] = 300

        binary_name = os.path.basename(profile.target).replace('.', '_')
        params["project_name"] = f"analysis_{binary_name}"
        return params

    def _optimize_pwntools_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Pwntools parameters."""
        params = {"target_binary": profile.target}

        if context.get("remote_host") and context.get("remote_port"):
            params["exploit_type"] = "remote"
            params["target_host"] = context["remote_host"]
            params["target_port"] = context["remote_port"]
        else:
            params["exploit_type"] = "local"

        return params

    def _optimize_ropper_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Ropper parameters."""
        params = {"binary": profile.target}

        if context.get("exploit_type") == "rop":
            params["gadget_type"] = "rop"
            params["quality"] = 3
        elif context.get("exploit_type") == "jop":
            params["gadget_type"] = "jop"
            params["quality"] = 2
        else:
            params["gadget_type"] = "all"
            params["quality"] = 2

        if context.get("arch"):
            params["arch"] = context["arch"]

        return params

    def _optimize_angr_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize angr parameters."""
        params = {"binary": profile.target}

        if context.get("symbolic_execution", True):
            params["analysis_type"] = "symbolic"
        elif context.get("cfg_analysis", False):
            params["analysis_type"] = "cfg"
        else:
            params["analysis_type"] = "static"

        if context.get("find_address"):
            params["find_address"] = context["find_address"]
        if context.get("avoid_addresses"):
            params["avoid_addresses"] = context["avoid_addresses"]

        return params

    def _optimize_prowler_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Prowler parameters."""
        params = {"provider": "aws"}

        if context.get("cloud_provider"):
            params["provider"] = context["cloud_provider"]

        if context.get("aws_profile"):
            params["profile"] = context["aws_profile"]
        if context.get("aws_region"):
            params["region"] = context["aws_region"]

        params["output_format"] = "json"
        params["output_dir"] = f"/tmp/prowler_{params['provider']}"
        return params

    def _optimize_scout_suite_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Scout Suite parameters."""
        params = {"provider": "aws"}

        if context.get("cloud_provider"):
            params["provider"] = context["cloud_provider"]

        if params["provider"] == "aws" and context.get("aws_profile"):
            params["profile"] = context["aws_profile"]

        params["report_dir"] = f"/tmp/scout-suite_{params['provider']}"
        return params

    def _optimize_kube_hunter_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize kube-hunter parameters."""
        params = {"report": "json"}

        if context.get("kubernetes_target"):
            params["target"] = context["kubernetes_target"]
        elif context.get("cidr"):
            params["cidr"] = context["cidr"]
        elif context.get("interface"):
            params["interface"] = context["interface"]

        if context.get("active_hunting", False):
            params["active"] = "true"

        return params

    def _optimize_trivy_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Trivy parameters."""
        params = {"target": profile.target, "output_format": "json"}

        if profile.target.startswith(("docker.io/", "gcr.io/", "quay.io/")) or ":" in profile.target:
            params["scan_type"] = "image"
        elif os.path.isdir(profile.target):
            params["scan_type"] = "fs"
        else:
            params["scan_type"] = "image"

        if context.get("severity"):
            params["severity"] = context["severity"]
        else:
            params["severity"] = "HIGH,CRITICAL"

        return params

    def _optimize_checkov_params(self, profile: TargetProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize Checkov parameters."""
        params = {"directory": profile.target, "output_format": "json"}

        if context.get("framework"):
            params["framework"] = context["framework"]
        elif os.path.isdir(profile.target):
            if any(f.endswith(".tf") for f in os.listdir(profile.target) if os.path.isfile(os.path.join(profile.target, f))):
                params["framework"] = "terraform"
            elif any(
                f.endswith(".yaml") or f.endswith(".yml")
                for f in os.listdir(profile.target)
                if os.path.isfile(os.path.join(profile.target, f))
            ):
                params["framework"] = "kubernetes"

        return params
