import React from 'react';
import { Routes, Route, Navigate, useParams } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Opportunities from './pages/Opportunities';
import FollowUps from './pages/FollowUps';
import ImportExport from './pages/ImportExport';
import { useAuthStore } from './store';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
};

const CustomersWrapper: React.FC = () => {
  const { customerId } = useParams<{ customerId?: string }>();
  return <Customers customerId={customerId} />;
};

const App: React.FC = () => {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout>
              <Navigate to="/dashboard" replace />
            </Layout>
          </PrivateRoute>
        }
      />
      
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </PrivateRoute>
        }
      />
      
      <Route
        path="/customers"
        element={
          <PrivateRoute>
            <Layout>
              <Customers />
            </Layout>
          </PrivateRoute>
        }
      />
      
      <Route
        path="/customers/:customerId"
        element={
          <PrivateRoute>
            <Layout>
              <CustomersWrapper />
            </Layout>
          </PrivateRoute>
        }
      />
      
      <Route
        path="/opportunities"
        element={
          <PrivateRoute>
            <Layout>
              <Opportunities />
            </Layout>
          </PrivateRoute>
        }
      />
      
      <Route
        path="/follow-ups"
        element={
          <PrivateRoute>
            <Layout>
              <FollowUps />
            </Layout>
          </PrivateRoute>
        }
      />
      
      <Route
        path="/import-export"
        element={
          <PrivateRoute>
            <Layout>
              <ImportExport />
            </Layout>
          </PrivateRoute>
        }
      />
      
      <Route
        path="*"
        element={
          <PrivateRoute>
            <Layout>
              <Navigate to="/dashboard" replace />
            </Layout>
          </PrivateRoute>
        }
      />
    </Routes>
  );
};

export default App;
