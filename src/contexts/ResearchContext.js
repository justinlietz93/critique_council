import React, { createContext, useContext, useState, useEffect } from 'react';
import { searchWestlaw, searchArxiv } from '../services/api';

const ResearchContext = createContext();

export function useResearch() {
  return useContext(ResearchContext);
}

export function ResearchProvider({ children }) {
  const [searchResults, setSearchResults] = useState({
    westlaw: [],
    arxiv: [],
    combined: []
  });
  const [recentDocuments, setRecentDocuments] = useState([]);
  const [savedDocuments, setSavedDocuments] = useState([]);
  const [annotations, setAnnotations] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load saved data from localStorage on initial render
  useEffect(() => {
    const loadSavedData = () => {
      const savedDocs = localStorage.getItem('savedDocuments');
      const recentDocs = localStorage.getItem('recentDocuments');
      const savedAnnotations = localStorage.getItem('annotations');

      if (savedDocs) setSavedDocuments(JSON.parse(savedDocs));
      if (recentDocs) setRecentDocuments(JSON.parse(recentDocs));
      if (savedAnnotations) setAnnotations(JSON.parse(savedAnnotations));
    };

    loadSavedData();
  }, []);

  // Save data to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('savedDocuments', JSON.stringify(savedDocuments));
  }, [savedDocuments]);

  useEffect(() => {
    localStorage.setItem('recentDocuments', JSON.stringify(recentDocuments));
  }, [recentDocuments]);

  useEffect(() => {
    localStorage.setItem('annotations', JSON.stringify(annotations));
  }, [annotations]);

  const search = async (query, filters = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      // Perform searches in parallel
      const [westlawResults, arxivResults] = await Promise.all([
        searchWestlaw(query, filters),
        searchArxiv(query, filters)
      ]);
      
      // Combine and sort results by relevance
      const combined = [...westlawResults, ...arxivResults].sort((a, b) => b.relevance - a.relevance);
      
      setSearchResults({
        westlaw: westlawResults,
        arxiv: arxivResults,
        combined
      });
    } catch (err) {
      console.error('Search error:', err);
      setError('An error occurred while searching. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const viewDocument = (document) => {
    // Add to recent documents if not already there
    setRecentDocuments(prev => {
      const exists = prev.some(doc => doc.id === document.id);
      if (!exists) {
        const updated = [document, ...prev].slice(0, 10); // Keep only 10 most recent
        return updated;
      }
      return prev;
    });
  };

  const saveDocument = (document) => {
    setSavedDocuments(prev => {
      const exists = prev.some(doc => doc.id === document.id);
      if (!exists) {
        return [...prev, document];
      }
      return prev;
    });
  };

  const removeDocument = (documentId) => {
    setSavedDocuments(prev => prev.filter(doc => doc.id !== documentId));
  };

  const addAnnotation = (documentId, annotation) => {
    setAnnotations(prev => ({
      ...prev,
      [documentId]: [...(prev[documentId] || []), annotation]
    }));
  };

  const removeAnnotation = (documentId, annotationId) => {
    setAnnotations(prev => ({
      ...prev,
      [documentId]: prev[documentId].filter(a => a.id !== annotationId)
    }));
  };

  const value = {
    searchResults,
    recentDocuments,
    savedDocuments,
    annotations,
    loading,
    error,
    search,
    viewDocument,
    saveDocument,
    removeDocument,
    addAnnotation,
    removeAnnotation
  };

  return (
    <ResearchContext.Provider value={value}>
      {children}
    </ResearchContext.Provider>
  );
}