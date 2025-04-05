// // "use client"
// //
// // import { useState, useEffect } from "react"
// // import "./styling/AgentSlider.css"
// //
// // const AgentSlider = () => {
// //     const [slideIndex, setSlideIndex] = useState(0)
// //
// //     // Sample agent data
// //     const agents = [
// //         { id: 1, name: "Agent Smith", specialty: "General Assistance" },
// //         { id: 2, name: "Agent Johnson", specialty: "Technical Support"},
// //         { id: 3, name: "Agent Brown", specialty: "Sales Inquiries"},
// //         { id: 4, name: "Agent Davis", specialty: "Customer Service"},
// //         { id: 5, name: "Agent Wilson", specialty: "Product Information"},
// //         { id: 6, name: "Agent Moore", specialty: "Billing Support"},
// //     ]
// //
// //     useEffect(() => {
// //         // Initialize the slider
// //         const intervalId = setInterval(() => {
// //             nextSlide()
// //         }, 5000)
// //
// //         // Clean up the interval on component unmount
// //         return () => clearInterval(intervalId)
// //     }, [slideIndex]) // Re-run effect when slideIndex changes
// //
// //     const showSlide = (index) => {
// //         let newIndex = index
// //
// //         if (index >= agents.length) {
// //             newIndex = 0
// //         } else if (index < 0) {
// //             newIndex = agents.length - 1
// //         }
// //
// //         setSlideIndex(newIndex)
// //     }
// //
// //     const prevSlide = () => {
// //         showSlide(slideIndex - 1)
// //     }
// //
// //     const nextSlide = () => {
// //         showSlide(slideIndex + 1)
// //     }
// //
// //     return (
// //         <div className="slider">
// //             <div className="slides">
// //                 {agents.map((agent, index) => (
// //                     <div key={agent.id} className={`slide agent-card ${index === slideIndex ? "displaySlide" : ""}`}>
// //                         <h2>{agent.name}</h2>
// //                         <p>{agent.specialty}</p>
// //                         {/*<button className="connect-button">Connect</button>*/}
// //                     </div>
// //                 ))}
// //             </div>
// //
// //             <button className="prev" onClick={prevSlide}>
// //                 &#10094;
// //             </button>
// //             <button className="next" onClick={nextSlide}>
// //                 &#10095;
// //             </button>
// //         </div>
// //     )
// // }
// //
// // export default AgentSlider
// //
//
// "use client"
//
// import { useState, useEffect } from "react";
// import "./styling/AgentSlider.css";
//
// const AgentSlider = () => {
//     const [slideIndex, setSlideIndex] = useState(0);
//
//     // Sample agent data
//     const agents = [
//         { id: 1, name: "Agent Smith", specialty: "General Assistance" },
//         { id: 2, name: "Agent Johnson", specialty: "Technical Support" },
//         { id: 3, name: "Agent Brown", specialty: "Sales Inquiries" },
//         { id: 4, name: "Agent Davis", specialty: "Customer Service" },
//         { id: 5, name: "Agent Wilson", specialty: "Product Information" },
//         { id: 6, name: "Agent Moore", specialty: "Billing Support" },
//     ];
//
//     useEffect(() => {
//         const intervalId = setInterval(() => {
//             nextSlide();
//         }, 5000);
//
//         return () => clearInterval(intervalId);
//     }, [slideIndex]);
//
//     const showSlide = (index) => {
//         let newIndex = index;
//
//         if (index >= agents.length) {
//             newIndex = 0;
//         } else if (index < 0) {
//             newIndex = agents.length - 1;
//         }
//
//         setSlideIndex(newIndex);
//     };
//
//     const prevSlide = () => {
//         showSlide(slideIndex - 1);
//     };
//
//     const nextSlide = () => {
//         showSlide(slideIndex + 1);
//     };
//
//     return (
//         <div className="slider">
//             <div
//                 className="slides"
//                 style={{ transform: `translateX(-${slideIndex * 100}%)` }}
//             >
//                 {agents.map((agent) => (
//                     <div key={agent.id} className="slide agent-card">
//                         <h2>{agent.name}</h2>
//                         <p>{agent.specialty}</p>
//                         {/*<button className="connect-button">Connect</button>*/}
//                     </div>
//                 ))}
//             </div>
//             <button className="prev" onClick={prevSlide}>
//                 &#10094;
//             </button>
//             <button className="next" onClick={nextSlide}>
//                 &#10095;
//             </button>
//         </div>
//     );
// };
//
// export default AgentSlider;


//////////////////////////////////////////////////////////////
"use client";

import React, { useState, useEffect } from "react";
import "./styling/AgentSlider.css";

const AgentSlider = () => {
    const [slideIndex, setSlideIndex] = useState(0);
    const [transitionEnabled, setTransitionEnabled] = useState(true);

    // Sample agent data
    const agents = [
        { id: 1, name: "Agent Smith", specialty: "General Assistance" },
        { id: 2, name: "Agent Johnson", specialty: "Technical Support" },
        { id: 3, name: "Agent Brown", specialty: "Sales Inquiries" },
        { id: 4, name: "Agent Davis", specialty: "Customer Service" },
        { id: 5, name: "Agent Wilson", specialty: "Product Information" },
        { id: 6, name: "Agent Moore", specialty: "Billing Support" },
    ];

    // Extend agents with the first slide at the end for seamless looping
    const extendedAgents = [...agents, agents[0]];

    // Auto-slide every 5 seconds
    useEffect(() => {
        const intervalId = setInterval(() => {
            setSlideIndex((prevIndex) => prevIndex + 1);
        }, 5000);

        return () => clearInterval(intervalId);
    }, []);

    // When reaching the cloned slide, reset back to first slide without transition
    useEffect(() => {
        if (slideIndex === agents.length) {
            // Wait for the transition to complete (0.5s)
            const timeoutId = setTimeout(() => {
                setTransitionEnabled(false); // Disable transition to reset position
                setSlideIndex(0);
                // Re-enable transition after a brief pause
                setTimeout(() => {
                    setTransitionEnabled(true);
                }, 50);
            }, 500); // Should match your CSS transition duration
            return () => clearTimeout(timeoutId);
        }
    }, [slideIndex, agents.length]);

    return (
        <div className="slider">
            <div
                className="slides"
                style={{
                    transform: `translateX(-${slideIndex * 100}%)`,
                    transition: transitionEnabled ? "transform 0.5s ease-in-out" : "none",
                }}
            >
                {extendedAgents.map((agent, index) => (
                    <div key={index} className="slide agent-card">
                        <h2>{agent.name}</h2>
                        <p>{agent.specialty}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AgentSlider;
