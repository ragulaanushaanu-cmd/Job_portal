import { useAuth } from "../context/AuthContext";

function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <h2>Job Portal</h2>
      </div>

      <div className="navbar-user">
        <span>{user?.username}</span>

        <button
          type="button"
          className="logout-button"
          onClick={logout}
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default Navbar;