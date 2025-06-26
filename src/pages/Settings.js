import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemSecondaryAction, 
  Switch, 
  Divider, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Button, 
  Alert,
  Grid
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';

function Settings() {
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      browser: true,
      peerReview: true,
      newCitations: false
    },
    display: {
      theme: 'light',
      fontSize: 'medium',
      compactView: false
    },
    search: {
      defaultSource: 'all',
      resultsPerPage: 20,
      saveSearchHistory: true
    },
    privacy: {
      shareUsageData: true,
      allowRecommendations: true
    },
    integration: {
      westlawApiKey: '••••••••••••••••',
      arxivApiKey: '••••••••••••••••'
    }
  });
  
  const [success, setSuccess] = useState(false);
  
  const handleToggle = (category, setting) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: !prev[category][setting]
      }
    }));
  };
  
  const handleChange = (category, setting, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: value
      }
    }));
  };
  
  const handleSave = () => {
    // In a real app, this would save the settings to the backend
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Settings saved successfully!
        </Alert>
      )}
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Notifications
            </Typography>
            
            <List>
              <ListItem>
                <ListItemText 
                  primary="Email Notifications" 
                  secondary="Receive notifications via email" 
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={settings.notifications.email}
                    onChange={() => handleToggle('notifications', 'email')}
                  />
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Browser Notifications" 
                  secondary="Receive notifications in your browser" 
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={settings.notifications.browser}
                    onChange={() => handleToggle('notifications', 'browser')}
                  />
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Peer Review Notifications" 
                  secondary="Get notified about peer review assignments and updates" 
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={settings.notifications.peerReview}
                    onChange={() => handleToggle('notifications', 'peerReview')}
                  />
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="New Citations Notifications" 
                  secondary="Get notified when your saved documents are cited" 
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={settings.notifications.newCitations}
                    onChange={() => handleToggle('notifications', 'newCitations')}
                  />
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Paper>
          
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Display
            </Typography>
            
            <List>
              <ListItem>
                <ListItemText primary="Theme" />
                <ListItemSecondaryAction>
                  <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                    <Select
                      value={settings.display.theme}
                      onChange={(e) => handleChange('display', 'theme', e.target.value)}
                    >
                      <MenuItem value="light">Light</MenuItem>
                      <MenuItem value="dark">Dark</MenuItem>
                      <MenuItem value="system">System</MenuItem>
                    </Select>
                  </FormControl>
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText primary="Font Size" />
                <ListItemSecondaryAction>
                  <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                    <Select
                      value={settings.display.fontSize}
                      onChange={(e) => handleChange('display', 'fontSize', e.target.value)}
                    >
                      <MenuItem value="small">Small</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="large">Large</MenuItem>
                    </Select>
                  </FormControl>
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Compact View" 
                  secondary="Use a more compact layout to show more content" 
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={settings.display.compactView}
                    onChange={() => handleToggle('display', 'compactView')}
                  />
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Search
            </Typography>
            
            <List>
              <ListItem>
                <ListItemText primary="Default Search Source" />
                <ListItemSecondaryAction>
                  <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                    <Select
                      value={settings.search.defaultSource}
                      onChange={(e) => handleChange('search', 'defaultSource', e.target.value)}
                    >
                      <MenuItem value="all">All Sources</MenuItem>
                      <MenuItem value="westlaw">Westlaw Only</MenuItem>
                      <MenuItem value="arxiv">ArXiv Only</MenuItem>
                    </Select>
                  </FormControl>
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText primary="Results Per Page" />
                <ListItemSecondaryAction>
                  <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
                    <Select
                      value={settings.search.resultsPerPage}
                      onChange={(e) => handleChange('search', 'resultsPerPage', e.target.value)}
                    >
                      <MenuItem value={10}>10</MenuItem>
                      <MenuItem value={20}>20</MenuItem>
                      <MenuItem value={50}>50</MenuItem>
                      <MenuItem value={100}>100</MenuItem>
                    </Select>
                  </FormControl>
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Save Search History" 
                  secondary="Save your search queries for future reference" 
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={settings.search.saveSearchHistory}
                    onChange={() => handleToggle('search', 'saveSearchHistory')}
                  />
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Paper>
          
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Privacy
            </Typography>
            
            <List>
              <ListItem>
                <ListItemText 
                  primary="Share Usage Data" 
                  secondary="Share anonymous usage data to help improve the platform" 
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={settings.privacy.shareUsageData}
                    onChange={() => handleToggle('privacy', 'shareUsageData')}
                  />
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Allow Recommendations" 
                  secondary="Allow the system to recommend documents based on your activity" 
                />
                <ListItemSecondaryAction>
                  <Switch
                    edge="end"
                    checked={settings.privacy.allowRecommendations}
                    onChange={() => handleToggle('privacy', 'allowRecommendations')}
                  />
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Paper>
          
          <Paper sx={{ p: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              API Integration
            </Typography>
            
            <List>
              <ListItem>
                <ListItemText 
                  primary="Westlaw API Key" 
                  secondary="Your Westlaw API key for accessing legal documents" 
                />
                <ListItemSecondaryAction>
                  <Button size="small" variant="outlined">
                    Change
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="ArXiv API Key" 
                  secondary="Your ArXiv API key for accessing scientific papers" 
                />
                <ListItemSecondaryAction>
                  <Button size="small" variant="outlined">
                    Change
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              size="large"
            >
              Save All Settings
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Settings;