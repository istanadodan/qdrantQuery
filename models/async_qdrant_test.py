# 필요한 패키지: pip install qdrant-client numpy

import asyncio
import numpy as np
from qdrant_client import AsyncQdrantClient, models


async def main():
    # 1. 비동기 Qdrant 클라이언트 생성
    client = AsyncQdrantClient(host="localhost", port=6333)

    collection_name = "async_sample_collection"
    vector_dim = 8

    # 2. 컬렉션 생성 (존재하지 않으면)
    if not await client.collection_exists(collection_name):
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_dim, distance=models.Distance.COSINE
            ),
        )

    # 3. 임의의 데이터 및 벡터 준비
    documents = [
        "사과는 빨갛다",
        "바나나는 노랗다",
        "하늘은 파랗다",
        "초록색 잎사귀",
    ]
    vectors = np.random.rand(len(documents), vector_dim)

    # 4. 벡터DB에 데이터 업로드 (비동기)
    points = [
        models.PointStruct(
            id=i, vector=vectors[i].tolist(), payload={"text": documents[i]}
        )
        for i in range(len(documents))
    ]
    await client.upsert(collection_name=collection_name, points=points)

    # 5. 검색 쿼리(임베딩) 생성 및 유사도 검색 (비동기)
    query_vector = np.random.rand(vector_dim).tolist()
    results = await client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=2,  # 상위 2개 결과 반환
    )

    # 6. 결과 출력
    for hit in results.points:
        print(f"ID: {hit.id}, Score: {hit.score}, 문서: {hit.payload['text']}")

    # (필요시) 컬렉션 삭제
    # await client.delete_collection(collection_name=collection_name)


# 비동기 실행
if __name__ == "__main__":
    asyncio.run(main())
