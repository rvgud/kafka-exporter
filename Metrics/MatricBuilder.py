from Logger import global_logger as logger
from typing import Iterable, Dict, List, Any
from prometheus_client import Gauge, Counter, Summary, Histogram
from typing import Any
class MatricBuilder:
    def buildMetrics(self,specs: Iterable[dict],registry):
        types = {
            "gauge": Gauge,
            "counter": Counter,
            "summary": Summary,
            "histogram": Histogram,
        }
        metrics: Dict[str, Any] = {}
        for spec in specs:
            if not isinstance(spec, dict):
                raise TypeError(f"Metric spec must be dict, got {type(spec)}")
            try:
                name = spec["name"]
                mtype = spec["type"].lower()
            except KeyError as missing:
                raise ValueError(f"Missing required key {missing} in metric spec")
            labels: List[str] = spec.get("labels", []) or []
            labels.append("cluster")
            labels.append("type")
            help_text: str = spec.get(
                "help",
                f"{mtype.title()} metric {name.replace('_', ' ')}",
            )
            if mtype not in types:
                raise ValueError(
                    f"Unsupported metric type '{mtype}' "
                    f"(choose from {', '.join(types)})"
                )
            metric_cls = types[mtype]
            metric: Any
            if labels:
                metric = metric_cls(name, help_text, labelnames=labels,registry=registry)
            else:
                metric = metric_cls(name, help_text,registry=registry)
            metrics[name] = metric
        return metrics
