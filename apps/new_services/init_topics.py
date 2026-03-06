"""
Kafka Topics Initialization Script
Создает все необходимые топики при старте Kafka
"""

import logging
import time
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация топиков
TOPICS = [
    # User Service
    {"name": "user.registered", "partitions": 3, "replication": 1},
    {"name": "user.updated", "partitions": 3, "replication": 1},
    {"name": "user.deleted", "partitions": 3, "replication": 1},
    {"name": "user.joined.home", "partitions": 3, "replication": 1},
    {"name": "user.left.home", "partitions": 3, "replication": 1},
    {"name": "invite.sent", "partitions": 3, "replication": 1},
    {"name": "invite.accepted", "partitions": 3, "replication": 1},

    # Device Registry
    {"name": "device.registered", "partitions": 5, "replication": 1},
    {"name": "device.updated", "partitions": 5, "replication": 1},
    {"name": "device.deleted", "partitions": 5, "replication": 1},
    {"name": "device.status.changed", "partitions": 5, "replication": 1},
    {"name": "home.created", "partitions": 3, "replication": 1},

    # Heating Control
    {"name": "temperature.updated", "partitions": 5, "replication": 1},
    {"name": "temperature.threshold.exceeded", "partitions": 3, "replication": 1},
    {"name": "mode.changed", "partitions": 3, "replication": 1},
    {"name": "schedule.triggered", "partitions": 3, "replication": 1},
    {"name": "battery.low", "partitions": 3, "replication": 1},

    # Lighting Control
    {"name": "light.power.changed", "partitions": 5, "replication": 1},
    {"name": "light.brightness.changed", "partitions": 5, "replication": 1},
    {"name": "light.color.changed", "partitions": 5, "replication": 1},
    {"name": "group.power.changed", "partitions": 3, "replication": 1},
    {"name": "scene.activated", "partitions": 3, "replication": 1},

    # Access Control
    {"name": "device.locked", "partitions": 5, "replication": 1},
    {"name": "device.unlocked", "partitions": 5, "replication": 1},
    {"name": "gate.opened", "partitions": 5, "replication": 1},
    {"name": "gate.closed", "partitions": 5, "replication": 1},
    {"name": "permission.granted", "partitions": 3, "replication": 1},
    {"name": "permission.revoked", "partitions": 3, "replication": 1},
    {"name": "temporary.code.created", "partitions": 3, "replication": 1},
    {"name": "temporary.code.used", "partitions": 3, "replication": 1},
    {"name": "temporary.code.expired", "partitions": 3, "replication": 1},
    {"name": "access.denied", "partitions": 3, "replication": 1},

    # Surveillance
    {"name": "camera.status.changed", "partitions": 5, "replication": 1},
    {"name": "motion.detected", "partitions": 5, "replication": 1},
    {"name": "person.detected", "partitions": 5, "replication": 1},
    {"name": "recording.started", "partitions": 5, "replication": 1},
    {"name": "recording.stopped", "partitions": 5, "replication": 1},

    # Scenarios Engine
    {"name": "scenario.created", "partitions": 3, "replication": 1},
    {"name": "scenario.updated", "partitions": 3, "replication": 1},
    {"name": "scenario.deleted", "partitions": 3, "replication": 1},
    {"name": "scenario.triggered", "partitions": 3, "replication": 1},
    {"name": "scenario.executed", "partitions": 3, "replication": 1},
    {"name": "command.sent", "partitions": 5, "replication": 1},

    # System
    {"name": "dead.letter.queue", "partitions": 1, "replication": 1},
    {"name": "audit.log", "partitions": 3, "replication": 1},
]


def wait_for_kafka(bootstrap_servers='kafka:9092', max_retries=30):
    """Ожидание готовности Kafka"""
    logger.info(f"Waiting for Kafka at {bootstrap_servers}...")

    for i in range(max_retries):
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers,
                client_id='topic-init'
            )
            admin_client.list_topics()
            logger.info("Kafka is ready!")
            return admin_client
        except NoBrokersAvailable:
            if i < max_retries - 1:
                logger.info(f"Kafka not ready, retrying in 2s... ({i + 1}/{max_retries})")
                time.sleep(2)
            else:
                logger.error("Cannot connect to Kafka after maximum retries")
                raise
        except Exception as e:
            logger.error(f"Error connecting to Kafka: {e}")
            time.sleep(2)

    raise Exception("Failed to connect to Kafka")


def create_topics(admin_client):
    """Создание топиков"""
    logger.info("Creating Kafka topics...")

    # Получаем существующие топики
    existing_topics = admin_client.list_topics()
    logger.info(f"Existing topics: {existing_topics}")

    # Подготавливаем новые топики
    new_topics = []
    for topic_config in TOPICS:
        if topic_config['name'] not in existing_topics:
            new_topics.append(NewTopic(
                name=topic_config['name'],
                num_partitions=topic_config['partitions'],
                replication_factor=topic_config['replication']
            ))
            logger.info(f"Will create: {topic_config['name']} "
                        f"(partitions: {topic_config['partitions']})")

    if not new_topics:
        logger.info("All topics already exist")
        return

    # Создаем топики
    try:
        admin_client.create_topics(new_topics)
        logger.info(f"Successfully created {len(new_topics)} topics")
    except TopicAlreadyExistsError:
        logger.warning("Some topics already exist")
    except Exception as e:
        logger.error(f"Error creating topics: {e}")
        raise


def verify_topics(admin_client):
    """Проверка созданных топиков"""
    logger.info("Verifying topics...")

    final_topics = admin_client.list_topics()
    created = [t['name'] for t in TOPICS if t['name'] in final_topics]
    missing = [t['name'] for t in TOPICS if t['name'] not in final_topics]

    logger.info(f"Topics created: {len(created)}/{len(TOPICS)}")
    if missing:
        logger.warning(f"Missing topics: {missing}")
    else:
        logger.info("All topics verified successfully!")

    return len(missing) == 0


def main():
    """Основная функция"""
    logger.info("Kafka Topics Initialization")

    # Параметры подключения
    bootstrap_servers = 'kafka:9092'

    try:
        # Ждем Kafka
        admin_client = wait_for_kafka(bootstrap_servers)

        # Создаем топики
        create_topics(admin_client)

        # Проверяем результат
        success = verify_topics(admin_client)

        if success:
            logger.info("Kafka topics initialization completed successfully")
        else:
            logger.error("Some topics are missing")
            exit(1)

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        exit(1)
    finally:
        if 'admin_client' in locals():
            admin_client.close()


if __name__ == "__main__":
    main()