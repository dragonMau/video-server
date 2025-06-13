
const STORAGE_KEY = 'userApiKey';

function getApiKey() {
  return localStorage.getItem(STORAGE_KEY);
}

function setApiKey(key) {
  localStorage.setItem(STORAGE_KEY, key);
}

function promptForApiKey() {
  const key = prompt('Enter your API key:');
  if (key) {
    setApiKey(key);
  }
  return key;
}

function ensureApiKey() {
  let key = getApiKey();
  if (!key) {
    key = promptForApiKey();
  }
  return key;
}

async function fetchWithApiKey(url, options = {}) {
  const key = ensureApiKey();
  if (!key) {
    throw new Error('API key is required');
  }

  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${key}`,
  };

  const response = await fetch(url, options);

  if (response.status === 401) {
    alert('Invalid API key. Please enter a new one.');
    localStorage.removeItem(STORAGE_KEY);
    return fetchWithApiKey(url, options); // Retry
  }

  return response;
}

async function makeApiCall() {
  try {
    const response = await fetchWithApiKey('https://api.example.com/data');
    const data = await response.json();
  } catch (err) {
    console.log('Error: ' + err.message); 
  }
}
