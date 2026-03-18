/**
 * TheSevenRPG — API Communication Layer
 * POST /api 단일 게이트웨이, Bearer 세션 인증, 재시도 로직
 */
import { getSessionId, clearSession } from './session.js';
import { showToast } from './utils.js';

const MAX_RETRIES = 3;
const BASE_DELAY = 1000;

/**
 * 서버 API 호출
 * @param {number} apiCode - API 코드 (1002, 1003, 2001, ...)
 * @param {object} data - 요청 데이터
 * @returns {Promise<object|null>} 서버 응답 또는 null (네트워크 실패)
 */
export async function apiCall(apiCode, data = {}) {
    const headers = { 'Content-Type': 'application/json' };

    const sessionId = getSessionId();
    if (sessionId) {
        headers['Authorization'] = `Bearer ${sessionId}`;
    }

    const body = JSON.stringify({
        api_code: apiCode,
        data: data
    });

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        try {
            const response = await fetch('/api', {
                method: 'POST',
                headers,
                body
            });

            const result = await response.json();

            if (!result.success) {
                handleApiError(result);
            }
            return result;

        } catch (err) {
            if (attempt < MAX_RETRIES - 1) {
                await new Promise(r => setTimeout(r, BASE_DELAY * 2 ** attempt));
            }
        }
    }

    showToast('서버에 연결할 수 없습니다. 네트워크를 확인해주세요.', 'error');
    return null;
}

/** API 에러 처리 */
function handleApiError(result) {
    const errorCode = result.error_code || '';
    const message = result.message || '알 수 없는 오류';

    // E1002: 세션 만료 → 로그인 화면으로
    if (errorCode === 'E1002') {
        clearSession();
        showToast('세션이 만료되었습니다. 다시 로그인해주세요.', 'warning');
        // 순환 의존 방지: app.js의 navigate() 대신 직접 hash 변경
        window.location.hash = '#login';
        return;
    }

    // 그 외 에러 → 토스트
    if (result.success === false) {
        showToast(message, 'error');
    }
}
