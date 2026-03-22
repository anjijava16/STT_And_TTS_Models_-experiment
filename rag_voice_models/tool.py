import os
from typing import List

from llama_index.core.indices import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.settings import Settings
from llama_index.core.storage import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv, find_dotenv
from pipecat.services.llm_service import FunctionCallParams
from qdrant_client import QdrantClient

load_dotenv(find_dotenv())

Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
# Local Qdrant connection
#qdrant_connector = QdrantClient(url="http://localhost:6333", api_key="th3s3cr3tk3y")
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Document
import os
# connect to Qdrant Cloud
qdrant_connector = QdrantClient(
    url=os.getenv("QDRANT_API_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    cloud_inference=True
)


async def retrieve_leukemia_knowledge_base(params: FunctionCallParams, query: str):
    """
    Use this tool to retrieve knowledge about leukemia.

    Args:
        query: str, user query to search the knowledge base
    """
    try:
        # Extract query from the arguments
        print(f"Calling function")

        if not query:
            await params.result_callback({"error": "No query provided"})
            return

        if qdrant_connector.collection_exists(collection_name=os.getenv("COLLECTION_NAME", "leukemia_knowledge_base")):
            vector_store = QdrantVectorStore(
                client=qdrant_connector,
                collection_name=os.getenv("COLLECTION_NAME", "leukemia_knowledge_base")
            )
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                storage_context=storage_context
            )
            retriever = index.as_retriever(top_k=15)

            context = ''
            nodes: List[NodeWithScore] = retriever.retrieve(query)
            for node in nodes:
                context += node.text

            print(f"Context retrieved: {context}")
            await params.result_callback(context)
        else:
            await params.result_callback({
                "error": "Collection does not exist in Qdrant"
            })
    except Exception as e:
        print(f"Error in retrieve_leukemia_knowledge_base: {str(e)}")
        await params.result_callback({
            "error": f"Failed to get context: {str(e)}"
        })
