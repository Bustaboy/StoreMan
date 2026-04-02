const API_BASE_URL = 'http://localhost:8000';

export type HealthResponse = {
  status?: string;
  detail?: string;
};

export type HealthCheckResult = {
  ok: boolean;
  statusCode?: number;
  data?: HealthResponse;
  error?: string;
};

export async function healthCheck(): Promise<HealthCheckResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      return {
        ok: false,
        statusCode: response.status,
        error: `Health check failed: ${response.status}`
      };
    }

    const data = (await response.json()) as HealthResponse;

    return {
      ok: true,
      statusCode: response.status,
      data
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : 'Unable to connect to backend at http://localhost:8000'
    };
  }
}
