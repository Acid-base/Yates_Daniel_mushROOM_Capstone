import React, { useState, useEffect } from 'react';
import { Search, Filter, Map, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Mushroom {
  id: number;
  text_name: string;
  author: string;
  rank: number;
  description: {
    general_description: string;
    habitat: string;
    uses: string;
  };
  classification: {
    kingdom: string;
    phylum: string;
    class: string;
    order: string;
    family: string;
  };
  observation_count: number;
}

interface Observation {
  id: number;
  when: string;
  notes: string;
  location: {
    name: string;
    latitude: number;
    longitude: number;
  };
}

const App: React.FC = () => {
  const [mushrooms, setMushrooms] = useState<Mushroom[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [family, setFamily] = useState('');
  const [habitat, setHabitat] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedMushroom, setSelectedMushroom] = useState<Mushroom | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [showMap, setShowMap] = useState(false);

  useEffect(() => {
    fetchMushrooms();
  }, [searchTerm, family, habitat, currentPage]);

  const fetchMushrooms = async () => {
    try {
      const response = await fetch(`/api/mushrooms?search=${searchTerm}&family=${family}&habitat=${habitat}&page=${currentPage}`);
      const data = await response.json();
      setMushrooms(data.mushrooms);
      setTotalPages(data.pages);
    } catch (error) {
      console.error('Error fetching mushrooms:', error);
    }
  };

  const fetchMushroomDetails = async (id: number) => {
    try {
      const response = await fetch(`/api/mushrooms/${id}`);
      const data = await response.json();
      setSelectedMushroom(data);
      fetchObservations(id);
    } catch (error) {
      console.error('Error fetching mushroom details:', error);
    }
  };

  const fetchObservations = async (id: number) => {
    try {
      const response = await fetch(`/api/mushrooms/${id}/observations`);
      const data = await response.json();
      setObservations(data);
    } catch (error) {
      console.error('Error fetching observations:', error);
    }
  };

  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  const SimpleMap: React.FC<{ observations: Observation[] }> = ({ observations }) => {
    return (
      <div className="h-[300px] bg-gray-200 relative">
        {observations.map((obs) => (
          <div
            key={obs.id}
            className="absolute w-2 h-2 bg-red-500 rounded-full"
            style={{
              left: `${((obs.location.longitude + 180) / 360) * 100}%`,
              top: `${((90 - obs.location.latitude) / 180) * 100}%`,
            }}
            title={`${obs.location.name}: ${new Date(obs.when).toLocaleDateString()}`}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Mushroom Field Guide</h1>
      <div className="mb-4 flex flex-wrap gap-2">
        <Input
          type="text"
          placeholder="Search mushrooms..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-grow"
        />
        <Select value={family} onValueChange={setFamily}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select family" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Agaricaceae">Agaricaceae</SelectItem>
            <SelectItem value="Boletaceae">Boletaceae</SelectItem>
            {/* Add more families */}
          </SelectContent>
        </Select>
        <Select value={habitat} onValueChange={setHabitat}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select habitat" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="forest">Forest</SelectItem>
            <SelectItem value="grassland">Grassland</SelectItem>
            {/* Add more habitats */}
          </SelectContent>
        </Select>
        <Button onClick={() => fetchMushrooms()}>
          <Search className="mr-2 h-4 w-4" /> Search
        </Button>
        <Button onClick={() => setShowMap(!showMap)}>
          <Map className="mr-2 h-4 w-4" /> {showMap ? 'Hide' : 'Show'} Map
        </Button>
      </div>
      {showMap ? (
        <SimpleMap observations={observations} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mushrooms.map((mushroom) => (
            <Card key={mushroom.id} onClick={() => fetchMushroomDetails(mushroom.id)} className="cursor-pointer">
              <CardHeader>
                <h2 className="text-xl font-semibold">{mushroom.text_name}</h2>
                <p className="text-sm text-gray-500">{mushroom.author}</p>
              </CardHeader>
              <CardContent>
                <img src={`/api/placeholder/300/200`} alt={mushroom.text_name} className="w-full h-40 object-cover mb-2" />
                <p className="mb-2">{mushroom.description?.general_description?.slice(0, 100)}...</p>
                <p className="text-sm">
                  <strong>Family:</strong> {mushroom.classification?.family}
                </p>
                <p className="text-sm">
                  <strong>Observations:</strong> {mushroom.observation_count}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <div className="mt-4 flex justify-center">
        <Button
          onClick={() => paginate(currentPage - 1)}
          disabled={currentPage === 1}
          className="mr-2"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          onClick={() => paginate(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
      <Dialog open={!!selectedMushroom} onOpenChange={() => setSelectedMushroom(null)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{selectedMushroom?.text_name}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <img src={`/api/placeholder/400/300`} alt={selectedMushroom?.text_name} className="w-full h-60 object-cover mb-2" />
              <p className="mb-2">{selectedMushroom?.description?.general_description}</p>
              <p className="text-sm">
                <strong>Habitat:</strong> {selectedMushroom?.description?.habitat}
              </p>
              <p className="text-sm">
                <strong>Uses:</strong> {selectedMushroom?.description?.uses}
              </p>
              <p className="text-sm">
                <strong>Family:</strong> {selectedMushroom?.classification?.family}
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2">Observations</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={observations}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="when" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="id" name="Observation Count" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
              <SimpleMap observations={observations} />
              <ul className="mt-4 max-h-60 overflow-y-auto">
                {observations.map((obs) => (
                  <li key={obs.id} className="mb-2">
                    <p className="text-sm">
                      <strong>Date:</strong> {new Date(obs.when).toLocaleDateString()}
                    </p>
                    <p className="text-sm">
                      <strong>Location:</strong> {obs.location.name}
                    </p>
                    <p className="text-sm">
                      <strong>Notes:</strong> {obs.notes}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default App;
