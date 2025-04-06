import './styling/App.css'
import AnimatedText from "./AnimatedText.jsx";
import Agent from "./Agent.jsx";
import ChatBot from "./ChatBot.jsx";

function Title() {
    return (
        <h1>Welcome to Mental Health Chatbot</h1>
    )
}

function App() {
    const titleText = Title().props.children;

    const agents = [
        { id: 1, name: "Agent Smith", specialty: "General Assistance", avatar: "/placeholder.svg?height=80&width=80" },
        { id: 2, name: "Agent Johnson", specialty: "Technical Support", avatar: "/placeholder.svg?height=80&width=80" },
        { id: 3, name: "Agent Brown", specialty: "Sales Inquiries", avatar: "/placeholder.svg?height=80&width=80" },
        { id: 4, name: "Agent Davis", specialty: "Customer Service", avatar: "/placeholder.svg?height=80&width=80" },
        { id: 5, name: "Agent Wilson", specialty: "Product Information", avatar: "/placeholder.svg?height=80&width=80" },
        { id: 6, name: "Agent Moore", specialty: "Billing Support", avatar: "/placeholder.svg?height=80&width=80" },
    ]

    const duplicatedAgents = [...agents, ...agents, ...agents]

    return (
        <>
            <div>
                <h1 className='title'>
                    <AnimatedText text={titleText}/>
                </h1>
            </div>

            <div className="agent-display">
                <h1>Available Agents</h1>

                <Agent />
            </div>

            <ChatBot />


        </>

    );
}

export default App;