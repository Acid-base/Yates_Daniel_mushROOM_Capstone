
// src/main.tsx
import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import MushroomDetails from './components/MushroomDetails'; // Ensure this path is correct
import MushroomSearch from './components/MushroomSearch';

const App: React.FC = () => {
return (
    <Router>
      <Switch>
    <Route path="/details" component={MushroomDetails} />
    <Route path="/search" component={MushroomSearch} />
    <Route path="/error" component={ErrorPage} />
import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import MushroomDetails from './components/MushroomDetails'; // Ensure this path is correct
import MushroomSearch from './components/MushroomSearch';

const App: React.FC = () => {
  return (
    <Router>
      <Switch>
        <Route path="/details" component={MushroomDetails} />
        <Route path="/search" component={MushroomSearch} />
        {/* Other routes */}
      </Switch>
    </Router>
  );
};

export default App;
