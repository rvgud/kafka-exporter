# 🔥 Fast Kafka Exporter for Prometheus

A **high-performance Kafka exporter for Prometheus**, optimized for low-latency metric scraping. This exporter is designed as a faster alternative to the popular [danielqsj/kafka_exporter](https://github.com/danielqsj/kafka_exporter), with a trade-off: slightly delayed metrics in exchange for significantly improved response times.

---

## 🚀 Why This Exporter?

Typical exporters (like `danielqsj/kafka_exporter`) fetch and compute Kafka metrics **live** when Prometheus scrapes the `/metrics` endpoint. This can lead to:

- High response latency
- Increased Kafka load
- Exporter instability in large clusters

**This exporter solves that by pre-fetching and caching metrics.** When Prometheus hits `/metrics`, results are returned immediately with no live computation or Kafka access.

> ⚡ This ensures ultra-fast response times and consistent performance.

---

## 🧠 How It Works

1. Metrics are **fetched and computed in the background** at a fixed interval (e.g., every 15 seconds).
2. When Prometheus scrapes `/metrics`, it receives the **most recently cached values**.
3. After each scrape (or on timer), the next fetch is scheduled in the background.

---

## 📉 Trade-off

| Feature             | Behavior                                      |
|---------------------|-----------------------------------------------|
| Metric freshness    | Always behind by `--scrape.interval` seconds |
| Response time       | Near-instant (no computation on scrape)      |
| Kafka load          | Controlled, predictable, and infrequent      |

---

## 🛠 Features

- ⚡ **Instant response** at `/metrics`
- 🔄 **Background pre-fetching** of Kafka metrics
- 🧮 **Pre-computed** offset, lag, and topic metrics
- 🔧 Configurable scrape interval
- 🪶 Lightweight and production-ready
- 🧵 Stable under heavy Prometheus load
- 🐳 Docker image support
- 🧪 Tested with large Kafka clusters

---

## 📈 Comparison with danielqsj/kafka_exporter

| Feature                         | This Exporter         | danielqsj/kafka_exporter |
|----------------------------------|------------------------|---------------------------|
| Pre-fetched metrics              | ✅ Yes                | ❌ No                    |
| Instant response time            | ✅ Yes                | ❌ No                    |
| Real-time accuracy               | ❌ No (slight delay)  | ✅ Yes                   |
| Kafka load during scrape         | ✅ Low                | ❌ High                  |
| Suitable for large Kafka setups  | ✅ Yes                | ⚠️ May struggle          |

---

## ❤️ Contributing

We welcome contributions, bug reports, and feature requests!  
Please open an issue or submit a pull request to help improve this exporter.

---

## 📄 License

This project is licensed under the [GPL-3.0 License](https://github.com/rvgud/kafka-exporter?tab=GPL-3.0-1-ov-file).

---


## 🐳 Usage

### 🛠 Build

```bash
docker build -t kafka-exporter .
```

### ▶️ Run

```bash
docker run -p 8080:8080 \
  -e KAFKA_SERVERS=localhost:9092 \
  -e CLUSTERNAME=dev-cluster \
  -e LOG_LEVEL=INFO \
  ravindrashekhawat/kafka-exporter:latest
```

> 🔹 `KAFKA_SERVERS` - (Required) Comma-separated list of Kafka bootstrap servers  
> 🔹 `CLUSTERNAME` - (Required) Identifier label for the Kafka cluster  
> 🔹 `LOG_LEVEL` - (Optional) Logging verbosity (e.g., INFO, DEBUG)

## 📊 Prometheus Configuration Example

```yaml
scrape_configs:
  - job_name: 'kafka-exporter'
    static_configs:
      - targets: ['localhost:8080']
```
---

## 📏 Metrics Exposed

### 🔹 Broker Metrics

| Metric Name              | Type  | Labels       | Description                                    |
|--------------------------|-------|--------------|------------------------------------------------|
| kafka_brokers            | Gauge | None         | Number of Brokers in the Kafka Cluster         |
| kafka_broker_info        | Gauge | address, id  | Information about each Kafka broker            |

### 🔹 Topic & Partition Metrics

| Metric Name                                           | Type  | Labels                  | Description                                        |
|-------------------------------------------------------|-------|--------------------------|----------------------------------------------------|
| kafka_topic_partitions                                | Gauge | topic                   | Number of partitions for each topic               |
| kafka_topic_partition_current_offset                  | Gauge | topic, partition        | Current offset for topic/partition                |
| kafka_topic_partition_oldest_offset                   | Gauge | topic, partition        | Oldest offset for topic/partition                 |
| kafka_topic_partition_in_sync_replica                 | Gauge | topic, partition        | In-sync replicas count                            |
| kafka_topic_partition_leader                          | Gauge | topic, partition        | Leader broker ID                                  |
| kafka_topic_partition_leader_is_preferred             | Gauge | topic, partition        | 1 if using the preferred leader                   |
| kafka_topic_partition_replicas                        | Gauge | topic, partition        | Number of replicas                                |
| kafka_topic_partition_under_replicated_partition      | Gauge | topic, partition        | 1 if under-replicated                             |

### 🔹 Consumer Group Metrics

| Metric Name                                | Type  | Labels                     | Description                                        |
|--------------------------------------------|-------|-----------------------------|----------------------------------------------------|
| kafka_consumergroup_current_offset         | Gauge | group, topic, partition    | Current consumer offset per partition             |
| kafka_consumergroup_current_offset_sum     | Gauge | group, topic               | Sum of current offsets per topic                  |
| kafka_consumergroup_lag                    | Gauge | group, topic, partition    | Approximate lag per partition                     |
| kafka_consumergroup_lag_sum                | Gauge | group, topic               | Total lag per topic                               |

### 🔹 Cluster Status Metric

| Metric Name                   | Type  | Labels             | Description                               |
|-------------------------------|-------|---------------------|-------------------------------------------|
| kafka_cluster_not_reachable   | Gauge | cluster, type       | 1 if Kafka cluster is not reachable       |