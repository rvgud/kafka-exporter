import os
from datetime import datetime
from Logger import global_logger
from Metrics import MatricBuilder
import gc
from KafkaConnector import KafkaConnector
from kafka.structs import TopicPartition
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
clustername=os.environ['CLUSTERNAME']
logger=global_logger
totalmetricsCreated=[]
class Scrapper:
    def startParrallelLogProcessing(self,registry):
        for collector in totalmetricsCreated:
            try:
                registry.unregister(collector)
            except Exception as e:
                logger.error("Couldn't clear one metric from registry.Ignoring.")
        logger.info(f"Cleared metrics {len(totalmetricsCreated)}")
        totalmetricsCreated.clear()
        logger.info(f"Remaining metrics {len(totalmetricsCreated)}")
        tasks = [
            (self.startScrapinBrokerMetrics, (registry)),
            (self.startScrapingTopicMetrics, (registry)),
            (self.startScrapingGroupsMetrics, (registry)),
        ]
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = []
            for func, args in tasks:
                futures.append(executor.submit(func, args))
            for future in as_completed(futures,timeout=45):
                try:
                    result = future.result(timeout=40)
                except Exception as exc:
                    logger.exception(f"Thread generated an exception")
        logger.info(f"Completed single collection cycle.")
    def startScrapinBrokerMetrics(self,registry):
        logger.info(f"Starting scrapping for broker metrics")
        metric_builder=MatricBuilder.MatricBuilder()
        broker_metrics = [
            {
                "name": "kafka_brokers",
                "type": "gauge",
                "labels": [],  # no labels
                "help": "Number of Brokers in the Kafka Cluster.",
            },
            {
                "name": "kafka_broker_info",
                "type": "gauge",
                "labels": ["address", "id"],  # two labels
                "help": "Information about the Kafka Broker.",
            },
        ]
        metricsCreated = metric_builder.buildMetrics(broker_metrics,registry)
        totalmetricsCreated.extend(list(metricsCreated.values()))
        del metric_builder
        logger.info(f"topic metric building finished")
        kafka_connector = KafkaConnector.KafkaConnector()
        kafka_admin_client = kafka_connector.get_admin_client()
        startProcessingtime = datetime.now()
        metadata=kafka_admin_client.describe_cluster()
        brokers = metadata.get('brokers', [])
        metricsCreated["kafka_brokers"]
        metricsCreated["kafka_brokers"].labels(cluster=clustername,type="kafka").set(len(brokers))
        for broker in brokers:
            host = broker["host"]
            port = broker["port"]
            address = f"{host}:{port}"
            broker_id = str(broker["node_id"])
            alive = kafka_connector.is_broker_alive(host, port)
            metricsCreated["kafka_broker_info"].labels(address=address, id=broker_id,cluster=clustername,type="kafka").set(1 if alive else 0)
        endProcessingtime = datetime.now()
        logger.info(f"collected brokers metric in {(endProcessingtime - startProcessingtime).total_seconds()}seconds ")
        kafka_connector.close()
        del kafka_connector
        gc.collect()
    def startScrapingTopicMetrics(self, registry):
        logger.info(f"Starting scrapping for topic metrics")
        metric_builder = MatricBuilder.MatricBuilder()
        topic_partition_metrics = [
            {
                "name": "kafka_topic_partitions",
                "type": "gauge",
                "labels": ["topic"],
                "help": "Number of partitions for this Topic.",
            },
            {
                "name": "kafka_topic_partition_current_offset",
                "type": "gauge",
                "labels": ["topic", "partition"],
                "help": "Current Offset of a Broker at Topic/Partition.",
            },
            {
                "name": "kafka_topic_partition_oldest_offset",
                "type": "gauge",
                "labels": ["topic", "partition"],
                "help": "Oldest Offset of a Broker at Topic/Partition.",
            },
            {
                "name": "kafka_topic_partition_in_sync_replica",
                "type": "gauge",
                "labels": ["topic", "partition"],
                "help": "Number of In-Sync Replicas for this Topic/Partition.",
            },
            {
                "name": "kafka_topic_partition_leader",
                "type": "gauge",
                "labels": ["topic", "partition"],
                "help": "Leader Broker ID of this Topic/Partition.",
            },
            {
                "name": "kafka_topic_partition_leader_is_preferred",
                "type": "gauge",
                "labels": ["topic", "partition"],
                "help": "1 if Topic/Partition is using the Preferred Broker.",
            },
            {
                "name": "kafka_topic_partition_replicas",
                "type": "gauge",
                "labels": ["topic", "partition"],
                "help": "Number of Replicas for this Topic/Partition.",
            },
            {
                "name": "kafka_topic_partition_under_replicated_partition",
                "type": "gauge",
                "labels": ["topic", "partition"],
                "help": "1 if Topic/Partition is under Replicated.",
            },
        ]
        metricsCreated = metric_builder.buildMetrics(topic_partition_metrics,registry)
        totalmetricsCreated.extend(list(metricsCreated.values()))
        del metric_builder
        logger.info(f"topics metric building finished")
        kafka_connector = KafkaConnector.KafkaConnector()
        startProcessingtime = datetime.now()
        collect_topic_partition_metrics(kafka_connector,metricsCreated)
        endProcessingtime = datetime.now()
        logger.info(f"collected topics metric in {(endProcessingtime - startProcessingtime).total_seconds()}seconds ")
        kafka_connector.close()
        del kafka_connector
        gc.collect()
    def startScrapingGroupsMetrics(self, registry):
        logger.info(f"Starting scrapping for groups metrics")
        metric_builder = MatricBuilder.MatricBuilder()

        consumer_group_metrics = [
            {
                "name": "kafka_consumergroup_current_offset",
                "type": "gauge",
                "labels": ["group", "topic", "partition"],
                "help": "Current Offset of a ConsumerGroup at Topic/Partition.",
            },
            {
                "name": "kafka_consumergroup_current_offset_sum",
                "type": "gauge",
                "labels": ["group", "topic"],
                "help": "Current Offset of a ConsumerGroup at Topic for all partitions.",
            },
            {
                "name": "kafka_consumergroup_lag",
                "type": "gauge",
                "labels": ["group", "topic", "partition"],
                "help": "Current Approximate Lag of a ConsumerGroup at Topic/Partition.",
            },
            {
                "name": "kafka_consumergroup_lag_sum",
                "type": "gauge",
                "labels": ["group", "topic"],
                "help": "Current Approximate Lag of a ConsumerGroup at Topic for all partitions.",
            },
        ]

        metricsCreated = metric_builder.buildMetrics(consumer_group_metrics,registry)
        totalmetricsCreated.extend(list(metricsCreated.values()))
        del metric_builder
        logger.info(f"groups metric building finished")
        kafka_connector = KafkaConnector.KafkaConnector()
        startProcessingtime = datetime.now()
        collect_consumer_group_metrics_parallel(kafka_connector, metricsCreated)
        endProcessingtime = datetime.now()
        logger.info(f"collected groups metric in {(endProcessingtime - startProcessingtime).total_seconds()}seconds ")
        kafka_connector.close()
        del kafka_connector
        gc.collect()
        
