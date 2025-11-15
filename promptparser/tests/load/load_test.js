import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.4/index.js';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8080';
const PROMPT_ENDPOINT = `${BASE_URL}/v1/parse`;

const cacheHits = new Counter('cache_hits');
const cacheMisses = new Counter('cache_misses');

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '4m', target: 10 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<8000'],
    http_req_failed: ['rate<0.02'],
  },
};

export default function loadTest() {
  const payload = JSON.stringify({
    prompt: {
      text: 'Create a 20 second TikTok ad for a sparkling water launch. Vibrant, high energy visuals.',
    },
    options: {
      include_cost_estimate: true,
    },
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      Connection: 'close',
    },
  };

  const response = http.post(PROMPT_ENDPOINT, payload, params);

  const ok = check(response, {
    'status is 200': (r) => r.status === 200,
    'has creative_direction': (r) => !!r.json('creative_direction'),
    'has scenes': (r) => (r.json('scenes') || []).length > 0,
  });

  if (ok) {
    if (response.json('metadata.cache_hit')) {
      cacheHits.add(1);
    } else {
      cacheMisses.add(1);
    }
  } else {
    cacheMisses.add(1);
  }

  sleep(5);
}

export function handleSummary(data) {
  const hits = data.metrics.cache_hits ? data.metrics.cache_hits.values.count : 0;
  const misses = data.metrics.cache_misses ? data.metrics.cache_misses.values.count : 0;
  const ratio = hits + misses === 0 ? 0 : hits / (hits + misses);
  return {
    stdout:
      textSummary(data, { indent: ' ', enableColors: true }) +
      `\nCache hit ratio: ${(ratio * 100).toFixed(2)}%\n`,
  };
}

