/**
 * Custom error classes for CrawlKit SDK
 */

class CrawlKitError extends Error {
  constructor(message) {
    super(message);
    this.name = 'CrawlKitError';
  }
}

class AuthenticationError extends CrawlKitError {
  constructor(message = 'Invalid API key') {
    super(message);
    this.name = 'AuthenticationError';
  }
}

class RateLimitError extends CrawlKitError {
  constructor(message = 'Rate limit exceeded', retryAfter = null) {
    super(message);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

class NotFoundError extends CrawlKitError {
  constructor(message = 'Resource not found') {
    super(message);
    this.name = 'NotFoundError';
  }
}

class ValidationError extends CrawlKitError {
  constructor(message = 'Validation error') {
    super(message);
    this.name = 'ValidationError';
  }
}

class ServerError extends CrawlKitError {
  constructor(message = 'Server error') {
    super(message);
    this.name = 'ServerError';
  }
}

module.exports = {
  CrawlKitError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
};
