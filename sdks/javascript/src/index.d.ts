/**
 * TypeScript declarations for CrawlKit SDK
 */

export interface CrawlKitOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

export interface ScrapeOptions {
  chunk?: boolean;
  chunkSize?: number;
  parser?: string;
}

export interface BatchOptions {
  chunk?: boolean;
  chunkSize?: number;
}

export interface DiscoverOptions {
  limit?: number;
}

export interface ScrapeResult {
  url: string;
  title?: string;
  content: string;
  chunks?: string[];
  metadata?: Record<string, any>;
}

export interface ParserInfo {
  name: string;
  description: string;
  supported_domains?: string[];
}

export interface UsageStats {
  requests_used: number;
  requests_limit: number;
  requests_remaining: number;
  reset_at?: string;
}

export class CrawlKitError extends Error {
  constructor(message: string);
}

export class AuthenticationError extends CrawlKitError {
  constructor(message?: string);
}

export class RateLimitError extends CrawlKitError {
  retryAfter: number | null;
  constructor(message?: string, retryAfter?: number);
}

export class NotFoundError extends CrawlKitError {
  constructor(message?: string);
}

export class ValidationError extends CrawlKitError {
  constructor(message?: string);
}

export class ServerError extends CrawlKitError {
  constructor(message?: string);
}

export class CrawlKit {
  constructor(options: CrawlKitOptions);

  scrape(url: string, options?: ScrapeOptions): Promise<ScrapeResult>;
  batch(urls: string[], options?: BatchOptions): Promise<ScrapeResult[]>;
  discover(url: string, options?: DiscoverOptions): Promise<string[]>;
  health(): Promise<Record<string, any>>;
  parsers(): Promise<ParserInfo[]>;
  usage(): Promise<UsageStats>;
}

export default CrawlKit;
