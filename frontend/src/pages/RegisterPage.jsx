import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Sparkles } from "lucide-react";
import { authApi } from "../services/api";
import { useApi } from "../hooks/useApi";

export function RegisterPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [passwordError, setPasswordError] = useState("");
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const { loading, error, execute: register } = useApi(authApi.register);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear password match error when editing password fields
    if (name === "password" || name === "confirmPassword") {
      setPasswordError("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Check if passwords match
    if (formData.password !== formData.confirmPassword) {
      setPasswordError("Passwords do not match");
      return;
    }

    // Prepare the registration data (omit confirmPassword)
    const registrationData = {
      username: formData.username,
      email: formData.email,
      password: formData.password,
    };

    const result = await register(registrationData);
    if (result) {
      // Show success message
      setRegistrationSuccess(true);

      // Navigate to login page after a short delay
      setTimeout(() => {
        navigate("/login", {
          state: {
            registrationSuccess: true,
            username: formData.username
          }
        });
      }, 1500);
    }
  };

  if (registrationSuccess) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-600 px-4">
        <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg text-center">
          <div className="mb-6 flex justify-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-600">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>

          <h1 className="mb-2 text-center text-2xl font-bold text-green-600">Registration Successful!</h1>
          <p className="mb-6 text-center text-muted-foreground">
            Your account has been created successfully. Redirecting you to login...
          </p>

          <div className="flex justify-center">
            <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
              <div className="h-full w-full origin-left animate-pulse rounded-full bg-green-500"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full items-center justify-center bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-600 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg">
        <div className="mb-6 flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary/10">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
        </div>

        <h1 className="mb-2 text-center text-2xl font-bold">Create Account</h1>
        <p className="mb-6 text-center text-muted-foreground">
          Sign up to access your AI financial research assistant
        </p>

        {error && (
          <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="mb-2 block text-sm font-medium">
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              value={formData.username}
              onChange={handleChange}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Enter your username"
              disabled={loading}
            />
          </div>

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
              placeholder="Create a password"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="mb-2 block text-sm font-medium">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              required
              value={formData.confirmPassword}
              onChange={handleChange}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Confirm your password"
              disabled={loading}
            />
            {passwordError && (
              <p className="mt-1 text-sm text-destructive">{passwordError}</p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Creating account...
              </>
            ) : (
              "Create Account"
            )}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          Already have an account?{" "}
          <a
            href="/login"
            className="font-medium text-primary hover:underline"
            onClick={(e) => {
              e.preventDefault();
              navigate("/login");
            }}
          >
            Log in
          </a>
        </div>
      </div>
    </div>
  );
} 