from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    url="https://420e8a6e-fc6f-4c8f-b000-3949bb883609.us-east4-0.gcp.cloud.qdrant.io:6333",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.fLGNQ189tHd9DvLzD3y9dZYC2RWnUgkK_MRIRNuJ4cs",
)

print(qdrant_client.get_collections())
