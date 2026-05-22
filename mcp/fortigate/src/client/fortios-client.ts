import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  isAxiosError,
} from "axios";
import https from "https";
import {
  FortiOSAuthError,
  FortiOSConnectionError,
  FortiOSApiError,
  FortiOSTimeoutError,
} from "./errors.js";

export interface FortiOSClientConfig {
  host: string;
  apiToken: string;
  timeoutMs?: number;
  maxRetries?: number;
  verifySsl?: boolean;
}

export interface RequestOptions {
  params?: Record<string, unknown>;
  data?: unknown;
}

/**
 * HTTP client for FortiOS CMDB API
 * Handles auth, retries, and FortiOS-specific errors
 */
export class FortiOSClient {
  private readonly client: AxiosInstance;
  private readonly config: Required<FortiOSClientConfig>;

  constructor(config: FortiOSClientConfig) {
    this.config = {
      timeoutMs: 30000,
      maxRetries: 3,
      verifySsl: true,
      ...config,
    };

    const baseURL = this.config.host.endsWith("/")
      ? this.config.host.slice(0, -1)
      : this.config.host;

    const axiosConfig: Record<string, unknown> = {
      baseURL: `${baseURL}/api/v2/cmdb`,
      timeout: this.config.timeoutMs,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    };

    if (this.config.verifySsl === false) {
      axiosConfig.httpsAgent = new https.Agent({ rejectUnauthorized: false });
    }

    this.client = axios.create(axiosConfig);

    // Request interceptor: add auth token via Authorization header
    this.client.interceptors.request.use((request) => {
      request.headers.Authorization = `Bearer ${this.config.apiToken}`;
      return request;
    });
  }

  /**
   * Perform GET request
   */
  async get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.requestWithRetry<T>("GET", path, options);
  }

  /**
   * Perform POST request
   */
  async post<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.requestWithRetry<T>("POST", path, options);
  }

  /**
   * Perform PUT request
   */
  async put<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.requestWithRetry<T>("PUT", path, options);
  }

  /**
   * Perform DELETE request
   */
  async delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.requestWithRetry<T>("DELETE", path, options);
  }

  /**
   * Perform GET request to Monitor API (api/v2/monitor)
   */
  async monitorGet<T>(path: string): Promise<T> {
    const url = `${this.config.host}/api/v2/monitor${path}`;
    const response: AxiosResponse<T> = await this.client.get(url);
    return response.data;
  }

  /**
   * Test connectivity and return basic info
   */
  async healthCheck(): Promise<{
    version: string;
    hostname: string;
    uptime: string;
  }> {
    const response = await this.monitorGet<{
      version: string;
      hostname: string;
      uptime: string;
    }>("/system/status");
    return response;
  }

  private async requestWithRetry<T>(
    method: string,
    path: string,
    options?: RequestOptions,
    attempt: number = 1
  ): Promise<T> {
    try {
      const config: AxiosRequestConfig = {
        method,
        url: path,
        params: options?.params,
        data: options?.data,
      };

      const response: AxiosResponse<T> = await this.client.request(config);
      return response.data;
    } catch (error) {
      if (isAxiosError(error)) {
        // Handle timeout
        if (error.code === "ECONNABORTED" || error.code === "ETIMEDOUT") {
          if (attempt < this.config.maxRetries) {
            const delay = Math.pow(2, attempt) * 1000;
            await this.sleep(delay);
            return this.requestWithRetry<T>(
              method,
              path,
              options,
              attempt + 1
            );
          }
          throw new FortiOSTimeoutError(
            `Request timed out after ${this.config.maxRetries} attempts`
          );
        }

        // Handle connection errors
        if (
          error.code === "ECONNREFUSED" ||
          error.code === "ENOTFOUND" ||
          error.code === "ECONNRESET"
        ) {
          if (attempt < this.config.maxRetries) {
            const delay = Math.pow(2, attempt) * 1000;
            await this.sleep(delay);
            return this.requestWithRetry<T>(
              method,
              path,
              options,
              attempt + 1
            );
          }
          throw new FortiOSConnectionError(
            `Connection failed after ${this.config.maxRetries} attempts. Check FORTIOS_HOST and connectivity.`
          );
        }

        // Handle HTTP errors
        const status = error.response?.status;
        const data = error.response?.data as
          | { error?: number; detail?: string; message?: string }
          | undefined;

        if (status === 401 || status === 403) {
          throw new FortiOSAuthError(
            data?.detail || "Invalid API token or insufficient permissions"
          );
        }

        throw new FortiOSApiError(
          data?.detail || data?.message || error.message,
          data?.error,
          status
        );
      }

      throw error;
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
