import { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { role: 'ai', content: '안녕하세요! 공무원 법령에 대해 무엇이든 물어보세요.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // API 기본 URL
  const API_BASE_URL = 'http://localhost:8000';

  // 새 메시지가 추가되면 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // textarea 자동 높이 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  // 실제 API 호출 함수
  const callAPI = async (question) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`API 오류: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || '알 수 없는 오류가 발생했습니다.');
      }

      return data;
    } catch (error) {
      console.error('API 호출 오류:', error);
      throw error;
    }
  };

  // 메시지 전송
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setError(null);

    // 사용자 메시지 추가
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // 실제 API 호출
      const data = await callAPI(userMessage);
      
      // AI 응답 추가
      const aiMessage = {
        role: 'ai',
        content: data.answer,
        sources: data.sources || [],
        articles: data.articles || []
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      // 오류 메시지 추가
      setError('답변을 가져오는 중 오류가 발생했습니다. 다시 시도해주세요.');
      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          content: `죄송합니다. 오류가 발생했습니다: ${error.message}\n\n백엔드 서버가 실행 중인지 확인해주세요.`,
          isError: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Enter 키로 전송
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 예시 질문
  const exampleQuestions = [
    "권리능력은 언제 시작되나요?",
    "민법 제750조 내용은?",
    "부동산 매매계약에 대해 알려주세요"
  ];

  const handleExampleClick = async (question) => {
    if (isLoading) return;

    setInput('');
    setError(null);

    // 사용자 메시지 추가
    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setIsLoading(true);

    try {
      // 실제 API 호출
      const data = await callAPI(question);
      
      // AI 응답 추가
      const aiMessage = {
        role: 'ai',
        content: data.answer,
        sources: data.sources || [],
        articles: data.articles || []
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      setError('답변을 가져오는 중 오류가 발생했습니다. 다시 시도해주세요.');
      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          content: `죄송합니다. 오류가 발생했습니다: ${error.message}\n\n백엔드 서버가 실행 중인지 확인해주세요.`,
          isError: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // 대화 초기화
  const handleReset = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/reset`, { method: 'POST' });
      setMessages([
        { role: 'ai', content: '안녕하세요! 공무원 법령에 대해 무엇이든 물어보세요.' }
      ]);
      setError(null);
    } catch (error) {
      console.error('초기화 오류:', error);
    }
  };

  return (
    <div className="app">
      {/* 헤더 */}
      <header className="header">
        <div className="header-content">
          <div className="header-icon">⚖️</div>
          <div className="header-text">
            <h1>공무원 법령 에이전트</h1>
            <p className="header-subtitle">법령 정보를 쉽고 빠르게</p>
          </div>
          <button onClick={handleReset} className="reset-button" title="대화 초기화">
            🔄
          </button>
        </div>
      </header>

      {/* 오류 표시 */}
      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      {/* 채팅 영역 */}
      <div className="chat-container">
        <div className="messages">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`message ${message.role === 'user' ? 'user-message' : 'ai-message'} ${message.isError ? 'error-message' : ''}`}
            >
              <div className="message-avatar">
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                <div className="message-role">
                  {message.role === 'user' ? '사용자' : 'AI 에이전트'}
                </div>
                <div className="message-bubble">
                  <div className="message-text">{message.content}</div>
                  
                  {/* 참조 조문 표시 */}
                  {message.articles && message.articles.length > 0 && (
                    <div className="message-articles">
                      <div className="articles-title">📌 참조 조문:</div>
                      <ul className="articles-list">
                        {message.articles.map((article, idx) => (
                          <li key={idx}>{article}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {/* 법령 출처 표시 */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="message-sources">
                      📖 출처: {message.sources.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {/* 로딩 표시 */}
          {isLoading && (
            <div className="message ai-message">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="message-role">AI 에이전트</div>
                <div className="message-bubble">
                  <div className="message-text loading">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 예시 질문 (첫 메시지일 때만) */}
          {messages.length === 1 && !isLoading && (
            <div className="example-questions">
              <p className="example-title">💡 이런 질문을 해보세요</p>
              <div className="example-buttons">
                {exampleQuestions.map((question, index) => (
                  <button
                    key={index}
                    className="example-button"
                    onClick={() => handleExampleClick(question)}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 입력 영역 */}
      <div className="input-area">
        <div className="input-container">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="법령에 대해 질문해주세요..."
            rows="1"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="send-button"
          >
            <span className="send-icon">➤</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;