/**
 * FortiOS-specific error types
 */

export class FortiOSError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode?: number
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class FortiOSAuthError extends FortiOSError {
  constructor(message: string = "Authentication failed") {
    super(message, "AUTH_ERROR", 401);
  }
}

export class FortiOSConnectionError extends FortiOSError {
  constructor(message: string = "Connection failed") {
    super(message, "CONNECTION_ERROR");
  }
}

export class FortiOSApiError extends FortiOSError {
  constructor(
    message: string,
    public readonly fortiosCode?: number,
    statusCode: number = 400
  ) {
    super(message, "API_ERROR", statusCode);
  }
}

export class FortiOSTimeoutError extends FortiOSConnectionError {
  constructor(message: string = "Request timed out") {
    super(message);
    Object.defineProperty(this, 'code', { value: "TIMEOUT_ERROR", writable: true });
  }
}
