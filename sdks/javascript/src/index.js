/**
 * CrawlKit JavaScript SDK - Web + Video Intelligence API for AI
 */

const { CrawlKit } = require('./client');
const {
  CrawlKitError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
} = require('./errors');

module.exports = {
  CrawlKit,
  CrawlKitError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
};

// ESM support
module.exports.default = CrawlKit;
