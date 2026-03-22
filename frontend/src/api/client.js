import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getBriefs = (params) => client.get('/briefs/', { params });
export const ingestManual = (data) => client.post('/ingest/manual', data);
export const postFeedback = (id, data) => client.post(`/briefs/${id}/feedback`, data);

export default client;
