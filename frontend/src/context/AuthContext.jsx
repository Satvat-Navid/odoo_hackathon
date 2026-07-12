import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { fetchMe, getToken, login as apiLogin, setToken } from '../services/api';

const AuthContext = createContext(null);

export const ROLES = {
  ADMIN: 'Admin',
  DEPARTMENT_HEAD: 'Department Head',
  ASSET_MANAGER: 'Asset Manager',
  EMPLOYEE: 'Employee',
};

// Roles allowed to register/allocate assets & approve transfers.
export const MANAGER_ROLES = [ROLES.ADMIN, ROLES.ASSET_MANAGER, ROLES.DEPARTMENT_HEAD];

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session from a persisted token on load.
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    fetchMe()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const data = await apiLogin(email, password);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      isAdmin: user?.role === ROLES.ADMIN,
      isManager: MANAGER_ROLES.includes(user?.role),
      login,
      logout,
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
