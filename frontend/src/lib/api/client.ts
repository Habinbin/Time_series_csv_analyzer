import createClient from 'openapi-fetch';
import type { paths } from './schema';

// 배포 환경: FastAPI가 같은 origin에서 서빙 → 상대경로 사용
// 로컬 개발: VITE_API_BASE_URL=http://localhost:8000 (.env.local에 설정)
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '';

export const api = createClient<paths>({
  baseUrl,
});

