/**
 * SeferFlow API Error Types
 */

export class APIError extends Error {
  readonly name = 'APIError';
  readonly statusCode: number;
  readonly status: 'success' | 'error';

  constructor(message: string, statusCode: number, status?: 'success' | 'error') {
    super(message);
    this.statusCode = statusCode;
    this.status = status || 'error';
  }
}

export class AuthError extends APIError {
  constructor(message: string = 'Authentication error') {
    super(message, 401 as any);
  }
}

export class PermissionError extends APIError {
  constructor(message: string = 'Permission denied') {
    super(message, 403 as any);
  }
}

export class RateLimitError extends APIError {
  constructor(message: string = 'Rate limit exceeded') {
    super(message, 429 as any);
  }
}
