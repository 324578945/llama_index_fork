"""Test vector store indexes."""

import os
from pathlib import Path
from typing import List

import pytest
from gpt_index.data_structs.node_v2 import Node

from gpt_index.indices.service_context import ServiceContext
from gpt_index.indices.vector_store.base import GPTVectorStoreIndex

from gpt_index.readers.schema.base import Document
from gpt_index.storage.storage_context import StorageContext
from gpt_index.vector_stores.faiss import FaissVectorStore
from gpt_index.vector_stores.types import NodeEmbeddingResult, VectorStoreQuery


def test_build_faiss(
    documents: List[Document],
    faiss_storage_context: StorageContext,
    mock_service_context: ServiceContext,
) -> None:
    """Test build GPTFaissIndex."""
    index = GPTVectorStoreIndex.from_documents(
        documents=documents,
        storage_context=faiss_storage_context,
        service_context=mock_service_context,
    )
    assert len(index.index_struct.nodes_dict) == 4

    node_ids = list(index.index_struct.nodes_dict.values())
    nodes = index.docstore.get_nodes(node_ids)
    node_texts = [node.text for node in nodes]
    assert "Hello world." in node_texts
    assert "This is a test." in node_texts
    assert "This is another test." in node_texts
    assert "This is a test v2." in node_texts


def test_faiss_insert(
    documents: List[Document],
    faiss_storage_context: StorageContext,
    mock_service_context: ServiceContext,
) -> None:
    """Test build GPTFaissIndex."""
    index = GPTVectorStoreIndex.from_documents(
        documents=documents,
        storage_context=faiss_storage_context,
        service_context=mock_service_context,
    )

    node_ids = index.index_struct.nodes_dict
    print(node_ids)

    # insert into index
    index.insert(Document(text="This is a test v3."))

    # check contents of nodes
    node_ids = index.index_struct.nodes_dict

    node_ids = list(index.index_struct.nodes_dict.values())
    nodes = index.docstore.get_nodes(node_ids)
    node_texts = [node.text for node in nodes]
    assert "This is a test v2." in node_texts
    assert "This is a test v3." in node_texts


@pytest.mark.skipif("CI" in os.environ, reason="no FAISS in CI")
def test_persist(tmp_path: Path) -> None:
    import faiss

    vector_store = FaissVectorStore(
        faiss_index=faiss.IndexFlatL2(5), persist_dir=str(tmp_path)
    )

    vector_store.add(
        [
            NodeEmbeddingResult(
                id="test id",
                node=Node("test text"),
                embedding=[0, 0, 0, 1, 1],
                doc_id="test_doc",
            )
        ]
    )

    result = vector_store.query(VectorStoreQuery(query_embedding=[0, 0, 0, 1, 1]))

    vector_store.persist()

    new_vector_store = FaissVectorStore.from_persist_dir(str(tmp_path))
    new_result = new_vector_store.query(
        VectorStoreQuery(query_embedding=[0, 0, 0, 1, 1])
    )

    assert result == new_result