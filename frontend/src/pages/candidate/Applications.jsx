import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import { getApiErrorMessage } from "../../utils/apiError";
import Loading from "../../components/Loading";

import {
  getMyApplications,
  getApplication,
  getApplicationHistory,
} from "../../api/candidateApplicationsApi";

function Applications() {
  const location = useLocation();

  const [applications, setApplications] = useState([]);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [statusFilter, setStatusFilter] = useState("");

  const [selectedApplication, setSelectedApplication] =
    useState(null);

  const [history, setHistory] = useState([]);

  const [detailsLoadingId, setDetailsLoadingId] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState(
    location.state?.successMessage || ""
  );

  useEffect(() => {
    if (!location.state?.successMessage) {
      return;
    }

    window.history.replaceState(
      {},
      document.title,
      window.location.pathname + window.location.search
    );
  }, [location]);

  const loadApplications = async () => {
    try {
      setLoading(true);
      setError("");

      const params = {
        page,
        page_size: pageSize,
        order: "desc",
      };

      if (statusFilter) {
        params.status = statusFilter;
      }

      const data = await getMyApplications(params);

      setApplications(data?.items || []);
      setTotal(data?.total || 0);
      setTotalPages(data?.total_pages || 0);
    } catch (error) {
      console.error(
        "Failed to load applications:",
        error
      );

      setError(getApiErrorMessage(error));
      setApplications([]);
      setTotal(0);
      setTotalPages(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, [page, statusFilter]);

  const handleStatusFilterChange = (event) => {
    setStatusFilter(event.target.value);
    setPage(1);
    setSelectedApplication(null);
    setHistory([]);
    setError("");
  };

  const handleViewDetails = async (applicationId) => {
    try {
      setDetailsLoadingId(applicationId);
      setError("");

      const [
        applicationData,
        historyData,
      ] = await Promise.all([
        getApplication(applicationId),
        getApplicationHistory(applicationId),
      ]);

      setSelectedApplication(applicationData);
      setHistory(historyData || []);
    } catch (error) {
      console.error(
        "Failed to load application details:",
        error
      );

      setError(getApiErrorMessage(error));
    } finally {
      setDetailsLoadingId(null);
    }
  };

  const closeDetails = () => {
    setSelectedApplication(null);
    setHistory([]);
  };

  if (loading) {
    return (
      <Loading message="Loading applications..." />
    );
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1>My Applications</h1>

          <p>
            Track the jobs you have applied for.
          </p>
        </div>
      </div>

      {successMessage && (
        <div
          className="form-success"
          role="status"
        >
          {successMessage}
        </div>
      )}

      {error && (
        <div
          className="form-error"
          role="alert"
        >
          {error}
        </div>
      )}

      <section className="dashboard-section">
        <div className="form-group">
          <label htmlFor="application-status">
            Filter by Status
          </label>

          <select
            id="application-status"
            value={statusFilter}
            onChange={handleStatusFilterChange}
          >
            <option value="">
              All Applications
            </option>

            <option value="Applied">
              Applied
            </option>

            <option value="Shortlisted">
              Shortlisted
            </option>

            <option value="Rejected">
              Rejected
            </option>

            <option value="Selected">
              Selected
            </option>
          </select>
        </div>

        {applications.length === 0 ? (
          <div className="empty-state">
            <h2>No applications found</h2>

            <p>
              {statusFilter
                ? `You don't have any ${statusFilter.toLowerCase()} applications.`
                : "You haven't applied for any jobs yet."}
            </p>
          </div>
        ) : (
          <>
            <div className="dashboard-grid">
              {applications.map(
                (application) => (
                  <div
                    className="dashboard-card"
                    key={application.id}
                  >
                    <h3>
                      Application #
                      {application.id}
                    </h3>

                    <p>
                      <strong>Job ID:</strong>{" "}
                      {application.job_id}
                    </p>

                    <p>
                      <strong>Resume:</strong>{" "}
                      {application.resume_id
                        ? `Resume #${application.resume_id}`
                        : "Not attached"}
                    </p>

                    <p>
                      <strong>Status:</strong>{" "}
                      {application.status}
                    </p>

                    <p>
                      <strong>Applied:</strong>{" "}
                      {application.applied_at
                        ? new Date(
                            application.applied_at
                          ).toLocaleDateString()
                        : "Not available"}
                    </p>

                    <p>
                      <strong>Last Updated:</strong>{" "}
                      {application.updated_at
                        ? new Date(
                            application.updated_at
                          ).toLocaleDateString()
                        : "Not available"}
                    </p>

                    <button
                      type="button"
                      className="primary-button"
                      disabled={
                        detailsLoadingId ===
                        application.id
                      }
                      onClick={() =>
                        handleViewDetails(
                          application.id
                        )
                      }
                    >
                      {detailsLoadingId ===
                      application.id
                        ? "Loading..."
                        : "View Details"}
                    </button>
                  </div>
                )
              )}
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="secondary-button"
                disabled={page <= 1}
                onClick={() =>
                  setPage(
                    (currentPage) =>
                      currentPage - 1
                  )
                }
              >
                Previous
              </button>

              <span
                aria-live="polite"
              >
                Page {page}
                {totalPages > 0
                  ? ` of ${totalPages}`
                  : ""}
              </span>

              <button
                type="button"
                className="secondary-button"
                disabled={
                  totalPages === 0 ||
                  page >= totalPages
                }
                onClick={() =>
                  setPage(
                    (currentPage) =>
                      currentPage + 1
                  )
                }
              >
                Next
              </button>
            </div>

            <p>
              Total applications: {total}
            </p>
          </>
        )}
      </section>

      {selectedApplication && (
        <section className="dashboard-section">
          <div className="dashboard-card">
            <h2>Application Details</h2>

            <p>
              <strong>Application:</strong>{" "}
              #{selectedApplication.id}
            </p>

            <p>
              <strong>Job:</strong>{" "}
              {selectedApplication.job?.title ||
                "Not available"}
            </p>

            <p>
              <strong>Company:</strong>{" "}
              {selectedApplication.job?.company
                ?.name || "Not available"}
            </p>

            <p>
              <strong>Location:</strong>{" "}
              {selectedApplication.job?.location ||
                "Not available"}
            </p>

            <p>
              <strong>Status:</strong>{" "}
              {selectedApplication.status}
            </p>

            <p>
              <strong>Resume:</strong>{" "}
              {selectedApplication.resume
                ?.original_filename ||
                "Not attached"}
            </p>

            {selectedApplication.resume && (
              <p>
                <strong>Resume Type:</strong>{" "}
                {selectedApplication.resume
                  .file_type ||
                  "Not available"}
              </p>
            )}

            <p>
              <strong>Applied:</strong>{" "}
              {selectedApplication.applied_at
                ? new Date(
                    selectedApplication.applied_at
                  ).toLocaleDateString()
                : "Not available"}
            </p>

            <p>
              <strong>Last Updated:</strong>{" "}
              {selectedApplication.updated_at
                ? new Date(
                    selectedApplication.updated_at
                  ).toLocaleDateString()
                : "Not available"}
            </p>

            <h3>Status History</h3>

            {history.length === 0 ? (
              <p>
                No status changes recorded.
              </p>
            ) : (
              history.map((entry) => (
                <div
                  className="dashboard-card"
                  key={entry.id}
                >
                  <p>
                    <strong>Status:</strong>{" "}
                    {entry.old_status
                      ? `${entry.old_status} → `
                      : ""}
                    {entry.new_status}
                  </p>

                  <p>
                    <strong>Changed At:</strong>{" "}
                    {entry.changed_at
                      ? new Date(
                          entry.changed_at
                        ).toLocaleString()
                      : "Not available"}
                  </p>
                </div>
              ))
            )}

            <button
              type="button"
              className="secondary-button"
              onClick={closeDetails}
            >
              Close Details
            </button>
          </div>
        </section>
      )}
    </div>
  );
}

export default Applications;