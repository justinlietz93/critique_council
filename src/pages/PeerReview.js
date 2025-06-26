import React, { useState } from 'react';
import { 
  Box, 
  Grid, 
  Paper, 
  Typography, 
  Tabs, 
  Tab, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemSecondaryAction, 
  IconButton, 
  Button, 
  Chip, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Divider
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Check as CheckIcon,
  Close as CloseIcon
} from '@mui/icons-material';

// Mock data for peer reviews
const mockAssignedReviews = [
  {
    id: 'review1',
    documentId: 'arxiv.123456.1',
    documentTitle: 'Machine Learning Applications in Legal Analysis',
    assignedDate: '2023-07-15',
    dueDate: '2023-07-30',
    status: 'pending',
    type: 'scientific'
  },
  {
    id: 'review2',
    documentId: 'westlaw.789012.3',
    documentTitle: 'Precedent Analysis in Patent Law',
    assignedDate: '2023-07-10',
    dueDate: '2023-07-25',
    status: 'in_progress',
    type: 'legal'
  }
];

const mockSubmittedReviews = [
  {
    id: 'review3',
    documentId: 'arxiv.345678.2',
    documentTitle: 'Neural Networks for Legal Document Classification',
    submittedDate: '2023-07-05',
    status: 'completed',
    rating: 4,
    type: 'scientific'
  },
  {
    id: 'review4',
    documentId: 'westlaw.901234.4',
    documentTitle: 'Comparative Analysis of Privacy Laws',
    submittedDate: '2023-06-28',
    status: 'completed',
    rating: 3,
    type: 'legal'
  }
];

