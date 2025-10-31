import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import axios from "axios";

// ✅ Use OpenID Connect Scopes (the ones your app supports)

interface User {
  id: string;
  name: string;
  email: string;
  accessToken: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithLinkedIn: () => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const LINKEDIN_CLIENT_ID = import.meta.env.VITE_LINKEDIN_CLIENT_ID;
const REDIRECT_URI = import.meta.env.VITE_LINKEDIN_REDIRECT_URI;

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem("linkedin_user");
    if (storedUser) setUser(JSON.parse(storedUser));

    if (window.location.pathname === "/auth/callback") {
      handleLinkedInCallback();
    } else {
      setLoading(false);
    }
  }, []);

  const signInWithLinkedIn = () => {
    const state = crypto.randomUUID();
    localStorage.setItem("linkedin_state", state);

    const scope = "openid profile email"; // ✅ FIXED SCOPES

    const authUrl = `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=${LINKEDIN_CLIENT_ID}&redirect_uri=${encodeURIComponent(
      REDIRECT_URI
    )}&scope=${encodeURIComponent(scope)}&state=${state}&prompt=login`;

    window.location.href = authUrl;
  };

  const handleLinkedInCallback = async () => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const error = params.get("error");

    if (error) {
      alert("LinkedIn login failed: " + error);
      setLoading(false);
      return;
    }

    if (!code || !state) {
      setLoading(false);
      return;
    }

    const savedState = localStorage.getItem("linkedin_state");
    if (state !== savedState) {
      console.error("Invalid OAuth state");
      setLoading(false);
      return;
    }

    try {
      // ✅ Exchange the code for a token in your backend
      const response = await axios.post(
        `${import.meta.env.VITE_BACKEND_URL}/auth/linkedin/token`,
        { code, redirect_uri: REDIRECT_URI }
      );

      const id_token = response.data.id_token; // ✅ OpenID Connect gives ID token
      if (!id_token) throw new Error("No ID token returned");

      // ✅ Decode JWT to extract user info (simplified)
      const base64Url = id_token.split(".")[1];
      const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      const userPayload = JSON.parse(window.atob(base64));

      const userData: User = {
        id: userPayload.sub,
        name: userPayload.name,
        email: userPayload.email,
        accessToken: id_token,
      };

      setUser(userData);
      localStorage.setItem("linkedin_user", JSON.stringify(userData));
      localStorage.removeItem("linkedin_state");

      // ✅ Redirect to dashboard
      window.history.replaceState({}, document.title, "/dashboard");
    } catch (err) {
      console.error("LinkedIn login error:", err);
    } finally {
      setLoading(false);
    }
  };

  const signOut = () => {
    setUser(null);
    localStorage.removeItem("linkedin_user");
  };

  return (
    <AuthContext.Provider value={{ user, loading, signInWithLinkedIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
