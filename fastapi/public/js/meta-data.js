/**
 * TheSevenTactics — Meta Data Manager
 * API 1002로 서버 메타데이터를 로드하고 룩업 함수를 제공한다.
 */
import { apiCall } from './api.js';

let _loaded = false;
let _configs = {};

/**
 * 서버에서 메타데이터를 로드한다. 앱 초기화 시 1회 호출.
 */
export async function loadMetaData() {
    if (_loaded) return true;

    const result = await apiCall(1002, {});
    if (!result?.success) {
        console.error('[MetaData] 메타데이터 로드 실패');
        return false;
    }

    _configs = result.data;
    _loaded = true;
    console.log('[MetaData] 메타데이터 로드 완료');
    return true;
}

/** 로드 여부 확인 */
export function isMetaLoaded() {
    return _loaded;
}

/** 전체 config 접근 */
export function getConfigs() {
    return _configs;
}
