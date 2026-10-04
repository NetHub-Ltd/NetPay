import { api, setIdToken, setToken, type User } from '../api/client'

/** Called from /auth/callback after token exchange. */
export async function applyAccessToken(
  accessToken: string,
  idToken?: string,
): Promise<User> {
  setToken(accessToken)
  if (idToken) setIdToken(idToken)
  return api.get<User>('/auth/me')
}
