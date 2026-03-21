/**
 * CrawlKit API client
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const {
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
  CrawlKitError,
} = require('./errors');

// Use native fetch (Node 18+) or node-fetch fallback
const fetch = globalThis.fetch || require('node-fetch');

/**
 * Sleep utility for retries
 * @param {number} ms - Milliseconds to sleep
 */
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const CREDENTIALS_FILE = path.join(os.homedir(), '.crawlkit', 'credentials.json');

/**
 * CrawlKit API client
 */
class CrawlKit {
  /**
   * Create a CrawlKit client
   * @param {Object} options - Configuration options
   * @param {string} [options.apiKey] - Your CrawlKit API key (optional - will auto-load from ~/.crawlkit/credentials.json)
   * @param {string} [options.baseUrl='https://api.crawlkit.org'] - API base URL
   * @param {number} [options.timeout=30000] - Request timeout in milliseconds
   * @param {number} [options.maxRetries=3] - Maximum number of retries
   */
  constructor({ apiKey, baseUrl = 'https://api.crawlkit.org', timeout = 30000, maxRetries = 3 } = {}) {
    this.apiKey = apiKey || this._loadCredentials();
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.timeout = timeout;
    this.maxRetries = maxRetries;
  }

  /**
   * Load saved credentials from ~/.crawlkit/credentials.json
   * @private
   */
  _loadCredentials() {
    try {
      if (fs.existsSync(CREDENTIALS_FILE)) {
        const data = fs.readFileSync(CREDENTIALS_FILE, 'utf8');
        const creds = JSON.parse(data);
        return creds.api_key || creds.apiKey;
      }
    } catch (err) {
      // Ignore errors
    }
    return null;
  }

  /**
   * Save credentials to ~/.crawlkit/credentials.json
   * @private
   */
  _saveCredentials(apiKey, userInfo = null) {
    const dir = path.dirname(CREDENTIALS_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
    }
    fs.writeFileSync(
      CREDENTIALS_FILE,
      JSON.stringify({ api_key: apiKey, user: userInfo }, null, 2),
      { encoding: 'utf8', mode: 0o600 }  // rw-------
    );
  }

