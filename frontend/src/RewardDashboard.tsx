import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Button, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  Alert, CircularProgress, Select, MenuItem, InputLabel, FormControl
} from '@mui/material';
import api from './api';

interface RewardAccount {
  id: number;
  subject_id: number;
  balance: number;
}

interface RewardRule {
  id: number;
  threshold_value: number;
  reward_amount: number;
  comparison_operator: string;
  behavior_definition_id: number | null;
}

interface Props {
  subjectId: number;
}

const RewardDashboard: React.FC<Props> = ({ subjectId }) => {
  const [account, setAccount] = useState<RewardAccount | null>(null);
  const [rules, setRules] = useState<RewardRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  // New Rule Form State
  const [newRuleThreshold, setNewRuleThreshold] = useState(80);
  const [newRuleAmount, setNewRuleAmount] = useState(10);
  const [newRuleOperator, setNewRuleOperator] = useState('gt');

  const fetchData = async () => {
    setLoading(true);
    try {
      const accRes = await api.get(`/subjects/${subjectId}/rewards/account`);
      setAccount(accRes.data);

      const rulesRes = await api.get(`/subjects/${subjectId}/rewards/rules`);
      setRules(rulesRes.data);
    } catch (err) {
      console.error(err);
      setMessage({type: 'error', text: 'Failed to load reward data.'});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [subjectId]);

  const handleCreateRule = async () => {
    try {
      await api.post(`/subjects/${subjectId}/rewards/rules`, {
        threshold_value: newRuleThreshold,
        reward_amount: newRuleAmount,
        comparison_operator: newRuleOperator,
        behavior_definition_id: null // Global rule for MVP
      });
      setMessage({type: 'success', text: 'Rule created successfully!'});
      fetchData();
    } catch (err) {
        console.error(err);
      setMessage({type: 'error', text: 'Failed to create rule.'});
    }
  };

  const handleCalculate = async () => {
    try {
      const res = await api.post(`/subjects/${subjectId}/rewards/calculate`);
      setMessage({type: 'success', text: res.data.status || 'Calculation complete'});
      fetchData();
    } catch (err) {
        console.error(err);
      setMessage({type: 'error', text: 'Calculation failed.'});
    }
  };

  const handlePayout = async () => {
      // For MVP, simple payout of $5 (500 cents)
      const amount = 500;
      try {
        await api.post(`/subjects/${subjectId}/rewards/payout`, {
            amount: amount,
            description: "Manual Payout from Dashboard"
        });
        setMessage({type: 'success', text: `Payout of ${amount} processed.`});
        fetchData();
      } catch (err) {
        console.error(err);
        setMessage({type: 'error', text: 'Payout failed (Insufficient funds?).'});
      }
  }

  if (loading && !account) return <CircularProgress />;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Reward Dashboard</Typography>

      {message && <Alert severity={message.type} sx={{ mb: 2 }}>{message.text}</Alert>}

      <Card sx={{ mb: 3, bgcolor: '#e3f2fd' }}>
        <CardContent>
          <Typography variant="h6">Current Balance</Typography>
          <Typography variant="h2">{account ? account.balance : 0} <span style={{fontSize: '1rem'}}>points/cents</span></Typography>
          <Box sx={{ mt: 2 }}>
            <Button variant="contained" color="primary" onClick={handleCalculate} sx={{ mr: 2 }}>
                Run Calculation (Check Rules)
            </Button>
            <Button variant="outlined" color="secondary" onClick={handlePayout}>
                Payout 500
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Typography variant="h5" gutterBottom>Active Rules</Typography>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table>
            <TableHead>
                <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Condition</TableCell>
                    <TableCell>Threshold</TableCell>
                    <TableCell>Reward</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {rules.map((rule) => (
                    <TableRow key={rule.id}>
                        <TableCell>{rule.id}</TableCell>
                        <TableCell>{rule.comparison_operator}</TableCell>
                        <TableCell>{rule.threshold_value}</TableCell>
                        <TableCell>{rule.reward_amount}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="h6">Add New Rule</Typography>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 1 }}>
        <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Operator</InputLabel>
            <Select
                value={newRuleOperator}
                label="Operator"
                onChange={(e) => setNewRuleOperator(e.target.value)}
            >
                <MenuItem value="gt">Greater Than (&gt;)</MenuItem>
                <MenuItem value="lt">Less Than (&lt;)</MenuItem>
                <MenuItem value="eq">Equal (=)</MenuItem>
            </Select>
        </FormControl>
        <TextField
            label="Threshold"
            type="number"
            value={newRuleThreshold}
            onChange={(e) => setNewRuleThreshold(Number(e.target.value))}
        />
        <TextField
            label="Reward Amount"
            type="number"
            value={newRuleAmount}
            onChange={(e) => setNewRuleAmount(Number(e.target.value))}
        />
        <Button variant="contained" onClick={handleCreateRule}>Create Rule</Button>
      </Box>
    </Box>
  );
};

export default RewardDashboard;
