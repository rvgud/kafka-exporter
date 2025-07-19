from kafka import KafkaAdminClient, BrokerConnection, KafkaConsumer
from Logger import global_logger
import os
import socket

logger = global_logger
bootstrap_servers=os.getenv('KAFKA_SERVERS')
class KafkaConnector:
    def __init__(self):
        """
        Initializes the KafkaConnector.

        :param bootstrap_servers: Comma-separated list of Kafka broker addresses.
        :param client_id: Optional client ID for Kafka.
        """
        self.client_id = "kafka-exporter"
        self.admin_client = self._create_admin_client()
        self.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers , enable_auto_commit=False,request_timeout_ms=15000)
        logger.debug("Kafka connector initialized ")

    def close(self):
        """
        Gracefully close Kafka consumer and admin client.
        """
        try:
            if self.consumer:
                self.consumer.close()
                logger.debug("Kafka consumer closed.")
        except Exception as e:
            logger.warning(f"Failed to close Kafka consumer: {e}")
        try:
            if self.admin_client:
                self.admin_client.close()
                logger.debug("Kafka admin client closed.")
        except Exception as e:
            logger.warning(f"Failed to close Kafka admin client: {e}")
    def _create_admin_client(self) -> KafkaAdminClient:
        """
        Create and return a Kafka AdminClient instance.
        """
        logger.info(f"bootstrap servers {self.bootstrap_servers}")
        return KafkaAdminClient(bootstrap_servers=self.bootstrap_servers,client_id=self.client_id,request_timeout_ms=15000)
    def get_admin_client(self) -> KafkaAdminClient:
        """
        Returns the AdminClient instance.
        """
        return self.admin_client
    def is_broker_alive(self,host: str, port: int, timeout: float = 2.0) -> bool:
        conn = BrokerConnection(host=host, port=port, afi=socket.AF_INET,request_timeout_ms=15000)
        conn.connect_blocking(timeout=timeout)
        if not conn.connected():
            conn.close()
            return False
        conn.close()
        return True
