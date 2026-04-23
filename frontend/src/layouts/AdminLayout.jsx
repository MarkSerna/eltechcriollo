import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import AdminSidebar from '../components/AdminSidebar';

const AdminLayout = ({ user, onLogout }) => {
  // Verificación de autenticación para proteger todas las subrutas admin
  if (!user.authenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen bg-white dark:bg-slate-950 transition-colors duration-300">
      {/* Barra lateral fija para navegación administrativa */}
      <AdminSidebar onLogout={onLogout} />
      
      {/* Área de contenido principal desplazada por el ancho del sidebar */}
      <main className="flex-1 ml-64 min-h-screen overflow-y-auto">
        <div className="p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;
