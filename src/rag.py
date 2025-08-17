import os
import logging
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from config import KNOWLEDGE_BASE_PATH, FAISS_DB_PATH, EMBEDDING_MODEL
from huggingface_hub import InferenceClient

log = logging.getLogger("rag-system")

# Загрузка модели для создания векторов
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

class RAG:
    """Класс для работы с RAG-системой."""
    def __init__(self, llm_client: InferenceClient):
        self.vector_store = self._load_or_create_vector_store()
        self.llm_client = llm_client

    def _load_documents(self) -> List[Document]:
        """Загружает все поддерживаемые документы из папки knowledge_base."""
        documents = []
        for filename in os.listdir(KNOWLEDGE_BASE_PATH):
            filepath = os.path.join(KNOWLEDGE_BASE_PATH, filename)
            if filename.endswith(".pdf"):
                try:
                    loader = PyPDFLoader(filepath)
                    documents.extend(loader.load())
                    log.info(f"Loaded {len(documents)} pages from {filename}")
                except Exception as e:
                    log.error(f"Failed to load PDF file {filepath}: {e}")
        return documents

    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """Разделяет документы на части (чанки)."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        log.info(f"Split documents into {len(chunks)} chunks.")
        return chunks

    def _load_or_create_vector_store(self):
        """Загружает или создает векторную базу данных."""
        if os.path.exists(FAISS_DB_PATH):
            log.info("Loading existing vector store from file.")
            return FAISS.load_local(
                FAISS_DB_PATH,
                embeddings=embeddings,
                allow_dangerous_deserialization=True  # Необходимо для безопасности
            )
        else:
            log.info("Creating new vector store from documents.")
            documents = self._load_documents()
            if not documents:
                log.warning("No documents found to build a knowledge base.")
                return None
            chunks = self._split_documents(documents)
            vector_store = FAISS.from_documents(chunks, embeddings)
            vector_store.save_local(FAISS_DB_PATH)
            log.info(f"Vector store created and saved to {FAISS_DB_PATH}.")
            return vector_store

    def query(self, question: str, chat_history: List[dict]) -> str:
        """Ищет ответ на вопрос в векторной базе данных и генерирует ответ LLM."""
        if not self.vector_store:
            log.warning("Vector store not initialized. Cannot perform RAG query.")
            return ""

        # Создаем цепочку для поиска
        retriever = self.vector_store.as_retriever()
        
        # Генерация промпта
        chat_history_str = "\n".join([f"{entry['speaker']}: {entry['text']}" for entry in chat_history])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a helpful assistant for SUNERA Energy. Use the following context to answer the user's question. "
             "If you don't know the answer, politely suggest they contact the company. "
             "Context: {context}"
             ),
            ("human",
             f"Chat history: {chat_history_str}\n"
             f"User question: {question}"
             )
        ])
        
        # В этом месте мы интегрируемся с вашим клиентом Hugging Face
        # Это упрощенный вариант, так как LangChain-компоненты для HuggingFace бывают сложными в настройке.
        # Мы просто найдем релевантные документы и передадим их в LLM.
        
        docs = retriever.get_relevant_documents(question)
        context = "\n".join([doc.page_content for doc in docs])
        
        final_prompt = prompt.format(context=context, question=question)

        try:
            return self.llm_client.text_generation(
                prompt=final_prompt,
                max_new_tokens=500,
                do_sample=True,
                temperature=0.7
            )
        except Exception as e:
            log.error(f"RAG query with LLM failed: {e}")
            return ""

