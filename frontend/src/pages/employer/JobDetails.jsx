import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getJob,
  deleteJob,
} from "../../api/jobsApi";
import Loading from "../../components/Loading";
import { getApiErrorMessage } from "../../utils/apiError";

function JobDetails() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const loadJob = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getJob(jobId);

        setJob(data);
      } catch (error) {
        console.error("Failed to load job:", error);

        setError(getApiErrorMessage(error));
      } finally {
        setLoading(false);
      }
    };

    loadJob();
  }, [jobId]);

  const handleDelete = async () => {
    if (!job) {
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to delete "${job.title}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);
      setError("");

      await deleteJob(jobId);

      navigate("/employer/jobs");
    } catch (error) {
      console.error("Failed to delete job:", error);

      setError(getApiErrorMessage(error));
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <Loading message="Loading job details..." />
    );
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <h1>Job Details</h1>
        </div>

        <div className="form-error">
          {error}
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            navigate("/employer/jobs")
          }
        >
          Back to Jobs
        </button>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <h1>Job Details</h1>
        </div>

        <div className="empty-state">
          <p>Job details are not available.</p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            navigate("/employer/jobs")
          }
        >
          Back to Jobs
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1>{job.title}</h1>

        <p>View job posting details.</p>
      </div>

      <section className="dashboard-section">
        <div className="dashboard-card">
          <h2>Job Information</h2>

          <p>
            <strong>Description:</strong>{" "}
            {job.description}
          </p>

          <p>
            <strong>Salary:</strong>{" "}
            ₹{job.salary}
          </p>

          <p>
            <strong>Location:</strong>{" "}
            {job.location}
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
            {job.skills?.join(", ") ||
              "Not provided"}
          </p>

          <p>
            <strong>Posted:</strong>{" "}
            {job.posted_at
              ? new Date(
                  job.posted_at
                ).toLocaleDateString()
              : "Not available"}
          </p>
        </div>
      </section>

      <div className="form-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            navigate("/employer/jobs")
          }
          disabled={deleting}
        >
          Back to Jobs
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={() =>
            navigate(
              `/employer/jobs/${job.id}/edit`
            )
          }
          disabled={deleting}
        >
          Edit Job
        </button>

        <button
          type="button"
          className="secondary-button"
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting
            ? "Deleting..."
            : "Delete Job"}
        </button>
      </div>
    </div>
  );
}

export default JobDetails;