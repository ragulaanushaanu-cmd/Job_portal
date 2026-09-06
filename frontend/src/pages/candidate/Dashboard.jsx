import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getCandidateDashboard } from "../../api/dashboardApi";

function Dashboard() {
  const { user } = useAuth();

  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setError("");

        const data = await getCandidateDashboard();

        setDashboard(data);
      } catch (error) {
        console.error("Failed to load candidate dashboard:", error);

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
        <h1>Candidate Dashboard</h1>
        <p>Welcome back, {user?.username}.</p>
      </div>

      {dashboard?.profile && (
        <section className="dashboard-section">
          <h2>Profile</h2>

          <div className="dashboard-card">
            <p>
              <strong>Name:</strong>{" "}
              {dashboard.profile.name}
            </p>

            <p>
              <strong>Email:</strong>{" "}
              {user?.email}
            </p>
          </div>
        </section>
      )}

      <section className="dashboard-section">
        <h2>Overview</h2>

        <div className="dashboard-grid">

          <div className="dashboard-card">
            <h3>Resumes</h3>
            <p className="dashboard-number">
              {dashboard?.resumes?.total ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Applications</h3>
            <p className="dashboard-number">
              {dashboard?.applications?.total ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Saved Jobs</h3>
            <p className="dashboard-number">
              {dashboard?.saved_jobs?.total ?? 0}
            </p>
          </div>

          <div className="dashboard-card">
            <h3>Primary Resume</h3>
            <p>
              {dashboard?.resumes?.primary_resume_id
                ? `Resume #${dashboard.resumes.primary_resume_id}`
                : "Not selected"}
            </p>
          </div>

        </div>
      </section>

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

      <section className="dashboard-section">
        <h2>Recent Applications</h2>

        {dashboard?.recent_applications?.length > 0 ? (
          <div className="recent-applications">
            {dashboard.recent_applications.map((application) => (
              <div
                className="dashboard-card"
                key={application.application_id}
              >
                <h3>
                  {application.job_title}
                </h3>

                <p>
                  Company: {application.company_name}
                </p>

                <p>
                  Status: {application.status}
                </p>
              </div>
            ))}
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