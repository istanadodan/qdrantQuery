from qdrant_client.models import PointStruct, NamedVector, VectorParams, Distance
from vdb_client_conn_test import qdrant_client as client

# Qdrant에 연결
# client = QdrantClient(host="localhost", port=6333)


def create_hybrid_db() -> None:
    # 1. Hybrid 인덱스는 보통 named vectors 사용 (예: dense/sparse)
    collection_name = "test_collection"
    # vectors_config = {
    #     "dense": {"size": 384, "distance": "Cosine"},
    #     "sparse": {"size": 1000, "distance": "Cosine"},  # 실제 모델 output에 맞게 조정
    # }

    vectors_config = {
        "dense": VectorParams(size=768, distance=Distance.COSINE),
        "sparse": VectorParams(size=1000, distance=Distance.DOT),  # 실제로는 항상 Dot
    }

    # 2. 컬랙션 생성(이미 존재한다면 생략)
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=vectors_config,
    )

    # 3. 포인트 준비 (각 벡터는 이름 지정)
    dense_vector = [0.1] * 384  # 예시 dense 벡터
    sparse_vector = [
        0.0
    ] * 1000  # 예시 sparse(대부분 0), 실제 sparse 모델 output 사용해야 함

    point = PointStruct(
        id=1,
        vector={
            "dense": dense_vector,
            "sparse": sparse_vector,
        },
        payload={"doc": "이것은 하이브리드 검색 예제입니다!"},
    )

    # 4. 벡터 insert
    client.upsert(
        collection_name=collection_name,
        points=[point],
        wait=True,
    )


def create_general_db() -> None:
    import numpy as np

    # 2-1 일반 저장
    # dense 벡터 컬렉션 생성 (예: 임베딩 차원 1536, Cosine 유사도)
    if not client.collection_exists(collection_name="my_dense_collection"):
        client.recreate_collection(
            collection_name="my_dense_collection",
            vectors_config=VectorParams(
                size=1536,  # 임베딩 벡터의 차원에 맞게 설정
                distance=Distance.COSINE,  # 또는 Distance.DOT, Distance.EUCLID 참고
            ),
        )

    # 샘플 dense 벡터 생성 (예: 1536차원, 실제 임베딩 사용 권장)
    def generate_fake_embedding():
        return np.random.rand(1536).tolist()

    # 포인트 데이터 생성
    points = [
        PointStruct(
            id=1,
            vector=generate_fake_embedding(),
            payload={"text": "Qdrant는 고속 벡터 검색 엔진입니다."},
        ),
        PointStruct(
            id=2,
            vector=generate_fake_embedding(),
            payload={"text": "파이썬을 사용하여 Qdrant에 데이터를 추가할 수 있습니다."},
        ),
        PointStruct(
            id=3,
            vector=generate_fake_embedding(),
            payload={"text": "이 문장은 텍스트 임베딩을 사용한 예시 데이터입니다."},
        ),
    ]

    # 벡터 upsert (insert or update)
    client.upsert(collection_name="my_dense_collection", points=points)


if __name__ == "__main__":
    create_general_db()
