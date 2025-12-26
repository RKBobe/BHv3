import React, { useState } from 'react';
import { Container, Box, TextField, Button, Typography, Paper } from '@mui/material';
import RewardDashboard from './RewardDashboard';
import api from './api';

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // For MVP demo, we hardcode subject ID after login or let user pick.
  // We'll just assume Subject ID 1 exists for now to show the dashboard.
  const [subjectId, setSubjectId] = useState<number>(1);

  const handleLogin = async () => {
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const res = await api.post('/token', formData);
      const accessToken = res.data.access_token;

      localStorage.setItem('token', accessToken);
      setToken(accessToken);
    } catch (err) {
      console.error(err);
      alert('Login failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography variant="h4" align="center">BHV3 Login</Typography>
          <TextField label="Email" value={email} onChange={e => setEmail(e.target.value)} fullWidth />
          <TextField label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} fullWidth />
          <Button variant="contained" size="large" onClick={handleLogin}>Log In</Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5">BHV3 App</Typography>
        <Button onClick={handleLogout}>Log Out</Button>
      </Box>

      <Box sx={{ mt: 4 }}>
        <Paper elevation={3}>
             {/* In a real app, we would list subjects and select one. Here we default to ID 1 */}
            <RewardDashboard subjectId={subjectId} />
        </Paper>

        <Box sx={{ mt: 2 }}>
            <Typography variant="caption">Debugging: Viewing Subject ID {subjectId}</Typography>
        </Box>
      </Box>
    </Container>
  );
}

export default App;
