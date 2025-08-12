"""
Confluent Kafka 클라이언트 모듈 (kafka_influence) 사용 예제
confluent-kafka 2.4.0 버전 기준
Producer와 Consumer의 입출력 처리 중심
"""

from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
import threading
import uuid

# 로깅 설정
logger = logging.getLogger(__name__)

bootstrap_servers = (
    # "kafka-0.kafka-svc.default.svc.cluster.local:9092,"
    # "kafka-1.kafka-svc.default.svc.cluster.local:9092,"
    "127.0.0.1:9092"
)


class KafkaInfluenceProducer:
    """Confluent Kafka Producer 클래스"""

    def __init__(self, bootstrap_servers: str = bootstrap_servers, **config):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "acks": "all",  # 모든 replica 확인
            "retries": 3,
            "batch.size": 16384,
            "linger.ms": 1,
            "queue.buffering.max.kbytes": 33554432,
            "compression.type": "snappy",
            "enable.idempotence": True,  # 중복 방지
            **config,
        }
        self._initialize_producer()

    def _initialize_producer(self):
        """Producer 초기화"""
        try:
            self.producer = Producer(self.config)
            logger.info("Confluent Kafka Producer 초기화 완료")
        except Exception as e:
            logger.error(f"Producer 초기화 실패: {e}")
            raise

    def _delivery_callback(self, err, msg):
        """메시지 전송 결과 콜백"""
        if err is not None:
            logger.error(f"메시지 전송 실패: {err}")
        else:
            logger.info(
                f"메시지 전송 성공 - Topic: {msg.topic()}, "
                f"Partition: {msg.partition()}, Offset: {msg.offset()}"
            )

    def publish_message(
        self,
        topic: str,
        message: Dict[Any, Any],
        key: Optional[str] = None,
        callback: Optional[Callable] = None,
    ):
        """단일 메시지 발행"""
        try:
            # 메시지에 메타데이터 추가
            message["timestamp"] = datetime.now().isoformat()
            message["message_id"] = str(uuid.uuid4())

            # JSON 직렬화
            value = json.dumps(message, ensure_ascii=False)

            # 메시지 전송 (비동기)
            self.producer.produce(
                topic=topic,
                value=value.encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                callback=callback or self._delivery_callback,
            )

            # 즉시 전송하려면 poll 호출
            self.producer.poll(0)

            return {
                "success": True,
                "message_id": message["message_id"],
                "topic": topic,
                "key": key,
            }

        except BufferError as e:
            logger.error(f"Producer 버퍼 가득참: {e}")
            return {"success": False, "error": "Buffer full"}
        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            return {"success": False, "error": str(e)}

    def publish_message_sync(
        self,
        topic: str,
        message: Dict[Any, Any],
        key: Optional[str] = None,
        timeout: float = 10.0,
    ):
        """동기 방식 메시지 발행"""
        try:
            message["timestamp"] = datetime.now().isoformat()
            message["message_id"] = str(uuid.uuid4())

            value = json.dumps(message, ensure_ascii=False)

            # 동기 전송을 위해 Future 객체 사용
            future = self.producer.produce(
                topic=topic,
                value=value.encode("utf-8"),
                key=key.encode("utf-8") if key else None,
            )

            # 전송 완료까지 대기
            self.producer.flush(timeout)

            return {
                "success": True,
                "message_id": message["message_id"],
                "topic": topic,
                "key": key,
            }

        except Exception as e:
            logger.error(f"동기 메시지 전송 실패: {e}")
            return {"success": False, "error": str(e)}

    def publish_batch_messages(
        self, topic: str, messages: List[Dict], key_field: Optional[str] = None
    ):
        """배치 메시지 발행"""
        results = []
        failed_count = 0

        try:
            for idx, message in enumerate(messages):
                key = message.get(key_field) if key_field else f"batch_{idx}"

                try:
                    message["timestamp"] = datetime.now().isoformat()
                    message["message_id"] = str(uuid.uuid4())

                    value = json.dumps(message, ensure_ascii=False)

                    self.producer.produce(
                        topic=topic,
                        value=value.encode("utf-8"),
                        key=str(key).encode("utf-8"),
                        callback=self._delivery_callback,
                    )

                    results.append(
                        {
                            "success": True,
                            "message_id": message["message_id"],
                            "index": idx,
                        }
                    )

                except Exception as e:
                    failed_count += 1
                    results.append({"success": False, "error": str(e), "index": idx})

                # 배치 처리 중 중간 poll
                if idx % 100 == 0:
                    self.producer.poll(0)

            # 모든 메시지 전송 완료 대기
            self.producer.flush()

            success_count = len(messages) - failed_count
            logger.info(
                f"배치 메시지 전송 완료 - 성공: {success_count}/{len(messages)}"
            )

            return {
                "total": len(messages),
                "success": success_count,
                "failed": failed_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"배치 메시지 전송 실패: {e}")
            return {
                "total": len(messages),
                "success": 0,
                "failed": len(messages),
                "error": str(e),
            }

    def close(self):
        """Producer 연결 종료"""
        if self.producer:
            # 남은 메시지 모두 전송
            self.producer.flush()
            logger.info("Producer 연결 종료")


