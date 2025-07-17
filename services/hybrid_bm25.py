# pip install qdrant-client fastembed
import openai
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams,
    SparseVectorParams,
    Modifier,
    PointStruct,
    SparseVector,
)
from fastembed import SparseTextEmbedding

# OpenAI API 키
openai.api_key = "<YOUR_OPENAI_KEY>"

# 샘플 데이터
documents = [
    "Qdrant는 벡터 검색 데이터베이스입니다.",
    "BM25는 키워드 기반의 검색 알고리즘입니다.",
]

# 1) Dense 벡터(OpenAI 임베딩)
embedding_model = "text-embedding-3-small"
resp = openai.embeddings.create(input=documents, model=embedding_model)
dense_embeddings = [d.embedding for d in resp.data]

# 2) Sparse 벡터(BM25)
bm25_model = SparseTextEmbedding(model_name="Qdrant/bm25")
bm25_embeddings = list(bm25_model.embed(documents))

client = QdrantClient(host="localhost", port=6333)

# collection 생성
client.recreate_collection(
    collection_name="hybrid_example",
    # Dense vector
    vectors_config={
        "dense": VectorParams(size=len(dense_embeddings[0]), distance="Cosine")
    },
    # Sparse vector
    sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)},
)

points = [
    PointStruct(
        id=i,
        vector={"dense": dense_embeddings[i]},
        sparse_vector={
            "bm25": SparseVector(
                indices=bm25_embeddings[i].indices.tolist(),
                values=bm25_embeddings[i].values.tolist(),
            )
        },
        payload={"content": documents[i]},
    )
    for i in range(len(documents))
]
client.upsert(collection_name="hybrid_example", points=points)
