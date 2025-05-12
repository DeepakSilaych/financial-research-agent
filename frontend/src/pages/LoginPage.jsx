import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Sparkles } from "lucide-react";
import { authApi } from "../services/api";
import { useApi } from "../hooks/useApi";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  // Check if the user has just registered successfully
  const [registrationSuccess, setRegistrationSuccess] = useState(
    location.state?.registrationSuccess || false
  );
  const registeredUsername = location.state?.username || "";

  // Clear the location state after reading the registration success flag
  useEffect(() => {
    if (location.state?.registrationSuccess) {
      // Clear the state after showing the message
      window.history.replaceState({}, document.title);

      // Pre-populate the email field if available
      if (registeredUsername && registeredUsername.includes("@")) {
        setFormData(prev => ({ ...prev, email: registeredUsername }));
      }

      // Auto-hide the success message after 5 seconds
      const timer = setTimeout(() => {
        setRegistrationSuccess(false);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [location.state, registeredUsername]);

  const { loading, error, execute: login } = useApi(authApi.login);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const result = await login(formData);
    if (result) {
      navigate("/");
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-600 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg">
        <div className="mb-6 flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
        </div>

        <h1 className="mb-2 text-center text-2xl font-bold">Welcome Back</h1>
        <p className="mb-6 text-center text-muted-foreground">
          Log in to access your AI financial research assistant
        </p>

        {registrationSuccess && (
          <div className="mb-4 rounded-md bg-green-50 p-3 text-sm text-green-600 border border-green-200">
            <div className="flex items-center">
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>
                Account created successfully! Please log in with your credentials.
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={formData.email}
              onChange={handleChange}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Enter your email"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Enter your password"
              disabled={loading}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember"
                name="remember"
                type="checkbox"
                className="h-4 w-4 rounded border-input accent-primary"
              />
              <label htmlFor="remember" className="ml-2 block text-sm text-muted-foreground">
                Remember me
              </label>
            </div>
            <a href="#" className="text-sm text-primary hover:underline">
              Forgot password?
            </a>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Logging in...
              </>
            ) : (
              "Log in"
            )}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          Don't have an account?{" "}
          <a
            href="/signup"
            className="font-medium text-primary hover:underline"
            onClick={(e) => {
              e.preventDefault();
              navigate("/signup");
            }}
          >
            Sign up
          </a>
        </div>
      </div>
    </div>
  );
} 