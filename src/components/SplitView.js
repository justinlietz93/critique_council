import React, { useState, useRef, useEffect } from 'react';
import { Box } from '@mui/material';

function SplitView({ leftPanel, rightPanel }) {
  const [splitPosition, setSplitPosition] = useState(50); // Percentage
  const containerRef = useRef(null);
  const resizerRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const handleMouseDown = (e) => {
      setIsDragging(true);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    const handleMouseMove = (e) => {
      if (!isDragging || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const newPosition = ((e.clientX - containerRect.left) / containerRect.width) * 100;
      
      // Limit the position to a reasonable range
      if (newPosition > 20 && newPosition < 80) {
        setSplitPosition(newPosition);
      }
    };

    const resizer = resizerRef.current;
    if (resizer) {
      resizer.addEventListener('mousedown', handleMouseDown);
    }
    
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mousemove', handleMouseMove);

    return () => {
      if (resizer) {
        resizer.removeEventListener('mousedown', handleMouseDown);
      }
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousemove', handleMouseMove);
    };
  }, [isDragging]);

  return (
    <Box 
      ref={containerRef}
      sx={{ 
        display: 'flex', 
        width: '100%', 
        height: '100%',
        overflow: 'hidden'
      }}
    >
      <Box 
        sx={{ 
          width: `${splitPosition}%`, 
          height: '100%', 
          overflow: 'auto',
          pr: 1
        }}
      >
        {leftPanel}
      </Box>
      
      <Box 
        ref={resizerRef}
        sx={{ 
          width: '8px', 
          height: '100%', 
          backgroundColor: 'rgba(0, 0, 0, 0.1)', 
          cursor: 'col-resize',
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.2)'
          }
        }}
      />
      
      <Box 
        sx={{ 
          width: `${100 - splitPosition}%`, 
          height: '100%', 
          overflow: 'auto',
          pl: 1
        }}
      >
        {rightPanel}
      </Box>
    </Box>
  );
}

export default SplitView;