  /**
   * OAuth Device Flow login — opens browser for authentication
   * @param {Object} options - Login options
   * @param {boolean} [options.openBrowser=true] - Whether to automatically open browser
   * @returns {Promise<boolean>} True if login succeeded
   */
  async login({ openBrowser = true } = {}) {
    try {
      // Step 1: Start device flow
      const startResp = await fetch(`${this.baseUrl}/v1/auth/device/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_name: 'CrawlKit JavaScript SDK' }),
      });

      if (!startResp.ok) {
        throw new Error('Failed to start device flow');
      }

      const data = await startResp.json();
      const { device_code, user_code, verification_url, interval = 5, expires_in = 600 } = data;

      console.log('\n🔐 CrawlKit Login');
      console.log('Open this URL in your browser:\n');
      console.log(`  ${verification_url}\n`);
      console.log(`Your code: ${user_code}\n`);

      if (openBrowser && typeof require !== 'undefined') {
        try {
          const open = require('open');
          await open(verification_url);
        } catch (err) {
          // open module not available, user can open manually
        }
      }

      // Step 2: Poll for approval
      process.stdout.write('Waiting for authorization...');
      const startTime = Date.now();

      while (Date.now() - startTime < expires_in * 1000) {
        await sleep(interval * 1000);
        process.stdout.write('.');

        try {
          const pollResp = await fetch(`${this.baseUrl}/v1/auth/device/poll`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_code }),
          });

          if (pollResp.status === 410) {
            console.log('\n❌ Code expired. Try again.');
            return false;
          }

          if (pollResp.status === 429) {
            // Rate limited, wait longer
            await sleep(2000);
            continue;
          }

          const pollData = await pollResp.json();

          if (pollData.status === 'approved') {
            const apiKey = pollData.api_key;
            const userInfo = pollData.user;

            this.apiKey = apiKey;
            this._saveCredentials(apiKey, userInfo);

            console.log(`\n✅ Logged in as ${userInfo?.email || 'unknown'}!`);
            console.log(`Credentials saved to ${CREDENTIALS_FILE}`);
            return true;
          }
        } catch (err) {
          console.log(`\n❌ Poll error: ${err.message}`);
          return false;
        }
      }

      console.log('\n❌ Timed out. Try again.');
      return false;
    } catch (err) {
      console.log(`\n❌ Login failed: ${err.message}`);
      return false;
    }
  }

  /**
   * Remove saved credentials
   */
  logout() {
    try {
      if (fs.existsSync(CREDENTIALS_FILE)) {
        fs.unlinkSync(CREDENTIALS_FILE);
        this.apiKey = null;
        console.log('✅ Logged out. Credentials removed.');
      } else {
        console.log('ℹ️  No saved credentials found.');
      }
    } catch (err) {
      console.log(`❌ Logout failed: ${err.message}`);
    }
  }

  /**
   * Make an HTTP request with error handling and retries
   * @private
   */
  async _request(method, endpoint, { params = {}, body = null } = {}) {
    if (!this.apiKey) {
      throw new AuthenticationError(
        'No API key configured. Run `ck.login()` or pass apiKey to constructor'
      );
    }

    const url = new URL(endpoint, this.baseUrl);

    // Add query parameters
    if (params && Object.keys(params).length > 0) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    let retries = 0;

    while (retries <= this.maxRetries) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        const options = {
          method,
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json',
          },
          signal: controller.signal,
        };

        if (body) {
          options.body = JSON.stringify(body);
        }

        const response = await fetch(url.toString(), options);
        clearTimeout(timeoutId);

        // Handle different status codes
        if (response.status === 401) {
          throw new AuthenticationError('Invalid API key');
        } else if (response.status === 404) {
          throw new NotFoundError(`Resource not found: ${endpoint}`);
        } else if (response.status === 422) {
          const data = await response.json();
          throw new ValidationError(data.detail || 'Validation error');
        } else if (response.status === 429) {
          const retryAfter = parseInt(response.headers.get('Retry-After') || '60', 10);
          if (retries < this.maxRetries) {
            await sleep(Math.min(retryAfter * 1000, 2 ** retries * 1000));
            retries++;
            continue;
          }
          throw new RateLimitError('Rate limit exceeded', retryAfter);
        } else if (response.status >= 500) {
          if (retries < this.maxRetries) {
            await sleep(2 ** retries * 1000);
            retries++;
            continue;
          }
          throw new ServerError(`Server error: ${response.status}`);
        }

        if (!response.ok) {
          throw new CrawlKitError(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        if (error.name === 'AbortError') {
          if (retries < this.maxRetries) {
            retries++;
            await sleep(2 ** retries * 1000);
            continue;
          }
          throw new CrawlKitError('Request timeout');
        }

        // Re-throw custom errors
        if (error instanceof CrawlKitError) {
          throw error;
        }

        // Wrap unknown errors
        throw new CrawlKitError(`Request failed: ${error.message}`);
      }
    }

    throw new CrawlKitError('Max retries exceeded');
  }

  /**
   * Scrape a URL and return structured content
   * @param {string} url - URL to scrape
   * @param {Object} [options] - Scrape options
   * @param {boolean} [options.chunk=false] - Whether to split content into chunks
   * @param {number} [options.chunkSize=1000] - Size of each chunk
   * @param {string} [options.parser] - Specific parser to use
   * @returns {Promise<Object>} Scrape result with content, title, and metadata
   */
  async scrape(url, { chunk = false, chunkSize = 1000, parser = null } = {}) {
    const params = { url };
    if (chunk) {
      params.chunk = 'true';
      params.chunk_size = chunkSize;
    }
    if (parser) {
      params.parser = parser;
    }

    return await this._request('GET', '/scrape', { params });
  }

  /**
   * Scrape multiple URLs in one request
   * @param {string[]} urls - List of URLs to scrape
   * @param {Object} [options] - Scrape options
   * @param {boolean} [options.chunk=false] - Whether to split content into chunks
   * @param {number} [options.chunkSize=1000] - Size of each chunk
   * @returns {Promise<Object[]>} Array of scrape results
   */
  async batch(urls, { chunk = false, chunkSize = 1000 } = {}) {
    const body = { urls };
    if (chunk) {
      body.chunk = true;
      body.chunk_size = chunkSize;
    }

    const data = await this._request('POST', '/batch', { body });
    return data.results || [];
  }

  /**
   * Discover links from a page
   * @param {string} url - URL to discover links from
   * @param {Object} [options] - Discovery options
   * @param {number} [options.limit=20] - Maximum number of links to return
   * @returns {Promise<string[]>} Array of discovered URLs
   */
  async discover(url, { limit = 20 } = {}) {
    const params = { url, limit };
    const data = await this._request('GET', '/discover', { params });
    return data.links || [];
  }

  /**
   * Check API health status
   * @returns {Promise<Object>} Health status information
   */
  async health() {
    return await this._request('GET', '/health');
  }

  /**
   * List available parsers
   * @returns {Promise<Object[]>} Array of available parsers
   */
  async parsers() {
    const data = await this._request('GET', '/parsers');
    return data.parsers || [];
  }

  /**
   * Get your API usage statistics
   * @returns {Promise<Object>} Usage statistics
   */
  async usage() {
    return await this._request('GET', '/usage');
  }
}

module.exports = { CrawlKit };
