import { Link } from "react-router-dom";

function NotFound() {
  return (
    <div className="not-found-page">
      <h1>404</h1>

      <h2>Page Not Found</h2>

      <p>
        Sorry, the page you are looking for does not exist.
      </p>

      <Link to="/dashboard">
        Go to Dashboard
      </Link>
    </div>
  );
}

export default NotFound;