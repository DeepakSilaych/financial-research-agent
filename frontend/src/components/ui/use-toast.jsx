import React, { createContext, useState, useContext, useCallback } from 'react';
import { X } from 'lucide-react';

// Toast context for managing toasts
const ToastContext = createContext(null);

// Toast component for displaying notifications
const Toast = ({ id, title, description, status = 'info', onClose }) => {
  // Determine toast styles based on status
  const statusStyles = {
    success: 'bg-green-100 text-green-800 border-green-300',
    error: 'bg-red-100 text-red-800 border-red-300',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    info: 'bg-blue-100 text-blue-800 border-blue-300',
  };

  // Apply appropriate styles
  const toastStyles = statusStyles[status] || statusStyles.info;

  return (
    <div
      className={`p-4 mb-3 rounded-md shadow-md border ${toastStyles} animate-in slide-in-from-right duration-300`}
      role="alert"
    >
      <div className="flex justify-between items-start">
        <div>
          {title && <h3 className="font-semibold mb-1">{title}</h3>}
          {description && <p className="text-sm">{description}</p>}
        </div>
        <button
          onClick={() => onClose(id)}
          className="ml-4 text-gray-500 hover:text-gray-700"
          aria-label="Close"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
};

// ToastProvider for wrapping application
export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  // Add a new toast
  const addToast = useCallback(({ title, description, status = 'info', duration = 5000 }) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, title, description, status }]);

    // Auto dismiss toast after duration
    if (duration) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }

    return id;
  }, []);

  // Remove a toast by id
  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}

      {/* Toast container - fixed position at top right */}
      <div className="fixed top-5 right-5 z-50 w-72">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            {...toast}
            onClose={removeToast}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

// Custom hook for using toast
export const useToast = () => {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }

  return context.addToast;
};

// Simple export for direct access
export const toast = (props) => {
  const context = useContext(ToastContext);

  if (context) {
    return context.addToast(props);
  } else {
    console.warn('Toast was called outside of ToastProvider');
  }
};

export default useToast; 