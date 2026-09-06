import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";

function EmployerLayout() {
  return (
    <div className="app-layout">
      <Navbar />

      <div className="app-body">
        <Sidebar />

        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default EmployerLayout;