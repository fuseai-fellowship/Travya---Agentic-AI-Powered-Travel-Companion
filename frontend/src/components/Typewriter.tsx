import { useState, useEffect } from 'react';

interface TypewriterProps {
  text: string;
  speed?: number;
  delay?: number;
  className?: string;
  onComplete?: () => void;
  loop?: boolean;
  loopDelay?: number;
}

export default function Typewriter({ 
  text, 
  speed = 30, 
  delay = 0,
  className = '',
  onComplete,
  loop = false,
  loopDelay = 2000
}: TypewriterProps) {
  const [displayText, setDisplayText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    const animate = () => {
      setDisplayText('');
      setIsComplete(false);
      
      if (!text) return;

      const timer = setTimeout(() => {
        let currentIndex = 0;
        
        const typeInterval = setInterval(() => {
          if (currentIndex < text.length) {
            setDisplayText(text.substring(0, currentIndex + 1));
            currentIndex++;
          } else {
            clearInterval(typeInterval);
            setIsComplete(true);
            onComplete?.();
            
            // Loop logic
            if (loop) {
              setTimeout(() => {
                animate();
              }, loopDelay);
            }
          }
        }, speed);

        return () => clearInterval(typeInterval);
      }, delay);

      return () => clearTimeout(timer);
    };

    animate();
  }, [text, speed, delay, onComplete, loop, loopDelay]);

  return (
    <span className={`typewriter ${className}`}>
      <span className="typewriter-content" style={{ width: text.length + 'ch', visibility: 'hidden', display: 'block', height: 0 }}>
        {text}
      </span>
      <span className="typewriter-animated">
        {displayText.split('').map((char, index) => (
          <span 
            key={index} 
            className={char === ' ' ? 'space' : 'char'}
            style={{
              display: 'inline-block',
              animation: `expandChar 0.2s ease-out ${index * 0.03}s both`
            }}
          >
            {char === ' ' ? '\u00A0' : char}
          </span>
        ))}
        {!isComplete && <span className="cursor">|</span>}
      </span>
    </span>
  );
}

