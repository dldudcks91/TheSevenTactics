/**
 * TheSevenRPG — Session Manager
 * localStorage 기반 세션 관리
 */
const KEYS = {
    SESSION_ID: 'session_id',
    USER_NO: 'user_no',
    USER_NAME: 'user_name',
};

/** 로그인 성공 시 세션 저장 */
export function saveSession(sessionId, userNo, userName) {
    localStorage.setItem(KEYS.SESSION_ID, sessionId);
    localStorage.setItem(KEYS.USER_NO, String(userNo));
    localStorage.setItem(KEYS.USER_NAME, userName);
}

/** 세션 ID 조회 */
export function getSessionId() {
    return localStorage.getItem(KEYS.SESSION_ID);
}

/** 유저 번호 조회 */
export function getUserNo() {
    const val = localStorage.getItem(KEYS.USER_NO);
    return val ? parseInt(val, 10) : null;
}

/** 유저 이름 조회 */
export function getUserName() {
    return localStorage.getItem(KEYS.USER_NAME);
}

/** 로그인 상태 확인 */
export function isLoggedIn() {
    return !!getSessionId();
}

/** 세션 삭제 (로그아웃) */
export function clearSession() {
    localStorage.removeItem(KEYS.SESSION_ID);
    localStorage.removeItem(KEYS.USER_NO);
    localStorage.removeItem(KEYS.USER_NAME);
}
