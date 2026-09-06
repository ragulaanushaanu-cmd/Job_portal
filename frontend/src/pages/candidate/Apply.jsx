import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { getJob } from "../../api/candidateJobsApi";
import { createApplication } from "../../api/candidateApplicationsApi";
import { getMyResumes } from "../../api/resumesApi";
import Loading from "../../components/Loading";
import { getApiErrorMessage } from "../../utils/apiError";

function Apply() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [job, setJob] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [resumeId, setResumeId] = useState("");

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    const loadApplyData = async () => {
      try {
        setLoading(true);
        setError("");

        const [jobData, resumeData] = await Promise.all([
          getJob(jobId),
          getMyResumes(),
        ]);

        setJob(jobData);

        const resumeList =
          resumeData?.items || resumeData || [];

        setResumes(resumeList);

        const primaryResume = resumeList.find(
          (resume) => resume.is_primary
        );

        if (primaryResume) {
          setResumeId(String(primaryResume.id));
        } else if (resumeList.length > 0) {
          setResumeId(String(resumeList[0].id));
        }
      } catch (error) {
        console.error(
          "Failed to load application data:",
          error
        );

        setError(getApiErrorMessage(error));
      } finally {
        setLoading(false);
      }
    };

    loadApplyData();
  }, [jobId]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!resumeId) {
      setError("Please select a resume before applying.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      await createApplication({
        job_id: Number(jobId),
        resume_id: Number(resumeId),
      });

      navigate("/candidate/applications", {
        replace: true,
        state: {
          successMessage:
            "Application submitted successfully.",
        },
      });
    } catch (error) {
      console.error(
        "Failed to submit application:",
        error
      );

      setError(getApiErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Loading message="Loading application form..." />
    );
  }

  if (error && !job) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <h1>Apply for Job</h1>
        </div>

        <div className="form-error" role="alert">
          {error}
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            navigate(`/candidate/jobs/${jobId}`)
          }
        >
          Back to Job
        </button>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <h1>Apply for Job</h1>
        </div>

        <div className="form-error" role="alert">
          Job information is not available.
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            navigate(`/candidate/jobs/${jobId}`)
          }
        >
          Back to Job
        </button>
      </div>
    );
  }

  return (
    <div className="form-page">
      <div className="page-header">
        <h1>Apply for {job.title}</h1>

        <p>
          Submit your application using one of your
          resumes.
        </p>
      </div>

      <form
        className="form-card"
        onSubmit={handleSubmit}
      >
        <div className="form-group">
          <label htmlFor="job">
            Job
          </label>

          <input
            id="job"
            type="text"
            value={`${job.title} - ${
              job.company?.name || "Company"
            }`}
            disabled
          />
        </div>

        <div className="form-group">
          <label htmlFor="resume">
            Select Resume
          </label>

          {resumes.length === 0 ? (
            <div className="empty-state">
              <p>
                You don't have any resumes yet.
              </p>

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  navigate("/candidate/resumes", {
                    state: {
                      returnTo: `/candidate/jobs/${jobId}/apply`,
                    },
                  })
                }
              >
                Upload Resume
              </button>
            </div>
          ) : (
            <select
              id="resume"
              value={resumeId}
              onChange={(event) =>
                setResumeId(event.target.value)
              }
              disabled={submitting}
              required
            >
              <option value="">
                Select a resume
              </option>

              {resumes.map((resume) => (
                <option
                  key={resume.id}
                  value={resume.id}
                >
                  {resume.original_filename ||
                    `Resume #${resume.id}`}
                  {resume.is_primary
                    ? " (Primary)"
                    : ""}
                </option>
              ))}
            </select>
          )}
        </div>

        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}

        {resumes.length > 0 && (
          <div className="form-actions">
            <button
              type="button"
              className="secondary-button"
              disabled={submitting}
              onClick={() =>
                navigate(
                  `/candidate/jobs/${jobId}`
                )
              }
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={
                submitting || !resumeId
              }
            >
              {submitting
                ? "Submitting..."
                : "Submit Application"}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}

export default Apply;