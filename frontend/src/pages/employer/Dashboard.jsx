import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getEmployerDashboard } from "../../api/employerDashboardApi";

function Dashboard() {
  const { user } = useAuth();

  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setError("");

        const data = await getEmployerDashboard();

        setDashboard(data);
      } catch (error) {
        console.error(
          "Failed to load employer dashboard:",
          error
        );

        setError(
          error.response?.data?.detail ||
          "Failed to load dashboard."
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return <p>Loading dashboard...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1>Employer Dashboard</h1>
        <p>Welcome back, {user?.username}.</p>
      </div>

      {/* Companies */}
      <section className="dashboard-section">
        <h2>Your Companies</h2>

        {dashboard?.companies?.length > 0 ? (
          <div className="dashboard-grid">
            {dashboard.companies.map((company) => (
              <div
                className="dashboard-card"
                key={company.id}
              >
                <h3>{company.name}</h3>
                <p>{company.location}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No companies found.</p>
          </div>
        )}
      </section>

      {/* Overview */}
      <section className="dashboard-section">
        <h2>Overview</h2>

        <div className="dashboard-grid">
          <div className="dashboard-card">
            <h3>Total Jobs</h3>
            <p className="dashboard-number">
              {dashboard?.total_jobs ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Total Applications</h3>
            <p className="dashboard-number">
              {dashboard?.applications?.total ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Shortlisted</h3>
            <p className="dashboard-number">
              {dashboard?.applications?.shortlisted ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Selected</h3>
            <p className="dashboard-number">
              {dashboard?.applications?.selected ?? 0}
            </p>
          </div>
        </div>
      </section>

      {/* Application Status */}
      <section className="dashboard-section">
        <h2>Application Status</h2>

        <div className="dashboard-grid">
          <div className="dashboard-card">
            <h3>Applied</h3>
            <p className="dashboard-number">
              {dashboard?.applications?.applied ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Shortlisted</h3>
            <p className="dashboard-number">
              {dashboard?.applications?.shortlisted ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Rejected</h3>
            <p className="dashboard-number">
              {dashboard?.applications?.rejected ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Selected</h3>
            <p className="dashboard-number">
              {dashboard?.applications?.selected ?? 0}
            </p>
          </div>
        </div>
      </section>

      {/* Recent Applications */}
      <section className="dashboard-section">
        <h2>Recent Applications</h2>

        {dashboard?.recent_applications?.length > 0 ? (
          <div className="recent-applications">
            {dashboard.recent_applications.map(
              (application) => (
                <div
                  className="dashboard-card"
                  key={application.application_id}
                >
                  <h3>{application.job_title}</h3>

                  <p>
                    Candidate:{" "}
                    {application.candidate_name}
                  </p>

                  <p>
                    Status: {application.status}
                  </p>

                  <p>
                    Applied:{" "}
                    {new Date(
                      application.applied_at
                    ).toLocaleDateString()}
                  </p>
                </div>
              )
            )}
          </div>
        ) : (
          <div className="empty-state">
            <p>No recent applications.</p>
          </div>
        )}
      </section>
    </div>
  );
}

export default Dashboard;