def collect_topic_partition_metrics(kafka_connector,metrics):
    admin = kafka_connector.get_admin_client()
    consumer = kafka_connector.consumer
    try:
        # 1⃣  One metadata call for the whole cluster
        topics_md = admin.describe_topics()  # returns list[TopicMetadata]

        # 2⃣  Build one global TopicPartition list
        all_tps = []
        for tm in topics_md:
            for pm in tm["partitions"]:
                all_tps.append(TopicPartition(tm["topic"], pm["partition"]))

        # 3⃣  Two batched ListOffsets requests
        beg_offsets = consumer.beginning_offsets(all_tps)
        end_offsets = consumer.end_offsets(all_tps)

        # 4⃣  Populate metrics (all local work)
        for tm in topics_md:
            topic = tm["topic"]
            parts = tm["partitions"]
            metrics["kafka_topic_partitions"].labels(topic=topic,cluster=clustername,type="kafka").set(len(parts))
            for pm in parts:
                pid = pm["partition"]
                tp = TopicPartition(topic=topic, partition=pid)

                # replica & ISR lists already ints in kafka-python ≥2.0
                replicas = pm["replicas"]
                isr = pm["isr"]
                leader = pm["leader"]
                preferred_leader = replicas[0] if replicas else -1

                metrics["kafka_topic_partition_current_offset"] \
                    .labels(topic=topic, partition=pid,cluster=clustername,type="kafka").set(end_offsets.get(tp, 0))
                metrics["kafka_topic_partition_oldest_offset"] \
                    .labels(topic=topic, partition=pid,cluster=clustername,type="kafka").set(beg_offsets.get(tp, 0))

                metrics["kafka_topic_partition_in_sync_replica"] \
                    .labels(topic=topic, partition=pid,cluster=clustername,type="kafka").set(len(isr))
                metrics["kafka_topic_partition_replicas"] \
                    .labels(topic=topic, partition=pid,cluster=clustername,type="kafka").set(len(replicas))
                metrics["kafka_topic_partition_under_replicated_partition"] \
                    .labels(topic=topic, partition=pid,cluster=clustername,type="kafka").set(1 if len(isr) < len(replicas) else 0)

                metrics["kafka_topic_partition_leader"] \
                    .labels(topic=topic, partition=pid,cluster=clustername,type="kafka").set(leader)
                metrics["kafka_topic_partition_leader_is_preferred"] \
                    .labels(topic=topic, partition=pid,cluster=clustername,type="kafka").set(1 if leader == preferred_leader else 0)
        consumer.close()
        admin.close()
    except Exception as e:
        consumer.close()
        admin.close()
        logger.error(f"[ERROR] Failed to collect Kafka metrics: {e}")
