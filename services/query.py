from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from pprint import pprint

client = QdrantClient(url="http://localhost:6333")

search_result = client.query_points(
    collection_name="test_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    query_filter=Filter(
        must=[FieldCondition(key="city", match=MatchValue(value="London"))]
    ),
    with_payload=True,
    limit=3,
).points

pprint(search_result)

# fastembed                 0.7.1
from fastembed import SparseTextEmbedding

bm25_model = SparseTextEmbedding(model_name="Qdrant/bm25")

# 1. 쿼리 문장 입력
query = "키워드 검색"
collection_name = "bm25_example"

# 2. 쿼리용 BM25 임베딩 생성
query_embedding = next(bm25_model.query_embed(query))
# 검색 텍스트
query = "키워드 검색"

import openai

# Dense 쿼리 벡터
q_dense = (
    openai.embeddings.create(input=[query], model=embedding_model).data[0].embedding
)
# Sparse 쿼리 벡터
q_sparse = next(bm25_model.query_embed(query))

# Hybrid 검색
results = client.search(
    collection_name="hybrid_example",
    query_vector={"dense": q_dense},
    query_sparse_vector={
        "bm25": {
            "indices": q_sparse.indices.tolist(),
            "values": q_sparse.values.tolist(),
        }
    },
    limit=3,
)

for r in results:
    print(r.payload["content"], r.score)
