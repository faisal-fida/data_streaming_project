import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [sensorData, setSensorData] = useState({
    sensor_id: '',
    temperature: '',
    humidity: '',
    timestamp: ''
  });
  const [receivedData, setReceivedData] = useState([]);
  const [message, setMessage] = useState('');
  const [loadingSend, setLoadingSend] = useState(false);
  const [loadingFetch, setLoadingFetch] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const errs = {};
    if (!sensorData.sensor_id || isNaN(sensorData.sensor_id)) errs.sensor_id = 'Sensor ID is required and must be a number';
    if (!sensorData.temperature || isNaN(sensorData.temperature)) errs.temperature = 'Temperature is required and must be a number';
    if (!sensorData.humidity || isNaN(sensorData.humidity)) errs.humidity = 'Humidity is required and must be a number';
    if (!sensorData.timestamp || isNaN(sensorData.timestamp)) errs.timestamp = 'Timestamp is required and must be a number';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleChange = (e) => {
    setSensorData({
      ...sensorData,
      [e.target.name]: e.target.value
    });
  };

  const sendData = async () => {
    if (!validate()) {
      setMessage('Please fix validation errors');
      return;
    }
    setLoadingSend(true);
    setMessage('');
    try {
      const response = await axios.post(`${API_BASE_URL}/send`, {
        sensor_id: parseInt(sensorData.sensor_id),
        temperature: parseFloat(sensorData.temperature),
        humidity: parseFloat(sensorData.humidity),
        timestamp: parseInt(sensorData.timestamp)
      });
      setMessage(response.data.message);
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Failed to send data');
    } finally {
      setLoadingSend(false);
    }
  };

  const fetchData = async () => {
    setLoadingFetch(true);
    setMessage('');
    try {
      const response = await axios.get(`${API_BASE_URL}/receive`);
      setReceivedData(response.data);
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Failed to fetch data');
    } finally {
      setLoadingFetch(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div style={{ maxWidth: 600, margin: 'auto', padding: 20 }}>
      <h1>Kafka Data Streaming</h1>
      <h2>Send Data</h2>
      <input
        type="number"
        name="sensor_id"
        placeholder="Sensor ID"
        value={sensorData.sensor_id}
        onChange={handleChange}
        style={{ width: '100%', marginBottom: 10 }}
      />
      {errors.sensor_id && <p style={{ color: 'red' }}>{errors.sensor_id}</p>}
      <input
        type="number"
        step="0.01"
        name="temperature"
        placeholder="Temperature"
        value={sensorData.temperature}
        onChange={handleChange}
        style={{ width: '100%', marginBottom: 10 }}
      />
      {errors.temperature && <p style={{ color: 'red' }}>{errors.temperature}</p>}
      <input
        type="number"
        step="0.01"
        name="humidity"
        placeholder="Humidity"
        value={sensorData.humidity}
        onChange={handleChange}
        style={{ width: '100%', marginBottom: 10 }}
      />
      {errors.humidity && <p style={{ color: 'red' }}>{errors.humidity}</p>}
      <input
        type="number"
        name="timestamp"
        placeholder="Timestamp"
        value={sensorData.timestamp}
        onChange={handleChange}
        style={{ width: '100%', marginBottom: 10 }}
      />
      {errors.timestamp && <p style={{ color: 'red' }}>{errors.timestamp}</p>}
      <button onClick={sendData} style={{ width: '100%', padding: 10 }} disabled={loadingSend}>
        {loadingSend ? 'Sending...' : 'Send to Kafka'}
      </button>
      {message && <p>{message}</p>}

      <h2>Received Data</h2>
      <button onClick={fetchData} style={{ marginBottom: 10 }} disabled={loadingFetch}>
        {loadingFetch ? 'Loading...' : 'Refresh Data'}
      </button>
      <table border="1" cellPadding="5" style={{ width: '100%' }}>
        <thead>
          <tr>
            <th>Sensor ID</th>
            <th>Temperature</th>
            <th>Humidity</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {receivedData.map((item, index) => (
            <tr key={index}>
              <td>{item.sensor_id}</td>
              <td>{item.temperature}</td>
              <td>{item.humidity}</td>
              <td>{item.timestamp}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
