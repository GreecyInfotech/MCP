"""AWS MCP server — S3, EC2, Lambda, and CloudWatch operations."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "aws",
    instructions=(
        "AWS integration for common cloud operations. List S3 buckets/objects, "
        "describe EC2 instances, list Lambda functions, and fetch CloudWatch logs."
    ),
)

_session: Any = None


def _get_session() -> Any:
    global _session
    if _session is None:
        try:
            import boto3
        except ImportError as exc:
            raise ImportError("Install AWS support: pip install -e '.[mcp]'") from exc
        settings = get_settings()
        kwargs: dict[str, str] = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            kwargs["aws_access_key_id"] = settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        _session = boto3.Session(**kwargs)
    return _session


def _client(service: str) -> Any:
    return _get_session().client(service)


@mcp.tool()
def list_s3_buckets() -> str:
    """List all S3 buckets in the AWS account."""
    try:
        response = _client("s3").list_buckets()
        buckets = [
            {"name": b["Name"], "created_at": str(b.get("CreationDate", ""))}
            for b in response.get("Buckets", [])
        ]
        return text_result({"buckets": buckets})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def list_s3_objects(bucket: str, prefix: str = "", max_keys: int = 100) -> str:
    """List objects in an S3 bucket with optional prefix."""
    try:
        response = _client("s3").list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=max_keys)
        objects = [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": str(obj["LastModified"]),
            }
            for obj in response.get("Contents", [])
        ]
        return text_result({"bucket": bucket, "prefix": prefix, "objects": objects})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def describe_ec2_instances(state: str = "running", max_results: int = 50) -> str:
    """Describe EC2 instances filtered by state (running, stopped, etc.)."""
    try:
        filters = [{"Name": "instance-state-name", "Values": [state]}] if state else []
        response = _client("ec2").describe_instances(Filters=filters)
        instances = []
        for reservation in response.get("Reservations", []):
            for inst in reservation.get("Instances", []):
                if len(instances) >= max_results:
                    break
                name = next(
                    (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                    "",
                )
                instances.append(
                    {
                        "instance_id": inst["InstanceId"],
                        "name": name,
                        "type": inst["InstanceType"],
                        "state": inst["State"]["Name"],
                        "az": inst.get("Placement", {}).get("AvailabilityZone"),
                        "private_ip": inst.get("PrivateIpAddress"),
                        "public_ip": inst.get("PublicIpAddress"),
                    }
                )
        return text_result({"state": state, "instances": instances})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def list_lambda_functions(max_items: int = 50) -> str:
    """List Lambda functions in the configured AWS region."""
    try:
        client = _client("lambda")
        paginator = client.get_paginator("list_functions")
        functions = []
        for page in paginator.paginate(PaginationConfig={"MaxItems": max_items}):
            for fn in page.get("Functions", []):
                functions.append(
                    {
                        "name": fn["FunctionName"],
                        "runtime": fn.get("Runtime"),
                        "memory": fn.get("MemorySize"),
                        "timeout": fn.get("Timeout"),
                        "last_modified": fn.get("LastModified"),
                    }
                )
        return text_result({"region": get_settings().aws_region, "functions": functions})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_cloudwatch_logs(
    log_group: str,
    log_stream: str = "",
    limit: int = 50,
    filter_pattern: str = "",
) -> str:
    """Fetch CloudWatch log events from a log group (optionally filtered by stream)."""
    try:
        client = _client("logs")
        if log_stream:
            response = client.get_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                limit=limit,
                startFromHead=False,
            )
            events = [
                {"timestamp": e["timestamp"], "message": e["message"]}
                for e in response.get("events", [])
            ]
            return text_result({"log_group": log_group, "log_stream": log_stream, "events": events})

        kwargs: dict[str, Any] = {"logGroupName": log_group, "limit": limit}
        if filter_pattern:
            kwargs["filterPattern"] = filter_pattern
        response = client.filter_log_events(**kwargs)
        events = [
            {
                "timestamp": e["timestamp"],
                "log_stream": e.get("logStreamName"),
                "message": e["message"],
            }
            for e in response.get("events", [])
        ]
        return text_result({"log_group": log_group, "events": events})
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