def collect_consumer_group_metrics_parallel(kafka_connector,metrics,max_workers: int = 32):
    admin = kafka_connector.get_admin_client()
    consumer = kafka_connector.consumer
    # Step 1: Get all group IDs
    startProcessingtime = datetime.now()
    # ── 1) discover all groups (one request) ────────────────────────────────
    try:
        t0 = datetime.now()
        group_ids = [gid for (gid, _) in admin.list_consumer_groups()]
        logger.info("discovered %d groups in %.2fs",
                    len(group_ids), (datetime.now() - t0).total_seconds())

        # containers
        tp_committed: dict[TopicPartition, tuple[str, int]] = {}    # tp → (group, committed)
        all_tps:      set[TopicPartition] = set()

        # ── 2) parallel fetch offsets + membership per group ────────────────────
        def fetch_group(group_id: str):
            try:
                offsets = admin.list_consumer_group_offsets(group_id)
                return group_id, offsets
            except Exception as exc:                       # keep exporter alive
                logger.warning("group %s fetch failed: %s", group_id, exc)
                return group_id, {}, 0

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(fetch_group, gid) for gid in group_ids]
            for fut in as_completed(futures):
                gid, offsets = fut.result()
                for tp, meta in offsets.items():
                    tp_committed[tp] = (gid, meta.offset)
                    all_tps.add(tp)

        # ── 3) one batched end-offset call ──────────────────────────────────────
        end_offsets = consumer.end_offsets(list(all_tps))

        # ── 4) compute lags + emit metrics ──────────────────────────────────────
        topic_offset_sum = defaultdict(int)   # (group, topic) → committed sum
        topic_lag_sum    = defaultdict(int)   # (group, topic) → lag sum

        for tp, (gid, committed) in tp_committed.items():
            topic, part = tp.topic, tp.partition
            log_end     = end_offsets.get(tp, 0)
            lag         = max(log_end - committed, 0)

            # partition-level
            metrics["kafka_consumergroup_current_offset"] \
                .labels(group=gid,topic=topic,partition=part,cluster=clustername,type="kafka").set(committed)
            metrics["kafka_consumergroup_lag"] \
                .labels(group=gid,topic=topic,partition=part,cluster=clustername,type="kafka").set(lag)

            # per-topic accumulation
            topic_offset_sum[(gid, topic)] += committed
            topic_lag_sum[(gid, topic)]    += lag

        # topic-level
        for (gid, topic), total in topic_offset_sum.items():
            metrics["kafka_consumergroup_current_offset_sum"] \
                .labels(group=gid,topic=topic,cluster=clustername,type="kafka").set(total)

        for (gid, topic), total in topic_lag_sum.items():
            metrics["kafka_consumergroup_lag_sum"] \
                .labels(group=gid,topic=topic,cluster=clustername,type="kafka").set(total)
        consumer.close()
        admin.close()
    except Exception as e:
        consumer.close()
        admin.close()
        logger.error(f"[ERROR] Failed to collect Kafka metrics: {e}")
        raise e
