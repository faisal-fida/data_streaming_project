import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [sensorData, setSensorData] = useState({
    sensor_id: '',
    temperature: '',
    humidity: '',
    timestamp: ''
  });
  const [receivedData, setReceivedData] = useState([]);
  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    setSensorData({
      ...sensorData,
      [e.target.name]: e.target.value
    });
  };

  const sendData = async () => {
    try {
      const response = await axios.post('http://localhost:8000/send', {
        sensor_id: parseInt(sensorData.sensor_id),
        temperature: parseFloat(sensorData.temperature),
        humidity: parseFloat(sensorData.humidity),
        timestamp: parseInt(sensorData.timestamp)
      });
      setMessage(response.data.message);
    } catch (error) {
      setMessage('Failed to send data');
    }
  };

  const fetchData = async () => {
    try {
      const response = await axios.get('http://localhost:8000/receive');
      setReceivedData(response.data);
    } catch (error) {
      setMessage('Failed to fetch data');
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
      <input
        type="number"
        step="0.01"
        name="temperature"
        placeholder="Temperature"
        value={sensorData.temperature}
        onChange={handleChange}
        style={{ width: '100%', marginBottom: 10 }}
      />
      <input
        type="number"
        step="0.01"
        name="humidity"
        placeholder="Humidity"
        value={sensorData.humidity}
        onChange={handleChange}
        style={{ width: '100%', marginBottom: 10 }}
      />
      <input
        type="number"
        name="timestamp"
        placeholder="Timestamp"
        value={sensorData.timestamp}
        onChange={handleChange}
        style={{ width: '100%', marginBottom: 10 }}
      />
      <button onClick={sendData} style={{ width: '100%', padding: 10 }}>
        Send to Kafka
      </button>
      {message && <p>{message}</p>}

      <h2>Received Data</h2>
      <button onClick={fetchData} style={{ marginBottom: 10 }}>
        Refresh Data
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
