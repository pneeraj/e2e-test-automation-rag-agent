"""
Builds (or loads a cached) Chroma vector store over the markdown notes in
knowledge_base/. This is deliberately small - a handful of real notes about
patterns the team has actually hit - not a crawl of the whole internet. It's
enough to make the RAG step return something more useful than a blank page.
"""
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent / "knowledge_base"
PERSIST_DIR = Path(__file__).resolve().parent / ".chroma"


def load_or_build_vector_store() -> Chroma:
    embeddings = OpenAIEmbeddings()

    if PERSIST_DIR.exists():
        return Chroma(persist_directory=str(PERSIST_DIR), embedding_function=embeddings)

    loader = DirectoryLoader(str(KNOWLEDGE_BASE_DIR), glob="*.md", loader_cls=TextLoader)
    documents = loader.load()
    chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(documents)

    return Chroma.from_documents(chunks, embeddings, persist_directory=str(PERSIST_DIR))


if __name__ == "__main__":
    load_or_build_vector_store()
    print(f"Vector store ready at {PERSIST_DIR}")
