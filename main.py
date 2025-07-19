import os
import threading
from Scrapper import Scrapper
from Logger import global_logger
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST, Gauge
from flask import Flask, Response
from waitress import serve
from KafkaConnector import KafkaConnector
logger=global_logger
app = Flask(__name__)
scrapper=Scrapper.Scrapper()
registry = CollectorRegistry()
clustername=os.environ['CLUSTERNAME']
kafka_cluster_not_reachable=Gauge("kafka_cluster_not_reachable","Set to 1 if Kafka broker is not reachable", ['cluster', 'type'],registry=registry)
@app.route('/metrics/')
def metrics():
    response = Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)
    thread = threading.Thread(target=scrapper.startParrallelLogProcessing, args=(registry,))
    thread.daemon = True
    thread.start()
    return response
@app.route('/')
def health():
    try:
        kafka_connector = KafkaConnector.KafkaConnector()
        healthy = kafka_connector.get_admin_client().describe_cluster()
        kafka_connector.close()
        if(healthy):
            kafka_cluster_not_reachable.labels(cluster=clustername,type="kafka").set(0)
            return Response("OK", status=200, mimetype='application/json')
        else:
            logger.error(f"Kafka broker not reachable {healthy}")
            kafka_cluster_not_reachable.labels(cluster=clustername,type="kafka").set(1)
            return Response("NOT_ABLE_PING_KAFKA", status=503, mimetype='application/json')
    except Exception as e:
        logger.exception("Exception in healthcheck")
        return Response("ERROR", status=503, mimetype='application/json')
    finally:
        kafka_connector.close()
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080,threads=5,connection_limit=1000,backlog=1000)