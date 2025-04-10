import './styling/App.css'
import AnimatedText from "./AnimatedText.jsx";
import Agent from "./Agent.jsx";
import ChatBot from "./ChatBot.jsx";
import React from "react";
import { useEffect } from "react";

function Title() {
    return (
        <h1>Welcome to MindChat</h1>
    )
}
function App() {
    const titleText = Title().props.children;

    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    return (
        <div className="app-container">
            <div className='title'>
                <AnimatedText text={titleText}/>
            </div>

            {/*<div className="agent-display">*/}
            {/*    <h1>Available Agents</h1>*/}
            {/*    <Agent/>*/}
            {/*</div>*/}

            <ChatBot/>

        </div>

    );

}

export default App;