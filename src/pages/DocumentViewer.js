import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Box, 
  Grid, 
  Paper, 
  Typography, 
  Tabs, 
  Tab, 
  CircularProgress,
  Button,
  Chip,
  Divider
} from '@mui/material';
import {
  Description as DocumentIcon,
  AccountTree as NetworkIcon,
  Psychology as SynthesisIcon
} from '@mui/icons-material';
import { useResearch } from '../contexts/ResearchContext';
import { getDocument, getCitationNetwork } from '../services/api';
import SplitView from '../components/SplitView';
import AnnotationTool from '../components/AnnotationTool';
import CitationNetwork from '../components/CitationNetwork';
import ResearchSynthesis from '../components/ResearchSynthesis';

function DocumentViewer() {
  const { id } = useParams();
  const { viewDocument, savedDocuments, saveDocument, removeDocument } = useResearch();
  const [document, setDocument] = useState(null);
  const [relatedDocument, setRelatedDocument] = useState(null);
  const [citationData, setCitationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [splitView, setSplitView] = useState(false);
  
  const isSaved = savedDocuments.some(doc => doc.id === id);

  useEffect(() => {
    const fetchDocument = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Parse the document ID to get the source
        const [source] = id.split('.');
        
        // Fetch the document
        const doc = await getDocument(id, source);
        setDocument(doc);
        
        // Register the document view
        viewDocument(doc);
        
        // Fetch citation network data
        const networkData = await getCitationNetwork(id, source);
        setCitationData(networkData);
      } catch (err) {
        console.error('Error fetching document:', err);
        setError('Failed to load document. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDocument();
  }, [id, viewDocument]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleToggleSave = () => {
    if (isSaved) {
      removeDocument(id);
    } else if (document) {
      saveDocument(document);
    }
  };

  const handleToggleSplitView = () => {
    setSplitView(!splitView);
    
    if (!splitView && !relatedDocument) {
      // When enabling split view, load a related document if none is loaded
      // In a real app, this would fetch a relevant document
      // For this example, we'll simulate loading a related document
      setRelatedDocument({
        id: 'related-doc',
        title: 'Related Document',
        source: document?.source === 'westlaw' ? 'arxiv' : 'westlaw',
        content: `
          <h1>Related Document</h1>
          <p>This is a simulated related document that would complement the main document.</p>
          <p>In a real implementation, this would be a document that is cited by or cites the main document,
          or is otherwise related based on content similarity.</p>
          <h2>Key Points</h2>
          <p>The key points of this document would relate to the main document in meaningful ways,
          providing additional context or contrasting perspectives.</p>
        `
      });
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 3, borderRadius: 2, bgcolor: 'error.light' }}>
        <Typography color="error">{error}</Typography>
      </Paper>
    );
  }

  if (!document) {
    return (
      <Paper sx={{ p: 3, borderRadius: 2 }}>
        <Typography>Document not found.</Typography>
      </Paper>
    );
  }

  const renderMainContent = () => {
    switch (tabValue) {
      case 0: // Document
        return <AnnotationTool documentId={document.id} content={document.content} />;
      case 1: // Citation Network
        return <CitationNetwork data={citationData} loading={!citationData} />;
      case 2: // Research Synthesis
        return <ResearchSynthesis documents={[document, ...(relatedDocument ? [relatedDocument] : [])]} />;
      default:
        return null;
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              {document.title}
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              <Chip 
                label={document.source === 'westlaw' ? 'Legal Document' : 'Scientific Paper'} 
                color={document.source === 'westlaw' ? 'primary' : 'accent'}
              />
              <Chip label={`Date: ${document.date}`} variant="outlined" />
              {document.source === 'westlaw' && (
                <Chip label={document.court} variant="outlined" />
              )}
              {document.source === 'arxiv' && document.categories?.map(category => (
                <Chip key={category} label={category} variant="outlined" />
              ))}
            </Box>
            
            <Typography variant="subtitle1" gutterBottom>
              {document.source === 'westlaw' 
                ? `Court: ${document.court}`
                : `Authors: ${document.authors?.join(', ')}`
              }
            </Typography>
          </Box>
          
          <Box>
            <Button
              variant={isSaved ? "outlined" : "contained"}
              color="primary"
              onClick={handleToggleSave}
              sx={{ mr: 1 }}
            >
              {isSaved ? "Unsave" : "Save"}
            </Button>
            
            <Button
              variant={splitView ? "contained" : "outlined"}
              color="secondary"
              onClick={handleToggleSplitView}
            >
              {splitView ? "Single View" : "Split View"}
            </Button>
          </Box>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        <Paper sx={{ borderRadius: 2 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab icon={<DocumentIcon />} label="Document" />
            <Tab icon={<NetworkIcon />} label="Citation Network" />
            <Tab icon={<SynthesisIcon />} label="Research Synthesis" />
          </Tabs>
        </Paper>
      </Box>
      
      {splitView ? (
        <SplitView
          leftPanel={renderMainContent()}
          rightPanel={
            relatedDocument ? (
              <Box sx={{ height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  {relatedDocument.title}
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  {relatedDocument.source === 'westlaw' ? 'Legal Document' : 'Scientific Paper'}
                </Typography>
                <Paper 
                  sx={{ 
                    p: 3, 
                    height: 'calc(100% - 80px)', 
                    overflow: 'auto',
                    borderRadius: 2
                  }}
                  dangerouslySetInnerHTML={{ __html: relatedDocument.content }}
                />
              </Box>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <Typography>No related document selected.</Typography>
              </Box>
            )
          }
        />
      ) : (
        renderMainContent()
      )}
    </Box>
  );
}

export default DocumentViewer;