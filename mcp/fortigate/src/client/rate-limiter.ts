/**
 * Rate Limiter and Circuit Breaker for FortiOS API calls
 */

export interface RateLimiterConfig {
  maxRequestsPerSecond: number;
  circuitBreakerThreshold: number;
  circuitBreakerTimeoutMs: number;
}

export class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRate: number;

  // Circuit breaker state
  private failures = 0;
  private circuitState: "closed" | "open" | "half-open" = "closed";
  private circuitOpenedAt = 0;
  private readonly circuitThreshold: number;
  private readonly circuitTimeout: number;

  constructor(config: RateLimiterConfig) {
    this.maxTokens = config.maxRequestsPerSecond;
    this.tokens = this.maxTokens;
    this.refillRate = config.maxRequestsPerSecond;
    this.lastRefill = Date.now();
    this.circuitThreshold = config.circuitBreakerThreshold;
    this.circuitTimeout = config.circuitBreakerTimeoutMs;
  }

  /**
   * Acquire a token. Returns ms to wait, or 0 if allowed immediately.
   */
  acquire(): number {
    this.refill();

    if (this.tokens >= 1) {
      this.tokens -= 1;
      return 0;
    }

    const waitMs = Math.ceil((1 - this.tokens) * (1000 / this.refillRate));
    return waitMs;
  }

  /**
   * Check if request is allowed by circuit breaker
   */
  isCircuitClosed(): boolean {
    if (this.circuitState === "closed") return true;

    if (this.circuitState === "open") {
      if (Date.now() - this.circuitOpenedAt >= this.circuitTimeout) {
        this.circuitState = "half-open";
        return true;
      }
      return false;
    }

    // half-open: allow one request
    return true;
  }

  /**
   * Report success — reset circuit breaker
   */
  reportSuccess(): void {
    this.failures = 0;
    if (this.circuitState === "half-open") {
      this.circuitState = "closed";
    }
  }

  /**
   * Report failure — increment circuit breaker
   */
  reportFailure(): void {
    this.failures += 1;
    if (this.failures >= this.circuitThreshold) {
      this.circuitState = "open";
      this.circuitOpenedAt = Date.now();
    }
  }

  getCircuitStatus(): { state: string; failures: number } {
    return { state: this.circuitState, failures: this.failures };
  }

  private refill(): void {
    const now = Date.now();
    const elapsedMs = now - this.lastRefill;
    const tokensToAdd = (elapsedMs / 1000) * this.refillRate;
    this.tokens = Math.min(this.maxTokens, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }
}

export const defaultRateLimiter = new RateLimiter({
  maxRequestsPerSecond: parseInt(process.env.FORTIOS_RATE_LIMIT || "10", 10),
  circuitBreakerThreshold: 5,
  circuitBreakerTimeoutMs: 30000,
});
