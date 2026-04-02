const API_BASE_URL = 'http://localhost:8000';

export type HealthResponse = {
  status?: string;
  detail?: string;
};

export async function healthCheck(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return (await response.json()) as HealthResponse;
}
