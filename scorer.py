# scorer.py
#!/usr/bin/env python3

import asyncio
import json
import logging
import os
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaConnectionError, KafkaError

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
RAW_TOPIC              = "transactions"
ENRICHED_TOPIC         = "scored-transactions"
GROUP_ID               = "scorer-group"
RETRY_BACKOFF_SEC      = 2
MAX_RETRIES            = 10

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scorer")


def compute_score(record: dict) -> float:
    # <-- your real scoring logic here
    return 0.0


async def wait_for_kafka() -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        admin = AIOKafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        try:
            await admin.start()
            await admin.list_topics()
            log.info("✅ Kafka reachable on %s", KAFKA_BOOTSTRAP_SERVERS)
            return
        except KafkaConnectionError:
            log.warning("⏳ Kafka not ready, retry %s/%s…", attempt, MAX_RETRIES)
            await asyncio.sleep(RETRY_BACKOFF_SEC)
        finally:
            try:
                await admin.close()
            except Exception:
                pass
    raise RuntimeError("Kafka never became ready")


async def ensure_topics() -> None:
    admin = AIOKafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    try:
        await admin.start()
        existing = set(await admin.list_topics())
        missing = [
            NewTopic(name, num_partitions=1, replication_factor=1)
            for name in (RAW_TOPIC, ENRICHED_TOPIC)
            if name not in existing
        ]
        if missing:
            await admin.create_topics(missing)
            log.info("🆕 Created topics: %s", [t.name for t in missing])
    finally:
        try:
            await admin.close()
        except Exception:
            pass


async def main():
    # 1) Wait for Kafka & create topics
    await wait_for_kafka()
    await ensure_topics()

    # 2) Start consumer
    consumer = AIOKafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
    )
    await consumer.start()

    # 3) Start producer
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()

    log.info("🚀 Scorer is up & running, waiting for messages…")

    try:
        while True:
            msg = await consumer.getone()
            try:
                payload = json.loads(msg.value.decode())
            except json.JSONDecodeError:
                log.error("Skipping invalid JSON: %s", msg.value)
                continue

            payload["fraud_score"] = compute_score(payload)
            try:
                await producer.send_and_wait(
                    ENRICHED_TOPIC,
                    json.dumps(payload).encode(),
                )
            except KafkaError as e:
                log.error("Failed to send enriched message: %s", e)
                await asyncio.sleep(RETRY_BACKOFF_SEC)
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
