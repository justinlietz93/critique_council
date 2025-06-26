import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Grid, 
  Paper, 
  Typography, 
  Tabs, 
  Tab, 
  Divider, 
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip
} from '@mui/material';
import { useLocation } from 'react-router-dom';
import { useResearch } from '../contexts/ResearchContext';
import DocumentCard from '../components/DocumentCard';

function Search() {
  const location = useLocation();
  const { searchResults, savedDocuments, loading, error, search } = useResearch();
  const [tabValue, setTabValue] = useState(0);
  const [sortOption, setSortOption] = useState('relevance');
  
  // Extract query and filters from location state if available
  useEffect(() => {
    if (location.state?.query) {
      search(location.state.query, location.state.filters || {});
    }
  }, [location.state, search]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleSortChange = (event) => {
    setSortOption(event.target.value);
  };

  // Get the appropriate results based on the selected tab
  const getResults = () => {
    switch (tabValue) {
      case 0: // All
        return searchResults.combined;
      case 1: // Legal
        return searchResults.westlaw;
      case 2: // Scientific
        return searchResults.arxiv;
      default:
        return [];
    }
  };

  // Sort the results based on the selected option
  const getSortedResults = () => {
    const results = getResults() || [];
    
    switch (sortOption) {
      case 'relevance':
        return [...results].sort((a, b) => b.relevance - a.relevance);
      case 'date-newest':
        return [...results].sort((a, b) => new Date(b.date) - new Date(a.date));
      case 'date-oldest':
        return [...results].sort((a, b) => new Date(a.date) - new Date(b.date));
      case 'citations':
        return [...results].sort((a, b) => (b.citations || 0) - (a.citations || 0));
      default:
        return results;
    }
  };

  const results = getSortedResults();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Search Results
      </Typography>
      
      {location.state?.query && (
        <Typography variant="subtitle1" gutterBottom>
          Results for: <Chip label={location.state.query} />
        </Typography>
      )}
      
      <Paper sx={{ mb: 3, borderRadius: 2 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label={`All (${searchResults.combined?.length || 0})`} />
          <Tab label={`Legal (${searchResults.westlaw?.length || 0})`} />
          <Tab label={`Scientific (${searchResults.arxiv?.length || 0})`} />
        </Tabs>
      </Paper>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="subtitle1">
          {results?.length || 0} results
        </Typography>
        
        <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
          <InputLabel id="sort-select-label">Sort By</InputLabel>
          <Select
            labelId="sort-select-label"
            id="sort-select"
            value={sortOption}
            onChange={handleSortChange}
            label="Sort By"
          >
            <MenuItem value="relevance">Relevance</MenuItem>
            <MenuItem value="date-newest">Date (Newest First)</MenuItem>
            <MenuItem value="date-oldest">Date (Oldest First)</MenuItem>
            <MenuItem value="citations">Citations (Most First)</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 3, borderRadius: 2, bgcolor: 'error.light' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      ) : results?.length > 0 ? (
        <Grid container spacing={3}>
          {results.map(document => (
            <Grid item xs={12} key={document.id}>
              <DocumentCard 
                document={document} 
                saved={savedDocuments.some(d => d.id === document.id)} 
              />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Paper sx={{ p: 5, textAlign: 'center', borderRadius: 2 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No results found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search terms or filters.
          </Typography>
        </Paper>
      )}
    </Box>
  );
}

export default Search;