"""Kubernetes MCP server — cluster inspection and pod operations."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "kubernetes",
    instructions=(
        "Kubernetes integration for cluster inspection. List pods, deployments, "
        "namespaces, events, and fetch pod logs."
    ),
)

_api: Any = None


def _get_api() -> Any:
    global _api
    if _api is None:
        try:
            from kubernetes import client, config
        except ImportError as exc:
            raise ImportError("Install Kubernetes support: pip install -e '.[mcp]'") from exc
        settings = get_settings()
        try:
            if settings.kubeconfig_path:
                config.load_kube_config(config_file=settings.kubeconfig_path)
            else:
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()
        except config.ConfigException as exc:
            raise ValueError(
                "Kubernetes config not found. Set KUBECONFIG_PATH or run in-cluster."
            ) from exc
        _api = client.CoreV1Api()
    return _api


def _apps_api() -> Any:
    from kubernetes import client

    return client.AppsV1Api()


def _default_namespace(namespace: str) -> str:
    return namespace or get_settings().kubernetes_namespace


@mcp.tool()
def list_namespaces() -> str:
    """List all namespaces in the cluster."""
    try:
        items = _get_api().list_namespace().items
        namespaces = [{"name": ns.metadata.name, "status": ns.status.phase} for ns in items]
        return text_result({"namespaces": namespaces})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def list_pods(namespace: str = "") -> str:
    """List pods in a namespace."""
    try:
        ns = _default_namespace(namespace)
        items = _get_api().list_namespaced_pod(namespace=ns).items
        pods = [
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "node": pod.spec.node_name,
                "restarts": sum(c.restart_count for c in (pod.status.container_statuses or [])),
            }
            for pod in items
        ]
        return text_result({"namespace": ns, "pods": pods})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_pod_logs(namespace: str, pod_name: str, container: str = "", tail_lines: int = 100) -> str:
    """Fetch logs from a pod container."""
    try:
        ns = _default_namespace(namespace)
        kwargs: dict[str, Any] = {"name": pod_name, "namespace": ns, "tail_lines": tail_lines}
        if container:
            kwargs["container"] = container
        logs = _get_api().read_namespaced_pod_log(**kwargs)
        return text_result({"namespace": ns, "pod": pod_name, "logs": logs})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def list_deployments(namespace: str = "") -> str:
    """List deployments in a namespace."""
    try:
        ns = _default_namespace(namespace)
        items = _apps_api().list_namespaced_deployment(namespace=ns).items
        deployments = [
            {
                "name": d.metadata.name,
                "namespace": d.metadata.namespace,
                "replicas": d.spec.replicas,
                "ready": d.status.ready_replicas or 0,
                "available": d.status.available_replicas or 0,
            }
            for d in items
        ]
        return text_result({"namespace": ns, "deployments": deployments})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def describe_deployment(namespace: str, name: str) -> str:
    """Get detailed deployment status and conditions."""
    try:
        ns = _default_namespace(namespace)
        d = _apps_api().read_namespaced_deployment(name=name, namespace=ns)
        return text_result(
            {
                "name": d.metadata.name,
                "namespace": d.metadata.namespace,
                "replicas": d.spec.replicas,
                "ready": d.status.ready_replicas,
                "available": d.status.available_replicas,
                "conditions": [
                    {"type": c.type, "status": c.status, "reason": c.reason, "message": c.message}
                    for c in (d.status.conditions or [])
                ],
                "selector": d.spec.selector.match_labels,
                "images": [c.image for c in d.spec.template.spec.containers],
            }
        )
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_events(namespace: str = "", limit: int = 50) -> str:
    """List recent cluster events in a namespace."""
    try:
        ns = _default_namespace(namespace)
        items = _get_api().list_namespaced_event(namespace=ns).items
        events = [
            {
                "type": e.type,
                "reason": e.reason,
                "message": e.message,
                "object": f"{e.involved_object.kind}/{e.involved_object.name}",
                "count": e.count,
                "last_timestamp": str(e.last_timestamp),
            }
            for e in sorted(items, key=lambda x: x.last_timestamp or "", reverse=True)[:limit]
        ]
        return text_result({"namespace": ns, "events": events})
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
