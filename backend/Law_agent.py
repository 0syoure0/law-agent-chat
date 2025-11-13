#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
공무원 법령 AI 어시스턴트
작성일: 2025-11-06

사용법:
    python law_agent.py

필수 환경 변수:
    GEMINI_API_KEY: Google Gemini API 키
"""

# .env 파일 로드 (이 부분을 주석 밖으로!)
from dotenv import load_dotenv
from pathlib import Path

# 현재 스크립트가 있는 디렉토리의 .env 파일 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

import os
import sys
import time
import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import re

# 서드파티 라이브러리 임포트
# 서드파티 라이브러리 임포트
try:
    import google.generativeai as genai
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS  # ✅ 수정
    from langchain_community.embeddings import HuggingFaceEmbeddings  # ✅ 수정
except ImportError as e:
    print(f"필요한 라이브러리를 설치해주세요: {e}")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LawAgentConfig:
    """법령 에이전트 설정"""
    model_name: str = "gemini-2.0-flash-exp"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    chunk_size: int = 800  # 법령은 더 큰 청크 필요
    chunk_overlap: int = 200  # 조문 연속성 유지
    top_k_results: int = 7  # 더 많은 관련 조문 검색
    temperature: float = 0.1  # 법령은 정확성이 중요
    max_history: int = 15  # 법률 상담은 컨텍스트가 중요


class LawDocumentLoader:
    """법령 문서 로더"""
    
    @staticmethod
    def load_txt(file_path: str) -> str:
        """텍스트 파일 로드"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def load_pdf(file_path: str) -> str:
        """PDF 파일 로드"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            logger.error("PyPDF2가 설치되지 않았습니다. pip install pypdf 를 실행하세요.")
            return ""
        except Exception as e:
            logger.error(f"PDF 로드 실패: {e}")
            return ""
    
    @staticmethod
    def load_docx(file_path: str) -> str:
        """DOCX 파일 로드"""
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            logger.error("python-docx가 설치되지 않았습니다. pip install python-docx 를 실행하세요.")
            return ""
        except Exception as e:
            logger.error(f"DOCX 로드 실패: {e}")
            return ""
    
    @classmethod
    def load_document(cls, file_path: str) -> str:
        """파일 확장자에 따라 적절한 로더 선택"""
        ext = os.path.splitext(file_path)[1].lower()
        
        loaders = {
            '.txt': cls.load_txt,
            '.pdf': cls.load_pdf,
            '.docx': cls.load_docx,
        }
        
        loader = loaders.get(ext)
        if loader:
            logger.info(f"법령 파일 로드 중: {file_path}")
            return loader(file_path)
        else:
            logger.warning(f"지원하지 않는 파일 형식: {ext}")
            return ""


class LawKnowledgeBase:
    """법령 지식 베이스"""
    
    def __init__(self, config: LawAgentConfig):
        self.config = config
        self.vectorstore = None
        self.embeddings = None
        self.document_count = 0
        self.law_metadata = {}  # 법령명, 조문 등 메타데이터
        
    def extract_law_structure(self, text: str) -> List[Dict]:
        """
        법령 구조 파싱 (조문, 항, 호 등)
        """
        law_sections = []
        
        # 조문 패턴: 제1조, 제2조 등
        article_pattern = r'제\s*(\d+)\s*조(?:\s*\(([^)]+)\))?'
        
        # 현재 조문 추적
        current_article = None
        current_title = None
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 조문 시작 감지
            match = re.match(article_pattern, line)
            if match:
                # 이전 조문 저장
                if current_article and current_content:
                    law_sections.append({
                        'article': current_article,
                        'title': current_title,
                        'content': '\n'.join(current_content)
                    })
                
                # 새 조문 시작
                current_article = f"제{match.group(1)}조"
                current_title = match.group(2) if match.group(2) else ""
                current_content = [line]
            else:
                # 조문 내용 추가
                if current_article:
                    current_content.append(line)
        
        # 마지막 조문 저장
        if current_article and current_content:
            law_sections.append({
                'article': current_article,
                'title': current_title,
                'content': '\n'.join(current_content)
            })
        
        return law_sections
    
    def create_knowledge_base(self, file_paths: List[str]) -> bool:
        """
        법령 파일로부터 지식 베이스 생성
        
        Args:
            file_paths: 법령 파일 경로 리스트
            
        Returns:
            성공 여부
        """
        try:
            all_docs = []
            
            # 모든 법령 파일 로드
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    logger.warning(f"파일을 찾을 수 없습니다: {file_path}")
                    continue
                    
                text = LawDocumentLoader.load_document(file_path)
                if text:
                    # 법령 구조 파싱
                    law_sections = self.extract_law_structure(text)
                    
                    if law_sections:
                        logger.info(f"{file_path}: {len(law_sections)}개 조문 발견")
                        all_docs.append((file_path, text, law_sections))
                    else:
                        # 구조화되지 않은 법령은 전체 텍스트로 처리
                        all_docs.append((file_path, text, None))
            
            if not all_docs:
                logger.error("로드된 법령 문서가 없습니다.")
                return False
            
            # 법령 전용 텍스트 분할기
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
                # 법령 구조 우선 분리
                separators=[
                    "\n제", "제", "\n\n",  # 조문 우선
                    "\n①", "\n②", "\n③",  # 항
                    "\n1.", "\n2.", "\n3.",  # 호
                    "。", ".", "\n", " ", ""
                ]
            )
            
            # 문서 청킹
            documents = []
            
            for file_path, text, law_sections in all_docs:
                if law_sections:
                    # 조문별로 문서 생성
                    for section in law_sections:
                        article_text = f"{section['article']}"
                        if section['title']:
                            article_text += f" ({section['title']})"
                        article_text += f"\n{section['content']}"
                        
                        documents.append(
                            Document(
                                page_content=article_text,
                                metadata={
                                    "source": file_path,
                                    "article": section['article'],
                                    "title": section['title'],
                                    "type": "article"
                                }
                            )
                        )
                else:
                    # 구조화되지 않은 문서는 청킹
                    chunks = text_splitter.split_text(text)
                    for i, chunk in enumerate(chunks):
                        documents.append(
                            Document(
                                page_content=chunk,
                                metadata={
                                    "source": file_path,
                                    "chunk_id": i,
                                    "type": "chunk"
                                }
                            )
                        )
            
            self.document_count = len(documents)
            logger.info(f"총 {self.document_count}개의 법령 조각 생성")
            
            # 임베딩 모델 초기화
            logger.info("법령 임베딩 모델 로드 중...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.config.embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # FAISS 벡터 스토어 생성
            logger.info("법령 벡터 데이터베이스 생성 중...")
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            logger.info("✅ 법령 지식 베이스 생성 완료")
            
            return True
            
        except Exception as e:
            logger.error(f"법령 지식 베이스 생성 실패: {e}")
            return False
    
    def search(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        법령 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            
        Returns:
            관련 법령 조문 리스트
        """
        if not self.vectorstore:
            logger.error("법령 데이터베이스가 초기화되지 않았습니다.")
            return []
        
        k = k or self.config.top_k_results
        try:
            # 유사도 점수와 함께 검색
            docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # 법령은 더 관대한 임계값 (조문이 길고 복잡)
            threshold = 2.0
            filtered_docs = [doc for doc, score in docs_and_scores if score < threshold]
            
            logger.info(f"법령 검색 완료: {len(filtered_docs)}개의 관련 조문 발견")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"법령 검색 실패: {e}")
            return []


