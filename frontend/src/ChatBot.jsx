import "./styling/ChatBot.css";
import {useEffect, useState, useRef} from "react";
import React from "react";


function ChatBot() {

    /* declare the new input from the keyboard and hold it in a var
    *  declare the new messages and them set them to the holder so they can display
    * */
    const [newInputValue, setNewInputValue] = useState("");
    const [messages, setMessages] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(false);
    const [errorMessage, setErrorMessage] = React.useState("");

    const bottomRef = useRef(null);
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const newMessage = async (e) => {
        e.preventDefault();// prevent form from refreshing the page

        // Checks if the message is empty or only whitespace. If so, it stops and doesn’t send anything.
        if (!newInputValue.trim()) {
            return;
        }
        setIsLoading(true);
        setErrorMessage("");
        setNewInputValue("");

        const newMessages = [...messages, {
            text: newInputValue,
            sender: "user"
        }];
        setMessages(newMessages);

        try {
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: newInputValue.trim() }),
            });

            if (response.ok) {
                const data = await response.json();
                setMessages((prevMessages) => [
                    ...prevMessages,
                    { sender: "ai", text: data.response },
                ]);            } else {
                const errorData = await response.json();
                setErrorMessage(`Chatbot error: ${errorData.error || 'Something went wrong'}`);
            }
        } catch (error) {
            setErrorMessage(`Network error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    return <main >
        <h1 className="header">Share your thought</h1>
        <div className="chatbot-container">
            {messages.map((msg, index) => (
                <p key={index} className={`message ${msg.sender}`}>
                    {msg.text}
                </p>
            ))}

            {/* 👇 This makes it auto-scroll to the newest message */}
            <div ref={bottomRef} />

            {isLoading && <div className="loading">Thinking...</div>}
            {errorMessage && <div className="error">{errorMessage}</div>}

            <form className="input-form" onSubmit={newMessage}>
                <input type="text" // take in the input and hold it in the newInputValue var
                       placeholder="Tell me anything"
                       value={newInputValue}
                       onChange={(e) => setNewInputValue(e.currentTarget.value)}
                       disabled={isLoading}
                />
                <input type="submit" value="Send"/>
            </form>
        </div>


    </main>
}

export default ChatBot