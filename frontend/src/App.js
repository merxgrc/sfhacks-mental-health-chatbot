import React, { useState } from 'react';
import './App.css'; // Import the CSS file

function ChatbotFrontend() {
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    setIsLoading(true);
    setErrorMessage('');
    setChatLog([...chatLog, { user: 'You', text: message }]);
    setMessage('');

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message.trim() }),
      });

      if (response.ok) {
        const data = await response.json();
        setChatLog([...chatLog, { user: 'Bot', text: data.response }]);
      } else {
        const errorData = await response.json();
        setErrorMessage(`Chatbot error: ${errorData.error || 'Something went wrong'}`);
      }
    } catch (error) {
      setErrorMessage(`Network error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (event) => {
    setMessage(event.target.value);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !isLoading) {
      handleSendMessage();
    }
  };

  return (
    <div className="chatbot-container">
      <h1 className="chatbot-heading">Mental Health Chatbot</h1>
      <div className="chat-log">
        {chatLog.map((msg, index) => (
          <div
            key={index}
            className={msg.user === 'You' ? 'user-message' : 'bot-message'}
          >
            <strong>{msg.user}:</strong> {msg.text}
          </div>
        ))}
        {isLoading && <div className="loading">Thinking...</div>}
        {errorMessage && <div className="error">{errorMessage}</div>}
      </div>
      <div className="input-container">
        <input
          type="text"
          value={message}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          className="input"
          disabled={isLoading}
        />
        <button onClick={handleSendMessage} className="button" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}

export default ChatbotFrontend;