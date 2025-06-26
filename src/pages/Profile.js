import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  Grid, 
  Avatar, 
  Divider, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon, 
  Chip,
  Alert
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  School as EducationIcon,
  Work as WorkIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

function Profile() {
  const { currentUser } = useAuth();
  const [formData, setFormData] = useState({
    name: currentUser?.name || '',
    email: currentUser?.email || '',
    institution: 'Stanford University',
    department: 'Law School',
    position: 'Researcher',
    bio: 'Specializing in the intersection of law and technology, with a focus on AI ethics and intellectual property.',
    researchInterests: ['AI Ethics', 'Intellectual Property', 'Data Privacy', 'Legal Analytics']
  });
  const [success, setSuccess] = useState(false);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    // In a real app, this would update the user profile in the backend
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };
  
  const handleAddInterest = () => {
    // In a real app, this would add a new research interest
    const newInterest = prompt('Enter a new research interest:');
    if (newInterest && !formData.researchInterests.includes(newInterest)) {
      setFormData(prev => ({
        ...prev,
        researchInterests: [...prev.researchInterests, newInterest]
      }));
    }
  };
  
  const handleRemoveInterest = (interest) => {
    setFormData(prev => ({
      ...prev,
      researchInterests: prev.researchInterests.filter(i => i !== interest)
    }));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Profile
      </Typography>
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Profile updated successfully!
        </Alert>
      )}
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
              <Avatar
                sx={{ width: 100, height: 100, mb: 2, bgcolor: 'primary.main' }}
              >
                {formData.name.charAt(0)}
              </Avatar>
              <Typography variant="h6">
                {formData.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formData.position} at {formData.institution}
              </Typography>
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <PersonIcon />
                </ListItemIcon>
                <ListItemText primary="Name" secondary={formData.name} />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <EmailIcon />
                </ListItemIcon>
                <ListItemText primary="Email" secondary={formData.email} />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <EducationIcon />
                </ListItemIcon>
                <ListItemText primary="Institution" secondary={formData.institution} />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <WorkIcon />
                </ListItemIcon>
                <ListItemText primary="Position" secondary={formData.position} />
              </ListItem>
            </List>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Research Interests
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
              {formData.researchInterests.map(interest => (
                <Chip 
                  key={interest} 
                  label={interest} 
                  onDelete={() => handleRemoveInterest(interest)}
                  size="small"
                />
              ))}
              <Chip 
                label="Add" 
                onClick={handleAddInterest} 
                color="primary" 
                variant="outlined"
                size="small"
              />
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Edit Profile
            </Typography>
            
            <form onSubmit={handleSubmit}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Full Name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    margin="normal"
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    margin="normal"
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Institution"
                    name="institution"
                    value={formData.institution}
                    onChange={handleChange}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Department"
                    name="department"
                    value={formData.department}
                    onChange={handleChange}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Position"
                    name="position"
                    value={formData.position}
                    onChange={handleChange}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Bio"
                    name="bio"
                    value={formData.bio}
                    onChange={handleChange}
                    margin="normal"
                    multiline
                    rows={4}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    startIcon={<SaveIcon />}
                  >
                    Save Changes
                  </Button>
                </Grid>
              </Grid>
            </form>
          </Paper>
          
          <Paper sx={{ p: 3, mt: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Account Settings
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Button variant="outlined" color="primary" fullWidth>
                  Change Password
                </Button>
              </Grid>
              <Grid item xs={12}>
                <Button variant="outlined" color="secondary" fullWidth>
                  Notification Preferences
                </Button>
              </Grid>
              <Grid item xs={12}>
                <Button variant="outlined" color="error" fullWidth>
                  Delete Account
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Profile;