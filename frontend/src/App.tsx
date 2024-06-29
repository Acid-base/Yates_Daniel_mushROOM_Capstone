// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Home from './components/Home';
import ProfilePage from './components/ProfilePage';
import './App.css';

const queryClient = new QueryClient();

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Switch>
          <Route path="/profile" component={ProfilePage} />
          <Route path="/" component={Home} />
        </Switch>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
