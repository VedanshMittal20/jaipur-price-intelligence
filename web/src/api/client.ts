import {
  CounterfactualResponse,
  DealSummary,
  LocalitySummary,
  ModelMetaResponse,
  PricePredictionResponse,
  PropertyRequest,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function predictPrice(req: PropertyRequest): Promise<PricePredictionResponse> {
  const resp = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({ detail: 'Prediction request failed' }));
    throw new Error(errorData.detail || `Server returned ${resp.status}`);
  }

  return resp.json();
}

export async function fetchLocalities(): Promise<LocalitySummary[]> {
  const resp = await fetch(`${API_BASE}/localities`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch localities (${resp.status})`);
  }
  return resp.json();
}

export async function fetchDeals(limit: number = 50): Promise<DealSummary[]> {
  const resp = await fetch(`${API_BASE}/deals?limit=${limit}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch deals (${resp.status})`);
  }
  return resp.json();
}

export async function fetchModelMeta(): Promise<ModelMetaResponse> {
  const resp = await fetch(`${API_BASE}/meta/model`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch model metadata (${resp.status})`);
  }
  return resp.json();
}

export async function fetchCounterfactuals(req: PropertyRequest): Promise<CounterfactualResponse> {
  const resp = await fetch(`${API_BASE}/counterfactual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({ detail: 'Counterfactual request failed' }));
    throw new Error(errorData.detail || `Server returned ${resp.status}`);
  }

  return resp.json();
}

