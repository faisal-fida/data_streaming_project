import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [sensorData, setSensorData] = useState({
    sensor_id: '',
    temperature: '',
    humidity: '',
    timestamp: Math.floor(Date.now() / 1000) // Default to current timestamp
  });
  const [receivedData, setReceivedData] = useState([]);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'
  const [loadingSend, setLoadingSend] = useState(false);
  const [loadingFetch, setLoadingFetch] = useState(false);
  const [errors, setErrors] = useState({});
  const [filters, setFilters] = useState({
    sensor_id: '',
    min_temp: '',
    max_temp: '',
    limit: 10
  });
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(null);

  // Validate form data
  const validate = () => {
    const errs = {};
    if (!sensorData.sensor_id || isNaN(sensorData.sensor_id) || parseInt(sensorData.sensor_id) <= 0) {
      errs.sensor_id = 'Sensor ID is required and must be a positive number';
    }
    
    if (!sensorData.temperature || isNaN(sensorData.temperature)) {
      errs.temperature = 'Temperature is required and must be a number';
    } else if (parseFloat(sensorData.temperature) < -50 || parseFloat(sensorData.temperature) > 100) {
      errs.temperature = 'Temperature must be between -50°C and 100°C';
    }
    
    if (!sensorData.humidity || isNaN(sensorData.humidity)) {
      errs.humidity = 'Humidity is required and must be a number';
    } else if (parseFloat(sensorData.humidity) < 0 || parseFloat(sensorData.humidity) > 100) {
      errs.humidity = 'Humidity must be between 0% and 100%';
    }
    
    if (!sensorData.timestamp || isNaN(sensorData.timestamp)) {
      errs.timestamp = 'Timestamp is required and must be a number';
    }
    
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // Handle form input changes
  const handleChange = (e) => {
    setSensorData({
      ...sensorData,
      [e.target.name]: e.target.value
    });
  };

  // Handle filter changes
  const handleFilterChange = (e) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value
    });
  };

  // Send data to API
  const sendData = async () => {
    if (!validate()) {
      setMessage('Please fix validation errors');
      setMessageType('error');
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
      setMessageType('success');
      
      // Reset form with a new timestamp
      setSensorData({
        ...sensorData,
        timestamp: Math.floor(Date.now() / 1000)
      });
      
      // Refresh data after successful send
      fetchData();
      
    } catch (error) {
      console.error('Error sending data:', error);
      setMessage(error.response?.data?.detail || 'Failed to send data');
      setMessageType('error');
    } finally {
      setLoadingSend(false);
    }
  };

  // Generate current timestamp
  const generateTimestamp = () => {
    setSensorData({
      ...sensorData,
      timestamp: Math.floor(Date.now() / 1000)
    });
  };

  // Fetch data with filters
  const fetchData = useCallback(async () => {
    setLoadingFetch(true);
    
    try {
      // Build query parameters
      const params = {};
      
      if (filters.sensor_id && !isNaN(filters.sensor_id)) {
        params.sensor_id = parseInt(filters.sensor_id);
      }
      
      if (filters.min_temp && !isNaN(filters.min_temp)) {
        params.min_temp = parseFloat(filters.min_temp);
      }
      
      if (filters.max_temp && !isNaN(filters.max_temp)) {
        params.max_temp = parseFloat(filters.max_temp);
      }
      
      if (filters.limit && !isNaN(filters.limit)) {
        params.limit = parseInt(filters.limit);
      }
      
      const response = await axios.get(`${API_BASE_URL}/receive`, { params });
      setReceivedData(response.data);
      
      // Clear any error messages on successful fetch
      if (messageType === 'error') {
        setMessage('');
        setMessageType('');
      }
      
    } catch (error) {
      console.error('Error fetching data:', error);
      setMessage(error.response?.data?.detail || 'Failed to fetch data');
      setMessageType('error');
    } finally {
      setLoadingFetch(false);
    }
  }, [filters, messageType]);

  // Toggle auto-refresh
  const toggleAutoRefresh = () => {
    if (autoRefresh) {
      // Turn off auto-refresh
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    } else {
      // Turn on auto-refresh (every 5 seconds)
      const interval = setInterval(() => {
        fetchData();
      }, 5000);
      setRefreshInterval(interval);
    }
    
    setAutoRefresh(!autoRefresh);
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  // Initial data fetch
  useEffect(() => {
    fetchData();
    
    // Cleanup interval on component unmount
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [fetchData, refreshInterval]);

  return (
    <div className="app-container">
      <div className="header">
        <h1>Kafka Data Streaming Dashboard</h1>
      </div>
      
      <div className="form-container">
        <h2>Send Sensor Data</h2>
        
        <div className="form-group">
          <label htmlFor="sensor_id">Sensor ID:</label>
          <input
            id="sensor_id"
            type="number"
            name="sensor_id"
            className="form-control"
            placeholder="Enter sensor ID"
            value={sensorData.sensor_id}
            onChange={handleChange}
          />
          {errors.sensor_id && <div className="error-message">{errors.sensor_id}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="temperature">Temperature (°C):</label>
          <input
            id="temperature"
            type="number"
            step="0.01"
            name="temperature"
            className="form-control"
            placeholder="Enter temperature"
            value={sensorData.temperature}
            onChange={handleChange}
          />
          {errors.temperature && <div className="error-message">{errors.temperature}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="humidity">Humidity (%):</label>
          <input
            id="humidity"
            type="number"
            step="0.01"
            name="humidity"
            className="form-control"
            placeholder="Enter humidity"
            value={sensorData.humidity}
            onChange={handleChange}
          />
          {errors.humidity && <div className="error-message">{errors.humidity}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="timestamp">Timestamp:</label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              id="timestamp"
              type="number"
              name="timestamp"
              className="form-control"
              placeholder="Unix timestamp"
              value={sensorData.timestamp}
              onChange={handleChange}
            />
            <button 
              onClick={generateTimestamp} 
              className="refresh-button"
              title="Generate current timestamp"
            >
              Now
            </button>
          </div>
          {errors.timestamp && <div className="error-message">{errors.timestamp}</div>}
          {sensorData.timestamp && (
            <div className="timestamp-display">
              {formatTimestamp(sensorData.timestamp)}
            </div>
          )}
        </div>
        
        <button 
          onClick={sendData} 
          className="button" 
          disabled={loadingSend}
        >
          {loadingSend ? (
            <>
              Sending... 
              <span className="loading-spinner"></span>
            </>
          ) : (
            'Send to Kafka'
          )}
        </button>
        
        {message && (
          <div className={`message ${messageType}`}>
            {message}
          </div>
        )}
      </div>
      
      <div className="data-container">
        <div className="data-header">
          <h2>Sensor Data</h2>
          <div>
            <button 
              onClick={fetchData} 
              className="refresh-button" 
              disabled={loadingFetch}
              style={{ marginRight: '10px' }}
            >
              {loadingFetch ? (
                <>
                  Loading... 
                  <span className="loading-spinner"></span>
                </>
              ) : (
                'Refresh Data'
              )}
            </button>
            
            <button 
              onClick={toggleAutoRefresh} 
              className="refresh-button"
              style={{ 
                backgroundColor: autoRefresh ? '#d9534f' : '#5bc0de'
              }}
            >
              {autoRefresh ? 'Stop Auto-refresh' : 'Auto-refresh (5s)'}
            </button>
          </div>
        </div>
        
        <div className="filter-container">
          <div className="filter-item">
            <label htmlFor="filter-sensor">Filter by Sensor ID:</label>
            <input
              id="filter-sensor"
              type="number"
              name="sensor_id"
              className="form-control"
              placeholder="Any sensor"
              value={filters.sensor_id}
              onChange={handleFilterChange}
            />
          </div>
          
          <div className="filter-item">
            <label htmlFor="filter-min-temp">Min Temperature:</label>
            <input
              id="filter-min-temp"
              type="number"
              step="0.1"
              name="min_temp"
              className="form-control"
              placeholder="No minimum"
              value={filters.min_temp}
              onChange={handleFilterChange}
            />
          </div>
          
          <div className="filter-item">
            <label htmlFor="filter-max-temp">Max Temperature:</label>
            <input
              id="filter-max-temp"
              type="number"
              step="0.1"
              name="max_temp"
              className="form-control"
              placeholder="No maximum"
              value={filters.max_temp}
              onChange={handleFilterChange}
            />
          </div>
          
          <div className="filter-item">
            <label htmlFor="filter-limit">Limit Results:</label>
            <input
              id="filter-limit"
              type="number"
              name="limit"
              className="form-control"
              min="1"
              max="100"
              value={filters.limit}
              onChange={handleFilterChange}
            />
          </div>
        </div>
        
        <button 
          onClick={fetchData} 
          className="button"
          style={{ marginBottom: '20px' }}
        >
          Apply Filters
        </button>
        
        {receivedData.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Sensor ID</th>
                <th>Temperature (°C)</th>
                <th>Humidity (%)</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {receivedData.map((item, index) => (
                <tr key={index}>
                  <td>{item.sensor_id}</td>
                  <td>{item.temperature.toFixed(2)}</td>
                  <td>{item.humidity.toFixed(2)}</td>
                  <td>
                    {item.timestamp}
                    <div className="timestamp-display">
                      {formatTimestamp(item.timestamp)}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="no-data">
            No data available. Try adjusting your filters or adding some sensor data.
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
