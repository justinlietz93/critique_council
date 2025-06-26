import React, { useState, useRef } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  IconButton, 
  Tooltip,
  Popover,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider
} from '@mui/material';
import {
  NoteAdd as NoteIcon,
  Delete as DeleteIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { v4 as uuidv4 } from 'uuid';
import { useResearch } from '../contexts/ResearchContext';

function AnnotationTool({ documentId, content }) {
  const { annotations, addAnnotation, removeAnnotation } = useResearch();
  const [selection, setSelection] = useState(null);
  const [annotationText, setAnnotationText] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const contentRef = useRef(null);
  
  const documentAnnotations = annotations[documentId] || [];

  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection.toString().length > 0) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      
      // Get the content container's position
      const containerRect = contentRef.current.getBoundingClientRect();
      
      // Calculate relative position
      const relativeRect = {
        top: rect.top - containerRect.top,
        left: rect.left - containerRect.left,
        width: rect.width,
        height: rect.height
      };
      
      setSelection({
        text: selection.toString(),
        position: relativeRect,
        range: {
          startOffset: range.startOffset,
          endOffset: range.endOffset,
          startContainer: range.startContainer.textContent,
          endContainer: range.endContainer.textContent
        }
      });
      
      // Position the popover
      setAnchorEl({
        clientWidth: 0,
        clientHeight: 0,
        getBoundingClientRect: () => ({
          top: rect.top,
          left: rect.left + (rect.width / 2),
          right: rect.right,
          bottom: rect.bottom,
          width: 0,
          height: 0
        })
      });
    }
  };

  const handleAddAnnotation = () => {
    if (selection && annotationText.trim()) {
      const newAnnotation = {
        id: uuidv4(),
        text: selection.text,
        note: annotationText,
        position: selection.range,
        timestamp: new Date().toISOString()
      };
      
      addAnnotation(documentId, newAnnotation);
      setAnnotationText('');
      setSelection(null);
      setAnchorEl(null);
    }
  };

  const handleRemoveAnnotation = (annotationId) => {
    removeAnnotation(documentId, annotationId);
  };

  const handlePopoverClose = () => {
    setAnchorEl(null);
    setSelection(null);
    setAnnotationText('');
  };

  // Function to highlight annotations in the content
  const highlightAnnotations = (content) => {
    if (!documentAnnotations.length) return content;
    
    // In a real implementation, this would be more sophisticated
    // For this example, we'll just wrap a simple implementation
    let highlightedContent = content;
    
    documentAnnotations.forEach(annotation => {
      const annotationId = annotation.id;
      const textToHighlight = annotation.text;
      
      // Simple replace - in a real app, this would need to be more precise
      // to handle multiple occurrences and HTML structure
      highlightedContent = highlightedContent.replace(
        textToHighlight,
        `<span class="annotation" data-annotation-id="${annotationId}">${textToHighlight}</span>`
      );
    });
    
    return highlightedContent;
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper 
        ref={contentRef}
        sx={{ 
          flex: 1, 
          p: 3, 
          mb: 2, 
          overflow: 'auto',
          borderRadius: 2
        }}
        onMouseUp={handleTextSelection}
        dangerouslySetInnerHTML={{ __html: highlightAnnotations(content) }}
      />
      
      <Paper sx={{ p: 2, borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          Annotations
          <Tooltip title="Select text in the document to add annotations">
            <IconButton size="small" sx={{ ml: 1 }}>
              <NoteIcon />
            </IconButton>
          </Tooltip>
        </Typography>
        
        {documentAnnotations.length > 0 ? (
          <List>
            {documentAnnotations.map((annotation, index) => (
              <React.Fragment key={annotation.id}>
                {index > 0 && <Divider />}
                <ListItem>
                  <ListItemText
                    primary={annotation.note}
                    secondary={
                      <>
                        <Typography component="span" variant="body2" color="text.primary">
                          "{annotation.text}"
                        </Typography>
                        <Typography component="span" variant="caption" display="block">
                          {new Date(annotation.timestamp).toLocaleString()}
                        </Typography>
                      </>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton edge="end" onClick={() => handleRemoveAnnotation(annotation.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No annotations yet. Select text in the document to add annotations.
          </Typography>
        )}
      </Paper>
      
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={handlePopoverClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
      >
        <Box sx={{ p: 2, width: 300 }}>
          <Typography variant="subtitle2" gutterBottom>
            Add Annotation
          </Typography>
          <Typography variant="body2" sx={{ mb: 2, fontStyle: 'italic' }}>
            "{selection?.text}"
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            placeholder="Add your notes here..."
            value={annotationText}
            onChange={(e) => setAnnotationText(e.target.value)}
            variant="outlined"
            size="small"
            sx={{ mb: 2 }}
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button onClick={handlePopoverClose} sx={{ mr: 1 }}>
              Cancel
            </Button>
            <Button 
              variant="contained" 
              color="primary"
              onClick={handleAddAnnotation}
              disabled={!annotationText.trim()}
            >
              Save
            </Button>
          </Box>
        </Box>
      </Popover>
    </Box>
  );
}

export default AnnotationTool;