class KafkaInfluenceConsumer:
    """Confluent Kafka Consumer 클래스"""

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: str = bootstrap_servers,
        **config,
    ):
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.consumer = None
        self.running = False

        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,  # 수동 커밋
            "max.poll.interval.ms": 300000,
            "session.timeout.ms": 10000,
            "fetch.min.bytes": 1,
            "fetch.wait.max.ms": 500,
            **config,
        }
        self._initialize_consumer()

    def _initialize_consumer(self):
        """Consumer 초기화"""
        try:
            self.consumer = Consumer(self.config)
            self.consumer.subscribe(self.topics)
            logger.info(
                f"Consumer 초기화 완료 - Topics: {self.topics}, Group: {self.group_id}"
            )
        except Exception as e:
            logger.error(f"Consumer 초기화 실패: {e}")
            raise

    def consume_messages(
        self,
        message_handler: Optional[Callable] = None,
        max_messages: Optional[int] = None,
        timeout: float = 1.0,
    ):
        """메시지 소비 (동기 방식)"""
        consumed_count = 0
        messages = []

        try:
            self.running = True

            while self.running:
                # 메시지 폴링
                msg = self.consumer.poll(timeout)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # 파티션 끝에 도달
                        logger.info(
                            f"파티션 끝 도달: {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
                        )
                        continue
                    else:
                        logger.error(f"Consumer 에러: {msg.error()}")
                        break

                # 메시지 처리
                value = msg.value().decode("utf-8")
                key = msg.key().decode("utf-8") if msg.key() else None
                try:
                    value = json.loads(msg.value().decode("utf-8"))

                except json.JSONDecodeError as e:
                    pass

                message_data = {
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                    "key": key,
                    "value": value,
                    "timestamp": (
                        msg.timestamp()[1] if msg.timestamp()[0] != -1 else None
                    ),
                    "consumed_at": datetime.now().isoformat(),
                }

                messages.append(message_data)
                consumed_count += 1

                # 메시지 처리 핸들러 호출
                if message_handler:
                    try:
                        message_handler(message_data)
                    except Exception as e:
                        logger.error(f"메시지 핸들러 에러: {e}")

                logger.info(
                    f"메시지 수신 - Topic: {msg.topic()}, "
                    f"Partition: {msg.partition()}, Offset: {msg.offset()}, data: {value}, key:{key}"
                )

                # 오프셋 커밋
                self.consumer.commit(msg)

                # 최대 메시지 수 확인
                if max_messages and consumed_count >= max_messages:
                    break

            logger.info(f"메시지 소비 완료 - 총 {consumed_count}개")
            return messages

        except KafkaException as e:
            logger.error(f"Kafka 예외: {e}")
            return messages
        except Exception as e:
            logger.error(f"메시지 소비 중 에러: {e}")
            return messages

    def consume_messages_async(
        self, message_handler: Callable, max_messages: Optional[int] = None
    ):
        """메시지 소비 (비동기 방식)"""

        def consume_worker():
            self.consume_messages(message_handler, max_messages)

        thread = threading.Thread(target=consume_worker, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Consumer 중지"""
        self.running = False
        logger.info("Consumer 중지 요청")

    def close(self):
        """Consumer 연결 종료"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Consumer 연결 종료")


class KafkaInfluenceAdmin:
    """Kafka 관리 클래스"""

    def __init__(self, bootstrap_servers: str = bootstrap_servers):
        self.admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})

    def create_topic(
        self, topic_name: str, num_partitions: int = 1, replication_factor: int = 1
    ):
        """토픽 생성"""
        try:
            topic = NewTopic(topic_name, num_partitions, replication_factor)
            futures = self.admin_client.create_topics([topic])

            for topic, future in futures.items():
                try:
                    future.result()
                    logger.info(f"토픽 '{topic}' 생성 완료")
                except Exception as e:
                    logger.error(f"토픽 '{topic}' 생성 실패: {e}")
        except Exception as e:
            logger.error(f"토픽 생성 중 에러: {e}")


# 사용 예제 및 테스트 함수들


