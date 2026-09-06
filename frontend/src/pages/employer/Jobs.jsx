import { useEffect, useState } from "react";
import { getEmployerJobs } from "../../api/jobsApi";
import { useNavigate } from "react-router-dom";

function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const loadJobs = async () => {
      try {
        setError("");

        const data = await getEmployerJobs();

        setJobs(data);
      } catch (error) {
        console.error("Failed to load jobs:", error);

        setError(
          error.response?.data?.detail ||
          "Failed to load jobs."
        );
      } finally {
        setLoading(false);
      }
    };

    loadJobs();
  }, []);

  if (loading) {
    return <p>Loading jobs...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <div className="dashboard-page">
      <div className="page-header page-header-with-action">
        <div>
            <h1>Jobs</h1>
            <p>Manage your job postings.</p>
        </div>

        <button
            type="button"
            className="primary-button"
            onClick={() => navigate("/employer/jobs/new")}
        >
            Create Job
        </button>
        </div>

      {jobs.length > 0 ? (
        <div className="recent-applications">
          {jobs.map((job) => (
            <div className="dashboard-card" key={job.id}>
              <h3>{job.title}</h3>

              <p>
                <strong>Location:</strong>{" "}
                {job.location}
              </p>

              <p>
                <strong>Salary:</strong>{" "}
                {job.salary}
              </p>

              <p>
                <strong>Employment:</strong>{" "}
                {job.employment_type}
              </p>

              <p>
                <strong>Experience:</strong>{" "}
                {job.experience_level}
              </p>

              <p>
                <strong>Work Mode:</strong>{" "}
                {job.work_mode}
              </p>

              <p>
                <strong>Skills:</strong>{" "}
                {job.skills?.join(", ")}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <p>No jobs found.</p>
        </div>
      )}
    </div>
  );
}

export default Jobs;
