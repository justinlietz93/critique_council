"""
Unit tests for ArXiv integration in ContentAssessor.

This module contains tests for the ContentAssessor's ability to
attach ArXiv references to extracted points.
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock
import logging

from src.content_assessor import ContentAssessor
from src.arxiv_reference_service import ArxivReferenceService

# Setup logging
logger = logging.getLogger("test_logger")
logger.setLevel(logging.DEBUG)

class TestArxivIntegration(unittest.TestCase):
    """Tests for ArXiv reference integration in ContentAssessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.assessor = ContentAssessor()
        self.assessor.set_logger(logger)
        
        # Test content and points
        self.test_content = "This is a test document about quantum computing and neural networks."
        self.test_points = [
            {"id": "point-1", "point": "Quantum computing uses quantum bits or qubits."},
            {"id": "point-2", "point": "Neural networks are a form of machine learning inspired by the human brain."}
        ]
        
        # Mock papers from ArXiv
        self.mock_papers = [
            {
                "id": "2101.12345",
                "title": "Advances in Quantum Computing",
                "authors": ["A. Researcher", "B. Scientist"],
                "summary": "This paper discusses recent advances in quantum computing technology.",
                "arxiv_url": "https://arxiv.org/abs/2101.12345",
                "published": "2021-01-01"
            },
            {
                "id": "2102.67890",
                "title": "Neural Networks and Deep Learning",
                "authors": ["C. Developer", "D. Engineer"],
                "summary": "This paper covers fundamental principles of neural networks and deep learning.",
                "arxiv_url": "https://arxiv.org/abs/2102.67890",
                "published": "2021-02-01"
            }
        ]
        
        # Mock config
        self.config = {
            'arxiv': {
                'enabled': True,
                'max_references_per_point': 2,
                'cache_dir': 'test_cache',
                'update_bibliography': True
            },
            'latex': {
                'output_dir': 'test_output',
                'output_filename': 'test_report'
            }
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test directories if they were created
        if os.path.exists('test_cache'):
            import shutil
            shutil.rmtree('test_cache')
        if os.path.exists('test_output'):
            import shutil
            shutil.rmtree('test_output')
    
    @patch('src.content_assessor.ArxivReferenceService')
    def test_attach_arxiv_references_enabled(self, mock_arxiv_service_class):
        """Test that ArXiv references are attached when enabled."""
        # Setup mock ArXiv service
        mock_arxiv_service = MagicMock()
        mock_arxiv_service_class.return_value = mock_arxiv_service
        
        # Mock the get_references_for_content method to return our mock papers
        mock_arxiv_service.get_references_for_content.return_value = self.mock_papers
        
        # Mock the update_latex_bibliography method to return success
        mock_arxiv_service.update_latex_bibliography.return_value = True
        
        # Call the method under test
        self.assessor._attach_arxiv_references(self.test_points, self.test_content, self.config)
        
        # Verify ArXiv service was initialized
        mock_arxiv_service_class.assert_called_once_with(cache_dir='test_cache')
        
        # Verify get_references_for_content was called for each point
        expected_calls = len(self.test_points)
        self.assertEqual(mock_arxiv_service.get_references_for_content.call_count, expected_calls)
        
        # Verify references were attached to points
        for point in self.test_points:
            self.assertIn('references', point)
            self.assertEqual(len(point['references']), len(self.mock_papers))
            
            # Verify reference format
            first_ref = point['references'][0]
            self.assertIn('id', first_ref)
            self.assertIn('title', first_ref)
            self.assertIn('authors', first_ref)
            self.assertIn('summary', first_ref)
            self.assertIn('url', first_ref)
            self.assertIn('published', first_ref)
        
        # Verify bibliography was updated
        mock_arxiv_service.update_latex_bibliography.assert_called_once()
    
    @patch('src.content_assessor.ArxivReferenceService')
    def test_attach_arxiv_references_disabled(self, mock_arxiv_service_class):
        """Test that ArXiv references are not attached when disabled."""
        # Set config to disable ArXiv references
        config = self.config.copy()
        config['arxiv']['enabled'] = False
        
        # Call the method under test
        self.assessor._attach_arxiv_references(self.test_points, self.test_content, config)
        
        # Verify ArXiv service was not initialized
        mock_arxiv_service_class.assert_not_called()
        
        # Verify no references were attached
        for point in self.test_points:
            self.assertNotIn('references', point)
    
    @patch('src.content_assessor.ArxivReferenceService')
    def test_error_handling_during_reference_lookup(self, mock_arxiv_service_class):
        """Test that errors during reference lookup are handled gracefully."""
        # Setup mock ArXiv service
        mock_arxiv_service = MagicMock()
        mock_arxiv_service_class.return_value = mock_arxiv_service
        
        # Make get_references_for_content raise an exception for the first point
        mock_arxiv_service.get_references_for_content.side_effect = [
            Exception("API error"),  # First call fails
            self.mock_papers         # Second call succeeds
        ]
        
        # Mock the update_latex_bibliography method to return success
        mock_arxiv_service.update_latex_bibliography.return_value = True
        
        # Call the method under test
        self.assessor._attach_arxiv_references(self.test_points, self.test_content, self.config)
        
        # Verify the method continued despite the error
        self.assertEqual(mock_arxiv_service.get_references_for_content.call_count, 2)
        
        # Verify references were attached only to the second point
        self.assertNotIn('references', self.test_points[0])
        self.assertIn('references', self.test_points[1])
    
    @patch('src.content_assessor.ArxivReferenceService')
    def test_bibliography_update_failure(self, mock_arxiv_service_class):
        """Test that bibliography update failures are handled gracefully."""
        # Setup mock ArXiv service
        mock_arxiv_service = MagicMock()
        mock_arxiv_service_class.return_value = mock_arxiv_service
        
        # Mock the get_references_for_content method to return our mock papers
        mock_arxiv_service.get_references_for_content.return_value = self.mock_papers
        
        # Make update_latex_bibliography raise an exception
        mock_arxiv_service.update_latex_bibliography.side_effect = Exception("File write error")
        
        # Call the method under test
        self.assessor._attach_arxiv_references(self.test_points, self.test_content, self.config)
        
        # Verify the method continued despite the error
        mock_arxiv_service.update_latex_bibliography.assert_called_once()
        
        # Verify references were still attached to points
        for point in self.test_points:
            self.assertIn('references', point)
    
    @patch('src.content_assessor.ArxivReferenceService')
    @patch('src.content_assessor.call_with_retry')
    def test_end_to_end_integration(self, mock_call_with_retry, mock_arxiv_service_class):
        """Test the end-to-end integration of ArXiv references in extract_points."""
        # Setup mock ArXiv service
        mock_arxiv_service = MagicMock()
        mock_arxiv_service_class.return_value = mock_arxiv_service
        
        # Mock the get_references_for_content method to return our mock papers
        mock_arxiv_service.get_references_for_content.return_value = self.mock_papers
        
        # Mock the call_with_retry response
        mock_result = {
            "points": self.test_points
        }
        mock_call_with_retry.return_value = (mock_result, "test-model")
        
        # Call extract_points
        points = self.assessor.extract_points(self.test_content, self.config)
        
        # Verify points were returned with references
        self.assertEqual(len(points), len(self.test_points))
        
        # Verify references were attached
        for point in points:
            self.assertIn('references', point)
            self.assertEqual(len(point['references']), len(self.mock_papers))


if __name__ == '__main__':
    unittest.main()
