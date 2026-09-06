import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { loginUser } from "../api/authApi";
import { getCurrentUser } from "../api/userApi";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(
    localStorage.getItem("access_token")
  );

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const login = async (username, password) => {
    const data = await loginUser(username, password);

    localStorage.setItem("access_token", data.access_token);

    setToken(data.access_token);

    const currentUser = await getCurrentUser();

    setUser(currentUser);

    return currentUser;
  };

  const logout = () => {
    localStorage.removeItem("access_token");

    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    const loadCurrentUser = async () => {
      const storedToken = localStorage.getItem("access_token");

      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();

        setUser(currentUser);
        setToken(storedToken);
      } catch (error) {
        console.error("Failed to load current user:", error);

        localStorage.removeItem("access_token");

        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadCurrentUser();
  }, []);

  const isAuthenticated = Boolean(token && user);

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated,
        loading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};