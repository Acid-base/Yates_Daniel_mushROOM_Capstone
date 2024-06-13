const request = require('supertest');
const app = require('../app'); // Assuming you have an Express app in app.js

describe('GET /mushrooms', () => {
  it('should return a paginated list of mushrooms', async () => {
    const response = await request(app).get('/mushrooms?page=1&limit=10');
    expect(response.status).toBe(200); 
    expect(response.body).toHaveProperty('mushrooms');
    expect(response.body).toHaveProperty('total');
    expect(response.body).toHaveProperty('page');
    expect(response.body).toHaveProperty('pages');
  });

  it('should filter mushrooms by region', async () => {
    const response = await request(app).get('/mushrooms?region=North America');
    expect(response.status).toBe(200);
    expect(response.body.mushrooms).toBeInstanceOf(Array); 
  });

  it('should filter mushrooms by edibility', async () => {
    const response = await request(app).get('/mushrooms?edibility=edible');
    expect(response.status).toBe(200);
    expect(response.body.mushrooms).toBeInstanceOf(Array);
  });
});
