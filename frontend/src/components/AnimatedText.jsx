import React from 'react';
import '../styling/AnimatedText.css';

const AnimatedText = ({ text }) => {
    return (
        <div className="animated-text">
            {text.split('').map((letter, index) => (
                <span
                    key={index}
                    className="letter"
                    style={{ animationDelay: `${index * 0.1}s` }} // Adjust timing as needed
                >
          {letter}
        </span>
            ))}
        </div>
    );
};

export default AnimatedText;
