export const APP_NAME = 'CampusClaw'

const DEFAULT_API_BASE_URL = 'http://10.159.119.45:8000/api/v1'
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

// VITE_API_BASE_URL is supplied per environment when the mini-program/App is built.
// The fallback points to the current phone hotspot for HBuilderX device runs.
export const BASE_URL = (configuredApiBaseUrl || DEFAULT_API_BASE_URL).replace(/\/+$/, '')
export const ENABLE_PASSWORD_LOGIN = true
export const ACCESS_TOKEN_KEY = 'pairup.access-token'
export const REFRESH_TOKEN_KEY = 'pairup.refresh-token'
export const CURRENT_USER_KEY = 'pairup.current-user'
export const LOGIN_REDIRECT_KEY = 'pairup.login-redirect'
export const PROFILE_ONBOARDED_KEY = 'pairup.profile-onboarded'
