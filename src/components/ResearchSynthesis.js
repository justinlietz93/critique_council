import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  CircularProgress,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Psychology as AIIcon,
  Article as DocumentIcon,
  Compare as CompareIcon,
  Lightbulb as InsightIcon
} from '@mui/icons-material';

function ResearchSynthesis({ documents }) {
  const [synthesisPrompt, setSynthesisPrompt] = useState('');
  const [synthesisResult, setSynthesisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSynthesis = async () => {
    if (!synthesisPrompt.trim() || documents.length === 0) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would call your backend API
      // which would process the documents and generate a synthesis
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API call
      
      // Simulate a synthesis result
      setSynthesisResult({
        summary: `This synthesis examines the intersection of ${synthesisPrompt} across legal and scientific domains. The analysis reveals several key insights and connections between the documents.`,
        keyInsights: [
          'Legal precedents establish a framework that aligns with scientific findings',
          'Recent scientific research challenges some established legal interpretations',
          'Both domains emphasize the importance of methodological rigor',
          'Emerging trends suggest a convergence of approaches in the future'
        ],
        connections: [
          {
            documents: [documents[0].id, documents[documents.length > 1 ? 1 : 0].id],
            relationship: 'Complementary findings',
            description: 'These documents present complementary perspectives that strengthen each other\'s conclusions.'
          },
          {
            documents: [documents[0].id, documents[documents.length > 2 ? 2 : 0].id],
            relationship: 'Potential contradiction',
            description: 'These documents present potentially contradictory findings that warrant further investigation.'
          }
        ],
        recommendations: [
          'Conduct further research on the specific intersection points identified',
          'Consider the legal implications of the scientific findings',
          'Explore how recent court decisions might impact scientific research directions',
          'Develop a framework that integrates both legal and scientific perspectives'
        ]
      });
    } catch (err) {
      console.error('Synthesis error:', err);
      setError('An error occurred while generating the synthesis. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper sx={{ p: 3, mb: 2, borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          AI-Powered Research Synthesis
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Generate insights by analyzing connections between legal and scientific documents. 
          Describe what you want to understand about these documents.
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Selected Documents ({documents.length})
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {documents.map(doc => (
              <Chip 
                key={doc.id}
                label={doc.title.length > 30 ? doc.title.substring(0, 30) + '...' : doc.title}
                size="small"
                icon={doc.source === 'westlaw' ? <DocumentIcon /> : <AIIcon />}
                color={doc.source === 'westlaw' ? 'primary' : 'accent'}
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
        
        <TextField
          fullWidth
          multiline
          rows={3}
          placeholder="What insights are you looking for? (e.g., 'Analyze how recent court decisions on AI patents align with current machine learning research')"
          value={synthesisPrompt}
          onChange={(e) => setSynthesisPrompt(e.target.value)}
          variant="outlined"
          sx={{ mb: 2 }}
        />
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSynthesis}
            disabled={loading || !synthesisPrompt.trim() || documents.length === 0}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <AIIcon />}
          >
            Generate Synthesis
          </Button>
        </Box>
      </Paper>
      
      {error && (
        <Paper sx={{ p: 3, mb: 2, borderRadius: 2, bgcolor: 'error.light' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}
      
      {synthesisResult && (
        <Paper sx={{ p: 3, flex: 1, overflow: 'auto', borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            Synthesis Results
          </Typography>
          
          <Typography variant="body1" paragraph>
            {synthesisResult.summary}
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            <Box component="span" sx={{ display: 'flex', alignItems: 'center' }}>
              <InsightIcon sx={{ mr: 1 }} />
              Key Insights
            </Box>
          </Typography>
          
          <List dense>
            {synthesisResult.keyInsights.map((insight, index) => (
              <ListItem key={index}>
                <ListItemIcon sx={{ minWidth: 30 }}>•</ListItemIcon>
                <ListItemText primary={insight} />
              </ListItem>
            ))}
          </List>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            <Box component="span" sx={{ display: 'flex', alignItems: 'center' }}>
              <CompareIcon sx={{ mr: 1 }} />
              Document Connections
            </Box>
          </Typography>
          
          {synthesisResult.connections.map((connection, index) => (
            <Box key={index} sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="primary">
                {connection.relationship}
              </Typography>
              <Typography variant="body2" paragraph>
                {connection.description}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {connection.documents.map(docId => {
                  const doc = documents.find(d => d.id === docId) || { 
                    title: 'Unknown Document', 
                    source: 'unknown' 
                  };
                  return (
                    <Chip 
                      key={docId}
                      label={doc.title.length > 20 ? doc.title.substring(0, 20) + '...' : doc.title}
                      size="small"
                      color={doc.source === 'westlaw' ? 'primary' : 'accent'}
                      variant="outlined"
                    />
                  );
                })}
              </Box>
            </Box>
          ))}
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            Recommendations
          </Typography>
          
          <List dense>
            {synthesisResult.recommendations.map((recommendation, index) => (
              <ListItem key={index}>
                <ListItemIcon sx={{ minWidth: 30 }}>•</ListItemIcon>
                <ListItemText primary={recommendation} />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
}

export default ResearchSynthesis;