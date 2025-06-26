import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  CardActions, 
  Button, 
  Chip, 
  Box,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon,
  Share as ShareIcon,
  OpenInNew as OpenIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useResearch } from '../contexts/ResearchContext';

function DocumentCard({ document, saved = false }) {
  const navigate = useNavigate();
  const { saveDocument, removeDocument, viewDocument } = useResearch();
  
  const handleViewDocument = () => {
    viewDocument(document);
    navigate(`/document/${document.id}`);
  };
  
  const handleToggleSave = () => {
    if (saved) {
      removeDocument(document.id);
    } else {
      saveDocument(document);
    }
  };
  
  const handleShare = () => {
    // In a real app, this would open a share dialog
    alert(`Sharing document: ${document.title}`);
  };

  return (
    <Card sx={{ mb: 2, borderRadius: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Chip 
            label={document.source === 'westlaw' ? 'Legal' : 'Scientific'} 
            size="small" 
            color={document.source === 'westlaw' ? 'primary' : 'accent'}
            sx={{ mr: 1 }}
          />
          <Typography variant="caption" color="text.secondary">
            {document.date}
          </Typography>
        </Box>
        
        <Typography variant="h6" component="div" gutterBottom>
          {document.title}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {document.source === 'westlaw' 
            ? `${document.court} • ${document.jurisdiction}`
            : `Authors: ${document.authors?.join(', ')}`
          }
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 1 }}>
          {document.source === 'westlaw' ? document.summary : document.abstract}
        </Typography>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {document.source === 'westlaw' && document.jurisdiction && (
            <Chip label={document.jurisdiction} size="small" variant="outlined" />
          )}
          {document.source === 'arxiv' && document.categories?.map((category) => (
            <Chip key={category} label={category} size="small" variant="outlined" />
          ))}
          {document.citations && (
            <Chip label={`${document.citations} citations`} size="small" variant="outlined" />
          )}
        </Box>
      </CardContent>
      
      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Box>
          <Tooltip title={saved ? "Remove from saved" : "Save document"}>
            <IconButton onClick={handleToggleSave} color={saved ? "primary" : "default"}>
              {saved ? <BookmarkIcon /> : <BookmarkBorderIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Share document">
            <IconButton onClick={handleShare}>
              <ShareIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Button 
          variant="contained" 
          color="primary" 
          endIcon={<OpenIcon />}
          onClick={handleViewDocument}
        >
          View
        </Button>
      </CardActions>
    </Card>
  );
}

export default DocumentCard;