import { useEffect, useState } from "react";

import {
  getEmployerApplications,
  updateApplicationStatus,
} from "../../api/applicationsApi";

function Applications() {
  const [applications, setApplications] = useState([]);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);

  const [statusFilter, setStatusFilter] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState(null);

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

      const data = await getEmployerApplications(params);

      setApplications(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 0);
    } catch (error) {
      console.error(
        "Failed to load employer applications:",
        error
      );

      setError(
        error.response?.data?.detail ||
          "Failed to load applications."
      );
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
  };

  const handleStatusChange = async (applicationId, status) => {
    try {
      setUpdatingId(applicationId);
      setError("");

      const updatedApplication =
        await updateApplicationStatus(
          applicationId,
          status
        );

      setApplications((previousApplications) =>
        previousApplications.map((application) =>
          application.id === updatedApplication.id
            ? updatedApplication
            : application
        )
      );
    } catch (error) {
      console.error(
        "Failed to update application status:",
        error
      );

      setError(
        error.response?.data?.detail ||
          "Failed to update application status."
      );
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading) {
    return <p>Loading applications...</p>;
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1>Applications</h1>
        <p>
          Review applications submitted to your jobs.
        </p>
      </div>

      {error && (
        <div className="form-error">
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
            <option value="">All Applications</option>
            <option value="Applied">Applied</option>
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
            <p>No applications found.</p>
          </div>
        ) : (
          <>
            <div className="dashboard-grid">
              {applications.map((application) => (
                <div
                  className="dashboard-card"
                  key={application.id}
                >
                  <h3>
                    Application #{application.id}
                  </h3>

                  <p>
                    <strong>Candidate:</strong>{" "}
                    {application.user?.username || "Unknown candidate"}
                  </p>

                  <p>
                    <strong>Email:</strong>{" "}
                    {application.user?.email || "Not available"}
                  </p>

                  <p>
                    <strong>Job:</strong>{" "}
                    {application.job?.title || "Unknown job"}
                  </p>

                  <p>
                    <strong>Company:</strong>{" "}
                    {application.job?.company?.name || "Unknown company"}
                  </p>

                  <p>
                    <strong>Location:</strong>{" "}
                    {application.job?.location || "Not specified"}
                  </p>

                  <p>
                    <strong>Resume:</strong>{" "}
                    {application.resume?.original_filename ||
                      "Not attached"}
                  </p>

                  <p>
                    <strong>Applied:</strong>{" "}
                    {application.applied_at
                      ? new Date(application.applied_at).toLocaleDateString()
                      : "Not available"}
                  </p>

                  <p>
                    <strong>Updated:</strong>{" "}
                    {application.updated_at
                      ? new Date(application.updated_at).toLocaleDateString()
                      : "Not available"}
                  </p>

                  <div className="form-group">
                    <label
                      htmlFor={`status-${application.id}`}
                    >
                      Status
                    </label>

                    <select
                      id={`status-${application.id}`}
                      value={application.status}
                      disabled={
                        updatingId === application.id
                      }
                      onChange={(event) =>
                        handleStatusChange(
                          application.id,
                          event.target.value
                        )
                      }
                    >
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

                  {updatingId === application.id && (
                    <small>
                      Updating status...
                    </small>
                  )}
                </div>
              ))}
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="secondary-button"
                disabled={page <= 1}
                onClick={() =>
                  setPage((current) => current - 1)
                }
              >
                Previous
              </button>

              <span>
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
                  setPage((current) => current + 1)
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
    </div>
  );
}

export default Applications;