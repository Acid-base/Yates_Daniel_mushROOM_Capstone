// LoginPage.tsx (Refactored with useMutation and local state)
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

interface LoginProps {
  // No props needed
}

const LoginPage: React.FC<LoginProps> = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false); // Local authentication state
  const navigate = useNavigate();

  const loginMutation = useMutation(
    async (credentials: { email: string; password: string }) => {
      const response = await axios.post('/users/login', credentials);
      return response.data;
    },
    {
      onSuccess: (data) => {
        const token = data.token;
        localStorage.setItem('token', token);
        setIsAuthenticated(true);
        navigate('/');
      },
      onError: (error: any) => {
        console.error('Login error:', error);
        if (error.response) {
          setErrorMessage(error.response.data.message || 'Invalid credentials');
        } else {
          setErrorMessage('An error occurred. Please try again later.');
        }
      },
    }
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    loginMutation.mutate({ email, password });
  };

  // Conditionally render content based on authentication