function PeerReview() {
  const [tabValue, setTabValue] = useState(0);
  const [assignedReviews, setAssignedReviews] = useState(mockAssignedReviews);
  const [submittedReviews, setSubmittedReviews] = useState(mockSubmittedReviews);
  const [openReviewDialog, setOpenReviewDialog] = useState(false);
  const [selectedReview, setSelectedReview] = useState(null);
  const [reviewForm, setReviewForm] = useState({
    rating: 3,
    comments: '',
    recommendation: 'accept'
  });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleOpenReview = (review) => {
    setSelectedReview(review);
    setReviewForm({
      rating: 3,
      comments: '',
      recommendation: 'accept'
    });
    setOpenReviewDialog(true);
  };

  const handleCloseReview = () => {
    setOpenReviewDialog(false);
    setSelectedReview(null);
  };

  const handleFormChange = (field, value) => {
    setReviewForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmitReview = () => {
    // In a real app, this would submit the review to the backend
    
    // Update the review status
    const updatedAssignedReviews = assignedReviews.filter(
      review => review.id !== selectedReview.id
    );
    
    // Add to submitted reviews
    const newSubmittedReview = {
      ...selectedReview,
      status: 'completed',
      submittedDate: new Date().toISOString().split('T')[0],
      rating: reviewForm.rating,
      recommendation: reviewForm.recommendation,
      comments: reviewForm.comments
    };
    
    setAssignedReviews(updatedAssignedReviews);
    setSubmittedReviews([newSubmittedReview, ...submittedReviews]);
    
    handleCloseReview();
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'pending':
        return <Chip label="Pending" color="warning" size="small" />;
      case 'in_progress':
        return <Chip label="In Progress" color="info" size="small" />;
      case 'completed':
        return <Chip label="Completed" color="success" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  const getRecommendationChip = (recommendation) => {
    switch (recommendation) {
      case 'accept':
        return <Chip label="Accept" color="success" size="small" />;
      case 'revise':
        return <Chip label="Revise" color="warning" size="small" />;
      case 'reject':
        return <Chip label="Reject" color="error" size="small" />;
      default:
        return null;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Peer Review
      </Typography>
      
      <Paper sx={{ mb: 3, borderRadius: 2 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label={`Assigned (${assignedReviews.length})`} />
          <Tab label={`Submitted (${submittedReviews.length})`} />
        </Tabs>
      </Paper>
      
      {tabValue === 0 && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            Assigned Reviews
          </Typography>
          
          {assignedReviews.length > 0 ? (
            <List>
              {assignedReviews.map((review) => (
                <React.Fragment key={review.id}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {review.documentTitle}
                          <Chip 
                            label={review.type === 'legal' ? 'Legal' : 'Scientific'} 
                            size="small" 
                            color={review.type === 'legal' ? 'primary' : 'accent'}
                            sx={{ ml: 1 }}
                          />
                          {getStatusChip(review.status)}
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography component="span" variant="body2">
                            Assigned: {review.assignedDate} • Due: {review.dueDate}
                          </Typography>
                        </>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Button
                        variant="contained"
                        color="primary"
                        size="small"
                        startIcon={<EditIcon />}
                        onClick={() => handleOpenReview(review)}
                      >
                        Review
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No assigned reviews at this time.
            </Typography>
          )}
        </Paper>
      )}
      
      {tabValue === 1 && (
        <Paper sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            Submitted Reviews
          </Typography>
          
          {submittedReviews.length > 0 ? (
            <List>
              {submittedReviews.map((review) => (
                <React.Fragment key={review.id}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {review.documentTitle}
                          <Chip 
                            label={review.type === 'legal' ? 'Legal' : 'Scientific'} 
                            size="small" 
                            color={review.type === 'legal' ? 'primary' : 'accent'}
                            sx={{ ml: 1 }}
                          />
                          {review.recommendation && getRecommendationChip(review.recommendation)}
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography component="span" variant="body2">
                            Submitted: {review.submittedDate} • Rating: {review.rating}/5
                          </Typography>
                          {review.comments && (
                            <Typography component="p" variant="body2" sx={{ mt: 1 }}>
                              "{review.comments.substring(0, 100)}..."
                            </Typography>
                          )}
                        </>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton edge="end">
                        <AssignmentIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No submitted reviews yet.
            </Typography>
          )}
        </Paper>
      )}
      
      {/* Review Dialog */}
      <Dialog open={openReviewDialog} onClose={handleCloseReview} maxWidth="md" fullWidth>
        <DialogTitle>
          Peer Review: {selectedReview?.documentTitle}
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Document Information
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Type:</strong> {selectedReview?.type === 'legal' ? 'Legal Document' : 'Scientific Paper'}
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Assigned Date:</strong> {selectedReview?.assignedDate}
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Due Date:</strong> {selectedReview?.dueDate}
              </Typography>
            </Grid>
            
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" gutterBottom>
                Review Form
              </Typography>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="rating-label">Rating (1-5)</InputLabel>
                <Select
                  labelId="rating-label"
                  value={reviewForm.rating}
                  onChange={(e) => handleFormChange('rating', e.target.value)}
                  label="Rating (1-5)"
                >
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <MenuItem key={rating} value={rating}>
                      {rating} {rating === 1 ? 'Star' : 'Stars'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="recommendation-label">Recommendation</InputLabel>
                <Select
                  labelId="recommendation-label"
                  value={reviewForm.recommendation}
                  onChange={(e) => handleFormChange('recommendation', e.target.value)}
                  label="Recommendation"
                >
                  <MenuItem value="accept">Accept</MenuItem>
                  <MenuItem value="revise">Revise</MenuItem>
                  <MenuItem value="reject">Reject</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={8}
                label="Review Comments"
                placeholder="Provide your detailed review comments here..."
                value={reviewForm.comments}
                onChange={(e) => handleFormChange('comments', e.target.value)}
                margin="normal"
                variant="outlined"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseReview} startIcon={<CloseIcon />}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleSubmitReview}
            startIcon={<CheckIcon />}
            disabled={!reviewForm.comments.trim()}
          >
            Submit Review
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default PeerReview;