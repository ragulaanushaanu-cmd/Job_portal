import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Loading from "../../components/Loading";
import { getJobs } from "../../api/candidateJobsApi";
import { getApiErrorMessage } from "../../utils/apiError";

function Jobs() {
  const navigate = useNavigate();

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(0);
  const [totalJobs, setTotalJobs] = useState(0);

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getJobs({
        page,
        page_size: pageSize,
      });

      const jobItems = Array.isArray(data)
        ? data
        : data?.items || [];

      setJobs(jobItems);

      if (Array.isArray(data)) {
        setTotalPages(jobItems.length > 0 ? 1 : 0);
        setTotalJobs(jobItems.length);
      } else {
        setTotalPages(data?.total_pages || 0);
        setTotalJobs(data?.total || 0);
      }
    } catch (error) {
      console.error("Failed to load jobs:", error);
      setError(getApiErrorMessage(error));
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const handlePreviousPage = () => {
    if (page > 1) {
      setPage((currentPage) => currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (page < totalPages) {
      setPage((currentPage) => currentPage + 1);
    }
  };

  if (loading) {
    return <Loading message="Loading available jobs..." />;
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <div>
            <h1>Jobs</h1>
            <p>Find opportunities that match your skills and experience.</p>
          </div>
        </div>

        <div className="form-error" role="alert">
          {error}
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadJobs}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1>Jobs</h1>
          <p>Find opportunities that match your skills and experience.</p>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="empty-state">
          <h2>No jobs found</h2>
          <p>
            There are no job opportunities available right now.
            Please check again later.
          </p>
        </div>
      ) : (
        <>
          <div className="recent-applications">
            {jobs.map((job) => (
              <div className="dashboard-card" key={job.id}>
                <h2>{job.title}</h2>

                <p>
                  <strong>Location:</strong>{" "}
                  {job.location || "Not specified"}
                </p>

                <p>
                  <strong>Salary:</strong>{" "}
                  {job.salary != null
                    ? `₹${job.salary}`
                    : "Not specified"}
                </p>

                <p>
                  <strong>Employment:</strong>{" "}
                  {job.employment_type || "Not specified"}
                </p>

                <p>
                  <strong>Experience:</strong>{" "}
                  {job.experience_level || "Not specified"}
                </p>

                <p>
                  <strong>Work Mode:</strong>{" "}
                  {job.work_mode || "Not specified"}
                </p>

                <p>
                  <strong>Skills:</strong>{" "}
                  {Array.isArray(job.skills) && job.skills.length > 0
                    ? job.skills.join(", ")
                    : "Not specified"}
                </p>

                <div className="form-actions">
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() =>
                      navigate(`/candidate/jobs/${job.id}`)
                    }
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div
              className="pagination"
              aria-label="Job pagination"
            >
              <button
                type="button"
                className="secondary-button"
                onClick={handlePreviousPage}
                disabled={page === 1}
              >
                Previous
              </button>

              <span
                className="pagination-info"
                aria-live="polite"
              >
                Page {page} of {totalPages}
                {totalJobs > 0
                  ? ` · ${totalJobs} jobs`
                  : ""}
              </span>

              <button
                type="button"
                className="secondary-button"
                onClick={handleNextPage}
                disabled={page === totalPages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Jobs;