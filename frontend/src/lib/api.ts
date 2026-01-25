/**
 * Centralized API Client for Money Lens
 * 
 * All API calls should go through this module to ensure:
 * - Consistent base URL handling
 * - HTTPS enforcement warnings
 * - Centralized error handling
 * - Type-safe request methods
 */

// Validate environment variable at module load
const API_BASE_RAW = import.meta.env.VITE_API_BASE;

if (!API_BASE_RAW) {
  throw new Error(
    "VITE_API_BASE must be set to your backend URL. " +
    "Example: VITE_API_BASE=https://your-huggingface-space.hf.space"
  );
}

// Warn if not using HTTPS (will cause mixed content errors in production)
if (!API_BASE_RAW.startsWith("https://") && !API_BASE_RAW.includes("localhost")) {
  console.warn(
    "[API Client] Backend URL is not HTTPS. " +
    "This may cause mixed content errors in production. " +
    `Current URL: ${API_BASE_RAW}`
  );
}

// Ensure no trailing slash for consistent URL building
const API_BASE = API_BASE_RAW.replace(/\/$/, "");

/**
 * Legacy helper for building API URLs
 * @deprecated Use apiClient.get() or apiClient.post() instead
 */
export const api = (path: string): string => `${API_BASE}/api/v1${path}`;

/**
 * API response type for error handling
 */
interface ApiError {
  detail?: string;
  message?: string;
}

/**
 * Centralized API client with GET, POST methods
 */
export const apiClient = {
  /**
   * Base URL for API requests
   */
  baseUrl: `${API_BASE}/api/v1`,

  /**
   * Perform a GET request
   */
  async get<T = unknown>(path: string): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `Request failed: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Perform a POST request with JSON body
   */
  async post<T = unknown, B = unknown>(path: string, body?: B): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `Request failed: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Perform a POST request with FormData (for file uploads)
   */
  async postForm<T = unknown>(path: string, formData: FormData): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const response = await fetch(url, {
      method: "POST",
      // Don't set Content-Type header - browser will set it with boundary for FormData
      body: formData,
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `Request failed: ${response.status}`);
    }

    return response.json();
  },
};

// Export the base URL for components that need direct access
export { API_BASE };