class LawAgent:
    """공무원 법령 AI 어시스턴트"""
    
    def __init__(self, api_key: str, knowledge_base: LawKnowledgeBase, config: LawAgentConfig):
        self.config = config
        self.knowledge_base = knowledge_base
        
        # LLM 초기화
        genai.configure(api_key=api_key)
        self.llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=api_key,
            temperature=config.temperature
        )
        
        # 법령 전문 시스템 메시지
        self.system_message = SystemMessage(content="""
당신은 대한민국 공무원을 위한 법령 전문 AI 어시스턴트입니다.

**역할 및 책임:**
- 공무원이 업무 수행 시 필요한 법령 정보를 정확하게 제공
- 법령의 해석과 적용에 대한 명확한 안내
- 관련 조문과 근거를 명시하여 신뢰성 확보

**답변 원칙:**
1. 제공된 법령 자료에 엄격히 기반하여 답변합니다.
2. 법령 조문을 인용할 때는 정확한 조문 번호와 내용을 명시합니다.
3. 법령에 명시되지 않은 사항은 "제공된 법령에서 찾을 수 없습니다"라고 명확히 밝힙니다.
4. 법령 해석이 필요한 경우, 가능한 해석을 제시하되 최종 판단은 담당 부서나 법무팀에 문의하도록 안내합니다.
5. 여러 조문이 관련된 경우, 모두 언급하고 상호 관계를 설명합니다.
6. 법령의 목적, 배경, 취지를 함께 설명하여 이해를 돕습니다.
7. 실무 적용 시 유의사항이 있다면 함께 안내합니다.

**답변 형식:**
1. 관련 법령 조문 명시
2. 조문 내용 설명
3. 실무 적용 가이드
4. 추가 참고사항 (필요시)

**주의사항:**
- 법령 해석은 참고용이며, 최종 판단은 전문가와 상담이 필요함을 안내
- 불확실한 내용은 추측하지 않음
- 법령 개정 사항이 있을 수 있으므로 최신 법령 확인 권고
""")
        
        # 대화 히스토리
        self.conversation_history = [self.system_message]
        self.query_count = 0
        
    def get_response(self, user_input: str) -> Tuple[str, List[str], List[str]]:
        """
        사용자 질문에 대한 법령 기반 응답 생성
        
        Args:
            user_input: 사용자 질문
            
        Returns:
            (응답 텍스트, 출처 리스트, 관련 조문 리스트)
        """
        try:
            self.query_count += 1
            start_time = time.time()
            
            # 관련 법령 검색
            relevant_docs = self.knowledge_base.search(user_input)
            
            if not relevant_docs:
                return "죄송합니다. 제공된 법령 자료에서 관련 내용을 찾을 수 없습니다.\n\n다른 표현으로 질문하시거나, 구체적인 법령명이나 조문을 명시해주시면 더 정확한 답변을 드릴 수 있습니다.", [], []
            
            # 컨텍스트 구성
            context_parts = []
            sources = set()
            articles = []
            
            for i, doc in enumerate(relevant_docs, 1):
                # 조문 정보 추출
                metadata = doc.metadata
                
                if metadata.get('type') == 'article':
                    article_info = f"【{metadata.get('article', '')}】"
                    if metadata.get('title'):
                        article_info += f" {metadata['title']}"
                    articles.append(article_info)
                    context_parts.append(f"[법령 조문 {i}] {article_info}\n{doc.page_content}")
                else:
                    context_parts.append(f"[법령 자료 {i}]\n{doc.page_content}")
                
                if 'source' in metadata:
                    source_name = os.path.basename(metadata['source'])
                    sources.add(source_name)
            
            context = "\n\n" + "="*70 + "\n\n".join(context_parts)
            
            # 법령 전문 프롬프트
            prompt = f"""다음 법령 자료를 바탕으로 공무원의 질문에 답변해주세요.

**법령 자료:**
{context}

**공무원 질문:** {user_input}

**답변 작성 가이드:**
1. 관련 법령 조문을 명확히 인용하세요 (예: "제○조에 따르면...")
2. 법령 내용을 정확히 설명하되, 이해하기 쉽게 풀어서 설명하세요
3. 실무 적용 시 주의사항이 있다면 함께 안내하세요
4. 법령에 없는 내용은 추측하지 마세요

**답변:**"""
            
            # 대화 히스토리 관리
            if len(self.conversation_history) > self.config.max_history * 2:
                self.conversation_history = [self.system_message] + \
                                           self.conversation_history[-(self.config.max_history * 2):]
            
            # LLM 호출
            messages = self.conversation_history + [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            # 히스토리 업데이트
            self.conversation_history.append(HumanMessage(content=user_input))
            self.conversation_history.append(AIMessage(content=response.content))
            
            elapsed_time = time.time() - start_time
            logger.info(f"법령 답변 생성 완료 (소요시간: {elapsed_time:.2f}초)")
            
            return response.content, list(sources), articles
            
        except Exception as e:
            logger.error(f"법령 답변 생성 실패: {e}")
            return f"오류가 발생했습니다: {str(e)}", [], []
    
    def reset_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history = [self.system_message]
        self.query_count = 0
        logger.info("대화 히스토리 초기화 완료")


class LawAgentConsole:
    """법령 에이전트 콘솔 인터페이스"""
    
    def __init__(self, agent: LawAgent):
        self.agent = agent
        
    def print_header(self):
        """헤더 출력"""
        print("\n" + "=" * 80)
        print("⚖️  공무원 법령 AI 어시스턴트".center(80))
        print("=" * 80)
        print(f"📚 법령 데이터: {self.agent.knowledge_base.document_count}개 조문/조각")
        print(f"🔧 AI 모델: {self.agent.config.model_name}")
        print(f"🎯 정확도 모드: 활성화 (temperature={self.agent.config.temperature})")
        print("=" * 80)
        print("\n📋 사용 가능한 명령어:")
        print("  • 법령 질문: 자유롭게 질문하세요 (예: '휴가 일수는 어떻게 되나요?')")
        print("  • 'quit' 또는 'exit': 프로그램 종료")
        print("  • 'reset' 또는 '초기화': 대화 내역 초기화")
        print("  • 'help' 또는 '도움말': 사용 안내")
        print("\n💡 팁: 구체적인 법령명이나 조문을 언급하면 더 정확한 답변을 받을 수 있습니다.")
        print("\n" + "=" * 80 + "\n")
    
    def print_message(self, sender: str, message: str, sources: List[str] = None, articles: List[str] = None):
        """메시지 출력"""
        if sender == "user":
            print(f"\n{'─' * 80}")
            print(f"👤 질문: {message}")
            print(f"{'─' * 80}")
        elif sender == "ai":
            print(f"\n⚖️  법령 답변:")
            print(f"{'─' * 80}")
            print(message)
            
            if articles:
                print(f"\n📌 참조 조문:")
                for article in articles:
                    print(f"   • {article}")
            
            if sources:
                print(f"\n📖 법령 출처: {', '.join(sources)}")
            
            print(f"{'─' * 80}")
            print("⚠️  주의: 이 답변은 참고용이며, 최종 판단은 법무팀과 상담하시기 바랍니다.")
            print(f"{'─' * 80}\n")
        else:
            print(f"\n💡 시스템: {message}\n")
    
    def print_help(self):
        """도움말 출력"""
        print("\n" + "=" * 80)
        print("📖 사용 가이드".center(80))
        print("=" * 80)
        print("\n1️⃣  질문 예시:")
        print("   • '공무원 휴가 일수는 어떻게 되나요?'")
        print("   • '징계 처분의 종류에 대해 알려주세요'")
        print("   • '복무 규정 중 제3조의 내용은 무엇인가요?'")
        print("   • '승진 요건을 설명해주세요'")
        print("\n2️⃣  효과적인 질문 방법:")
        print("   • 구체적으로: '휴가'보다는 '연차휴가 사용 절차'")
        print("   • 법령명 언급: '국가공무원법 제○조'")
        print("   • 상황 설명: '5년차 공무원의 승진 요건'")
        print("\n3️⃣  명령어:")
        print("   • reset: 새로운 주제로 질문할 때")
        print("   • quit: 프로그램 종료")
        print("=" * 80 + "\n")
    
    def run(self):
        """콘솔 인터페이스 실행"""
        self.print_header()
        
        while True:
            try:
                user_input = input("💬 법령 질문: ").strip()
                
                if not user_input:
                    continue
                
                # 명령어 처리
                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("\n👋 법령 에이전트를 종료합니다. 업무에 도움이 되셨기를 바랍니다!")
                    break
                
                if user_input.lower() in ['reset', '초기화']:
                    self.agent.reset_history()
                    self.print_message("system", "대화가 초기화되었습니다. 새로운 질문을 해주세요.")
                    continue
                
                if user_input.lower() in ['help', '도움말']:
                    self.print_help()
                    continue
                
                # 법령 답변 생성
                print("\n🔍 법령 검색 중...")
                response, sources, articles = self.agent.get_response(user_input)
                
                self.print_message("ai", response, sources, articles)
                
            except KeyboardInterrupt:
                print("\n\n👋 법령 에이전트를 종료합니다. 감사합니다!")
                break
            except Exception as e:
                logger.error(f"오류 발생: {e}")
                self.print_message("system", f"오류가 발생했습니다: {str(e)}")


def main():
    """메인 함수"""
    # API 키 확인
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY 환경 변수를 설정해주세요.")
        print("\n사용법:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        print("  python law_agent.py")
        sys.exit(1)
    
    # 설정 초기화
    config = LawAgentConfig(
        model_name="gemini-2.0-flash-exp",
        chunk_size=800,
        chunk_overlap=200,
        top_k_results=7,
        temperature=0.1  # 법령은 정확성이 중요
    )
    
    # 법령 지식 베이스 생성
    knowledge_base = LawKnowledgeBase(config)
    
    # 법령 파일 경로 (여러 파일 가능)
    file_paths = [
        "민법(법률)(제20432호)(20250131).pdf",  # 기본 법령 파일
        # "국가공무원법.txt",
        # "공무원복무규정.pdf",
        # "인사규정.docx",
    ]
    
    # 파일 존재 확인
    existing_files = [f for f in file_paths if os.path.exists(f)]
    if not existing_files:
        logger.error(f"법령 파일을 찾을 수 없습니다: {file_paths}")
        print("\n다음 중 하나를 수행해주세요:")
        print("1. 현재 디렉토리에 법령 파일을 준비하세요 (txt, pdf, docx)")
        print("2. 스크립트 내의 file_paths 변수를 수정하여 올바른 경로를 지정하세요")
        print("\n예시 파일명: 국가공무원법.txt, 공무원복무규정.pdf 등")
        sys.exit(1)
    
    success = knowledge_base.create_knowledge_base(existing_files)
    
    if not success:
        logger.error("법령 지식 베이스 생성에 실패했습니다.")
        sys.exit(1)
    
    # 법령 에이전트 초기화
    agent = LawAgent(api_key, knowledge_base, config)
    
    # 콘솔 인터페이스 실행
    console = LawAgentConsole(agent)
    console.run()


if __name__ == "__main__":
    main()