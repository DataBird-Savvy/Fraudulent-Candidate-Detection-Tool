
import os
from pinecone.grpc import PineconeGRPC as pinecone

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
from numpy import dot
from numpy.linalg import norm
from dotenv import load_dotenv
from logger import logger
from exception import ResumeFraudException

load_dotenv()

class PlagiarismDetector:
    def __init__(self, index_name="hybrid-index", namespace="resumes"):
        try:
            api_key = os.getenv("PINECONE_API_KEY")
            logger.info("Initializing Pinecone...")
            
            self.pc = pinecone(api_key=api_key)

            self.index = self.pc.Index(host="https://hybrid-index-ik95w3g.svc.aped-4627-b74a.pinecone.io")
            self.namespace = namespace
            logger.info(f"Pinecone index '{index_name}' connected successfully. Namespace: '{namespace}'")

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {e}")
            raise ResumeFraudException("Pinecone initialization failed.") from e
   
    @staticmethod
    def load_and_chunk(file_path: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List:
        try:
            filename = os.path.basename(file_path)
            logger.info(f"Loading and chunking document: {filename}")

            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif filename.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
            else:
                raise ValueError("Unsupported file format. Use PDF or DOCX.")

            docs = loader.load()
            for doc in docs:
                doc.metadata["source_file"] = filename

            splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = splitter.split_documents(docs)

            for i, chunk in enumerate(chunks):
                chunk.metadata["id"] = f"{filename}_chunk{i}"

            logger.info(f"Document '{filename}' split into {len(chunks)} chunks.")
            return chunks

        except Exception as e:
            logger.error(f"Error loading/chunking document '{file_path}': {e}")
            raise ResumeFraudException(f"Failed to load and chunk document: {file_path}") from e

    
    def get_hybrid_embeddings(self,text: str):
        try:
            logger.info("Generating hybrid embeddings...")
            dense_emb = self.pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=text,
                parameters={"input_type": "query", "truncate": "END"}
            )[0]['values']

            sparse_emb_raw = self.pc.inference.embed(
                model="pinecone-sparse-english-v0",
                inputs=text,
                parameters={"input_type": "query", "truncate": "END"}
            )[0]

            sparse_emb = {
                'indices': sparse_emb_raw['sparse_indices'],
                'values': sparse_emb_raw['sparse_values']
            }

            return dense_emb, sparse_emb

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise ResumeFraudException("Failed to generate embeddings.") from e

   
    def check_resume_chunks(self, file_path: str, top_k: int = 1,threshold: float = 0.85) -> List[Dict]:
        try:
            chunks = self.load_and_chunk(file_path)
            plagiarism_matches = []

            logger.info(f"Checking plagiarism for {len(chunks)} chunks in '{file_path}' against Pinecone index.")

            for chunk in chunks:
                dense_vector, sparse_vector = self.get_hybrid_embeddings(chunk.page_content)
                query_response = self.index.query(
                    namespace=self.namespace,
                    top_k=top_k,
                    vector=dense_vector,
                    sparse_vector=sparse_vector,
                    include_values=False,
                    include_metadata=True
                )
                for match in query_response.get('matches', []):
                    if match['score'] >= threshold:
                        plagiarism_matches.append({
                            # 'chunk_id': chunk.metadata['id'],
                            # 'matched_id': match['id'],
                            'score': match['score'],
                            'source_file': match['metadata']['source_file'],
                        })


            logger.info(f"Found {len(plagiarism_matches)} potential plagiarism matches for '{file_path}'.")
            logger.debug(f"Plagiarism matches: {plagiarism_matches}")
            return plagiarism_matches

        except Exception as e:
            logger.error(f"Error checking resume chunks for plagiarism: {e}")
            raise ResumeFraudException(f"Failed plagiarism check for: {file_path}") from e

    
    def check_with_jd(self, resume_path: str, jd_text: str, threshold: float = 0.7) -> dict:
        try:
            chunks = self.load_and_chunk(resume_path)
            total_score = 0.0
            logger.info(f"Comparing resume '{resume_path}' with its JD...")

            for chunk in chunks:
                dense_resume, sparse_resume = self.get_hybrid_embeddings(chunk.page_content)
                dense_jd, sparse_jd = self.get_hybrid_embeddings(jd_text)

                dense_score = dot(dense_resume, dense_jd) / (norm(dense_resume) * norm(dense_jd) + 1e-10)
                
                resume_sparse_dict = dict(zip(sparse_resume['indices'], sparse_resume['values']))
                jd_sparse_dict = dict(zip(sparse_jd['indices'], sparse_jd['values']))
                common_indices = set(resume_sparse_dict.keys()) & set(jd_sparse_dict.keys())
                sparse_score = (
                    sum(resume_sparse_dict[i] * jd_sparse_dict[i] for i in common_indices) /
                    (sum(resume_sparse_dict.values()) + 1e-10)
                    if common_indices else 0.0
                )

                total_score += 0.3 * dense_score + 0.7 * sparse_score

            avg_score = total_score / len(chunks) if chunks else 0.0
            logger.info(f"Average similarity score between resume and JD: {avg_score:.4f}")

            result = {
                
                "avg_score": avg_score,
                
                "match": avg_score >= threshold
            }
            return result

        except Exception as e:
            logger.error(f"Error checking resume vs JD: {e}")
            raise ResumeFraudException(f"Failed JD comparison for: {resume_path}") from e
