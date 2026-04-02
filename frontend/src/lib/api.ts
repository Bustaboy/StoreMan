const API_BASE_URL = 'http://localhost:8000';

export type ApiResult<T> = {
  ok: boolean;
  statusCode?: number;
  data?: T;
  error?: string;
};

export type HealthResponse = {
  status?: string;
  detail?: string;
};

export type Material = {
  id: number;
  code: string;
  name: string;
  category?: string | null;
  quantity_on_hand: number;
  unit?: string | null;
  location?: string | null;
  updated_at?: string | null;
};

async function getJson<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      return {
        ok: false,
        statusCode: response.status,
        error: `Request failed: ${response.status}`
      };
    }

    const data = (await response.json()) as T;

    return {
      ok: true,
      statusCode: response.status,
      data
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : `Unable to connect to backend at ${API_BASE_URL}`
    };
  }
}

export function healthCheck(): Promise<ApiResult<HealthResponse>> {
  return getJson<HealthResponse>('/health');
}

export async function fetchMaterials(query?: string): Promise<ApiResult<Material[]>> {
  const normalizedQuery = query?.trim();

  if (!normalizedQuery) {
    return getJson<Material[]>('/materials');
  }

  const encodedQuery = encodeURIComponent(normalizedQuery);

  const searchResult = await getJson<Material[]>(`/materials/search?q=${encodedQuery}`);
  if (searchResult.ok) {
    return searchResult;
  }

  return getJson<Material[]>(`/materials?q=${encodedQuery}`);
}
