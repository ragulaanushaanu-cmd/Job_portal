
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getSavedJobs,
  deleteSavedJob,
} from "../../api/candidateSavedJobsApi";
import Loading from "../../components/Loading";
import { getApiErrorMessage } from "../../utils/apiError";

function SavedJobs() {
  const navigate = useNavigate();

  const [savedJobs, setSavedJobs] = useState([]);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [deletingJobId, setDeletingJobId] = useState(null);

  const loadSavedJobs = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getSavedJobs({
        page,
        page_size: pageSize,
        order: "desc",
      });

      setSavedJobs(data?.items || []);
      setTotal(data?.total || 0);
      setTotalPages(data?.total_pages || 0);
    } catch (error) {
      console.error("Failed to load saved jobs:", error);

      setError(getApiErrorMessage(error));
      setSavedJobs([]);
      setTotal(0);
      setTotalPages(0);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadSavedJobs();
  }, [loadSavedJobs]);

  const handleRemove = async (jobId) => {
    try {
      setDeletingJobId(jobId);
      setError("");
      setSuccessMessage("");

      await deleteSavedJob(jobId);

      setSavedJobs((previousSavedJobs) =>
        previousSavedJobs.filter(
          (savedJob) => savedJob.job?.id !== jobId
        )
      );

      setTotal((currentTotal) =>
        currentTotal > 0 ? currentTotal - 1 : 0
      );

      setSuccessMessage("Job removed from saved jobs.");

      // Move back one page if the last item on the current page was removed.
      if (savedJobs.length === 1 && page > 1) {
        setPage((currentPage) => currentPage - 1);
      }
    } catch (error) {
      console.error("Failed to remove saved job:", error);

      setError(getApiErrorMessage(error));
    } finally {
      setDeletingJobId(null);
    }
  };

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
    return <Loading message="Loading saved jobs..." />;
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1>Saved Jobs</h1>
          <p>Jobs you have saved for later.</p>
        </div>
      </div>

      {error && (
        <div className="form-error" role="alert" aria-live="assertive">
          {error}
        </div>
      )}

      {successMessage && (
        <div
          className="form-success"
          role="status"
          aria-live="polite"
        >
          {successMessage}
        </div>
      )}

      <section className="dashboard-section">
        {savedJobs.length === 0 ? (
          <div className="empty-state">
            <h2>No saved jobs</h2>

            <p>
              You have not saved any jobs yet. Browse available
              jobs and save the ones you want to revisit later.
            </p>

            <button
              type="button"
              className="primary-button"
              onClick={() => navigate("/candidate/jobs")}
            >
              Browse Jobs
            </button>
          </div>
        ) : (
          <>
            <div className="dashboard-grid">
              {savedJobs.map((savedJob) => {
                const job = savedJob.job;

                if (!job) {
                  return (
                    <div
                      className="dashboard-card"
                      key={savedJob.id}
                    >
                      <h3>Saved Job</h3>

                      <p>
                        Job information is no longer available.
                      </p>

                      <div
                        className="form-actions"
                        style={{
                          display: "flex",
                          gap: "12px",
                          flexWrap: "wrap",
                          alignItems: "center",
                        }}
                      >
                        <button
                          type="button"
                          className="secondary-button"
                          disabled={deletingJobId === savedJob.id}
                          onClick={() => handleRemove(savedJob.id)}
                        >
                          {deletingJobId === savedJob.id
                            ? "Removing..."
                            : "Remove Saved Job"}
                        </button>
                      </div>
                    </div>
                  );
                }

                return (
                  <div
                    className="dashboard-card"
                    key={savedJob.id}
                  >
                    <h3>{job.title}</h3>

                    <p>
                      <strong>Company:</strong>{" "}
                      {job.company?.name || "Company not available"}
                    </p>

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
                      <strong>Skills:</strong>{" "}
                      {Array.isArray(job.skills) &&
                      job.skills.length > 0
                        ? job.skills.join(", ")
                        : "Not provided"}
                    </p>

                    <p>
                      <strong>Saved:</strong>{" "}
                      {savedJob.saved_at
                        ? new Date(
                            savedJob.saved_at
                          ).toLocaleDateString()
                        : "Not available"}
                    </p>

                    <div
                      className="form-actions"
                      style={{
                        display: "flex",
                        gap: "12px",
                        flexWrap: "wrap",
                        alignItems: "center",
                      }}
                    >
                      <button
                        type="button"
                        className="primary-button"
                        onClick={() =>
                          navigate(`/candidate/jobs/${job.id}`)
                        }
                      >
                        View Job
                      </button>

                      <button
                        type="button"
                        className="secondary-button"
                        disabled={deletingJobId === job.id}
                        onClick={() => handleRemove(job.id)}
                      >
                        {deletingJobId === job.id
                          ? "Removing..."
                          : "Remove Saved Job"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {totalPages > 1 && (
              <div
                className="form-actions"
                style={{
                  display: "flex",
                  gap: "16px",
                  flexWrap: "wrap",
                  alignItems: "center",
                }}
              >
                <button
                  type="button"
                  className="secondary-button"
                  disabled={page <= 1}
                  onClick={handlePreviousPage}
                >
                  Previous
                </button>

                <span aria-live="polite">
                  Page {page} of {totalPages}
                </span>

                <button
                  type="button"
                  className="secondary-button"
                  disabled={page >= totalPages}
                  onClick={handleNextPage}
                >
                  Next
                </button>
              </div>
            )}

            <p>
              <strong>Total saved jobs:</strong> {total}
            </p>
          </>
        )}
      </section>
    </div>
  );
}

export default SavedJobs;