def example_producer_usage():
    """Producer 사용 예제"""
    print("\n=== Confluent Kafka Producer 사용 예제 ===")

    producer = KafkaInfluenceProducer()

    # 단일 메시지 전송 (비동기)
    message = {
        "user_id": "user_001",
        "action": "login",
        "data": {"ip": "192.168.1.100", "device": "mobile"},
    }

    result = producer.publish_message("user_events", message, key="user_001")
    print(f"비동기 메시지 전송 결과: {result}")

    # 단일 메시지 전송 (동기)
    sync_result = producer.publish_message_sync("user_events", message, key="user_001")
    print(f"동기 메시지 전송 결과: {sync_result}")

    # 배치 메시지 전송
    batch_messages = [
        {"user_id": "user_002", "action": "view_product", "product_id": "prod_123"},
        {"user_id": "user_003", "action": "add_to_cart", "product_id": "prod_456"},
        {"user_id": "user_004", "action": "purchase", "order_id": "order_789"},
    ]

    batch_result = producer.publish_batch_messages(
        "user_events", batch_messages, "user_id"
    )
    print(f"배치 메시지 전송 결과: {batch_result}")

    producer.close()


def example_consumer_usage():
    """Consumer 사용 예제"""
    print("\n=== Confluent Kafka Consumer 사용 예제 ===")

    # 메시지 처리 핸들러 정의
    def handle_message(message_data):
        """수신된 메시지 처리"""
        value = message_data["value"]
        print(f"메시지 처리: {value.get('user_id')} - {value.get('action')}")

        # 비즈니스 로직 처리
        if value.get("action") == "purchase":
            print(f"  구매 처리: 주문 ID {value.get('order_id')}")
        elif value.get("action") == "login":
            print(f"  로그인 처리: IP {value.get('data', {}).get('ip')}")

    consumer = KafkaInfluenceConsumer(["user_events"], "example_group")

    # 동기 방식으로 메시지 소비 (최대 5개)
    print("동기 방식으로 메시지 소비 시작...")
    messages = consumer.consume_messages(handle_message, max_messages=5)
    print(f"소비된 메시지 수: {len(messages)}")

    consumer.close()


def example_async_consumer():
    """비동기 Consumer 사용 예제"""
    print("\n=== 비동기 Consumer 사용 예제 ===")

    def async_message_handler(message_data):
        value = message_data["value"]
        print(f"비동기 처리: {value.get('user_id')} - {value.get('action')}")

    consumer = KafkaInfluenceConsumer(["user_events"], "async_group")

    # 비동기로 메시지 소비 시작
    thread = consumer.consume_messages_async(async_message_handler, max_messages=3)

    # 메인 스레드에서 다른 작업 수행
    print("메인 스레드에서 다른 작업 진행...")
    time.sleep(5)

    # Consumer 중지
    consumer.stop()
    thread.join(timeout=2)
    consumer.close()


def example_admin_usage():
    """Admin 사용 예제"""
    print("\n=== Kafka Admin 사용 예제 ===")

    admin = KafkaInfluenceAdmin()

    # 토픽 생성
    admin.create_topic("test_topic", num_partitions=3, replication_factor=1)


def full_example():
    """완전한 예제: Producer와 Consumer 함께 사용"""
    print("\n=== 완전한 예제: Producer와 Consumer ===")

    # 토픽 생성
    admin = KafkaInfluenceAdmin()
    admin.create_topic("real_time_events", num_partitions=2)

    time.sleep(1)  # 토픽 생성 대기

    # Consumer를 먼저 시작 (비동기)
    def message_processor(msg):
        print(f"실시간 처리: {msg['value']}")

    consumer = KafkaInfluenceConsumer(["real_time_events"], "demo_group")
    thread = consumer.consume_messages_async(message_processor, max_messages=5)

    # Consumer가 준비될 시간
    time.sleep(2)

    # Producer로 메시지 전송
    producer = KafkaInfluenceProducer()

    for i in range(5):
        message = {
            "event_id": f"event_{i}",
            "type": "demo",
            "data": f"데모 데이터 {i}",
            "sequence": i,
        }
        result = producer.publish_message("real_time_events", message, f"demo_{i}")
        print(f"메시지 {i} 전송: {result['success']}")
        time.sleep(0.5)

    # 정리
    time.sleep(3)
    consumer.stop()
    thread.join(timeout=5)

    producer.close()
    consumer.close()


if __name__ == "__main__":
    # 각 예제 실행
    try:
        # Admin 예제
        # example_admin_usage()
        # time.sleep(1)

        # Producer 예제
        example_producer_usage()
        time.sleep(2)

        # Consumer 예제
        example_consumer_usage()
        time.sleep(2)

        # 비동기 Consumer 예제
        example_async_consumer()
        time.sleep(2)

        # 전체 예제
        full_example()

    except Exception as e:
        logger.error(f"예제 실행 중 에러: {e}")
        print("Kafka 서버가 실행 중인지 확인해주세요!")
        print("설치 명령: pip install confluent-kafka==2.4.0")
