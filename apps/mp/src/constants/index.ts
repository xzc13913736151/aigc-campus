export const APP_NAME = 'CampusClaw'

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000/api/v1'
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

// VITE_API_BASE_URL is supplied per environment when the mini-program/App is built.
// The fallback keeps local H5 development working without depending on a changing LAN IP.
export const BASE_URL = (configuredApiBaseUrl || DEFAULT_API_BASE_URL).replace(/\/+$/, '')
export const ENABLE_PASSWORD_LOGIN = true
export const ACCESS_TOKEN_KEY = 'pairup.access-token'
export const REFRESH_TOKEN_KEY = 'pairup.refresh-token'
export const CURRENT_USER_KEY = 'pairup.current-user'
export const LOGIN_REDIRECT_KEY = 'pairup.login-redirect'
export const PROFILE_ONBOARDED_KEY = 'pairup.profile-onboarded'
