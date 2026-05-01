from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

from .graph_builder import DirectedLabelledGraph, build_graph_from_paths
from .io import load_yaml_file
from .report import write_verification_reports
from .validation import DocumentValidationError


class VerificationError(DocumentValidationError):
    """Raised when verification inputs or results are invalid for the bounded model."""


def verify_from_paths(
    topology_path: str | Path,
    policies_directory: str | Path,
    queries_path: str | Path,
    output_directory: str | Path,
) -> dict[str, Any]:
    """Build the graph, evaluate the bounded queries, and write reports."""
    graph = build_graph_from_paths(topology_path=topology_path, policies_directory=policies_directory)
    queries_document = load_verification_queries(queries_path)
    report_document = verify_graph(graph=graph, queries_document=queries_document)
    write_verification_reports(report_document, output_directory)
    return report_document


def load_verification_queries(path: str | Path) -> dict[str, Any]:
    """Load and validate the bounded verification query document."""
    document = load_yaml_file(path)
    required_reachable = document.get("required_reachable")
    forbidden_unreachable = document.get("forbidden_unreachable")
    terminal_services = document.get("terminal_services")

    if not isinstance(required_reachable, list) or not required_reachable:
        raise VerificationError("queries must define required_reachable as a non-empty list")
    if not isinstance(forbidden_unreachable, list) or not forbidden_unreachable:
        raise VerificationError("queries must define forbidden_unreachable as a non-empty list")
    if not isinstance(terminal_services, list) or not terminal_services:
        raise VerificationError("queries must define terminal_services as a non-empty list")

    for section_name in ("required_reachable", "forbidden_unreachable"):
        for entry in document[section_name]:
            if set(entry) != {"source", "destination"}:
                raise VerificationError(
                    f"query entries in {section_name} must contain only source and destination"
                )

    for service in terminal_services:
        if not isinstance(service, str) or not service:
            raise VerificationError("terminal_services entries must be non-empty strings")

    return document


def verify_graph(
    graph: DirectedLabelledGraph, queries_document: dict[str, Any]
) -> dict[str, Any]:
    """Evaluate the bounded reachability and non-reachability queries."""
    required_results: list[dict[str, Any]] = []
    forbidden_results: list[dict[str, Any]] = []
    terminal_results: list[dict[str, Any]] = []
    reachable_paths: list[dict[str, Any]] = []
    violation_paths: list[dict[str, Any]] = []

    for query in queries_document["required_reachable"]:
        path = find_path(graph, query["source"], query["destination"])
        status = "pass" if path else "fail"
        edge_provenance = path_edge_provenance(graph, path) if path else []
        result = {
            "source": query["source"],
            "destination": query["destination"],
            "status": status,
            "path": path,
            "edge_provenance": edge_provenance,
        }
        required_results.append(result)
        if path:
            reachable_paths.append(
                {
                    "source": query["source"],
                    "destination": query["destination"],
                    "path": path,
                }
            )

    for query in queries_document["forbidden_unreachable"]:
        path = find_path(graph, query["source"], query["destination"])
        status = "pass" if path is None else "fail"
        edge_provenance = path_edge_provenance(graph, path) if path else []
        result = {
            "source": query["source"],
            "destination": query["destination"],
            "status": status,
            "violation_path": path,
            "edge_provenance": edge_provenance,
        }
        forbidden_results.append(result)
        if path:
            violation_paths.append(
                {
                    "source": query["source"],
                    "destination": query["destination"],
                    "path": path,
                }
            )

    for service in queries_document["terminal_services"]:
        if service not in graph.nodes:
            raise VerificationError(f"terminal service '{service}' is missing from the graph")

        outgoing_edges = list(graph.adjacency.get(service, ()))
        service_violation_paths: list[dict[str, Any]] = []
        for workload in graph.workload_nodes:
            path = find_path(graph, service, workload)
            if path and len(path) > 1:
                service_violation_paths.append(
                    {
                        "destination": workload,
                        "path": path,
                        "edge_provenance": path_edge_provenance(graph, path),
                    }
                )
                violation_paths.append(
                    {
                        "source": service,
                        "destination": workload,
                        "path": path,
                    }
                )

        status = "pass" if not outgoing_edges and not service_violation_paths else "fail"
        terminal_results.append(
            {
                "service": service,
                "status": status,
                "outgoing_edges": outgoing_edges,
                "violation_paths": service_violation_paths,
            }
        )

    overall_status = (
        "pass"
        if all(result["status"] == "pass" for result in required_results)
        and all(result["status"] == "pass" for result in forbidden_results)
        and all(result["status"] == "pass" for result in terminal_results)
        else "fail"
    )

    return {
        "overall_status": overall_status,
        "required_reachable": required_results,
        "forbidden_unreachable": forbidden_results,
        "terminal_service_transit": terminal_results,
        "paths_found_for_reachable_paths": reachable_paths,
        "paths_found_for_violations": violation_paths,
        "edge_provenance": _serialize_edge_provenance(graph),
        "graph_node_count": len(graph.nodes),
        "graph_edge_count": len(graph.edges),
    }


def find_path(
    graph: DirectedLabelledGraph, source: str, destination: str
) -> list[str] | None:
    """Find the first deterministic breadth-first path between two nodes."""
    if source not in graph.nodes or destination not in graph.nodes:
        raise VerificationError(f"query references unknown node: {source} -> {destination}")

    queue: deque[list[str]] = deque([[source]])
    visited = {source}

    while queue:
        path = queue.popleft()
        current = path[-1]
        if current == destination:
            return path

        for neighbor in graph.adjacency.get(current, ()):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return None


def path_edge_provenance(
    graph: DirectedLabelledGraph, path: list[str] | None
) -> list[dict[str, Any]]:
    """Return deterministic provenance records for each edge in a path."""
    if not path or len(path) < 2:
        return []

    provenance_records: list[dict[str, Any]] = []
    for source, destination in zip(path, path[1:]):
        provenance = graph.edge_provenance[(source, destination)]
        provenance_records.append(
            {
                "source": source,
                "destination": destination,
                "provenance": list(provenance),
            }
        )
    return provenance_records


def _serialize_edge_provenance(graph: DirectedLabelledGraph) -> dict[str, list[str]]:
    return {
        f"{source}->{destination}": list(provenance)
        for (source, destination), provenance in sorted(graph.edge_provenance.items())
    }
