import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Sidebar() {
  const { user } = useAuth();

  const getNavClass = ({ isActive }) =>
    isActive ? "sidebar-link active" : "sidebar-link";

  return (
    <aside className="sidebar">
      <h3>Menu</h3>

      {user?.role === "Candidate" && (
        <nav className="sidebar-nav">
          <NavLink
            to="/candidate/dashboard"
            className={getNavClass}
          >
            Dashboard
          </NavLink>

          <NavLink
            to="/candidate/jobs"
            className={getNavClass}
          >
            Jobs
          </NavLink>

          <NavLink
            to="/candidate/applications"
            className={getNavClass}
          >
            Applications
          </NavLink>

          <NavLink
            to="/candidate/saved-jobs"
            className={getNavClass}
          >
            Saved Jobs
          </NavLink>

          <NavLink
            to="/candidate/resumes"
            className={getNavClass}
          >
            Resumes
          </NavLink>

          <NavLink
            to="/candidate/profile"
            className={getNavClass}
          >
            Profile
          </NavLink>
        </nav>
      )}

      {user?.role === "Employer" && (
        <nav className="sidebar-nav">
          <NavLink
            to="/employer/dashboard"
            className={getNavClass}
          >
            Dashboard
          </NavLink>

          <NavLink
            to="/employer/jobs"
            className={getNavClass}
          >
            Jobs
          </NavLink>

          <NavLink
            to="/employer/applications"
            className={getNavClass}
          >
            Applications
          </NavLink>

          <NavLink
            to="/employer/company"
            className={getNavClass}
          >
            Company
          </NavLink>
        </nav>
      )}
    </aside>
  );
}

export default Sidebar;