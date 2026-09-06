
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getJob } from "../../api/candidateJobsApi";
import { saveJob } from "../../api/candidateSavedJobsApi";
import { getMyResumes } from "../../api/candidateResumesApi";
import { analyzeResume } from "../../api/ats";
import Loading from "../../components/Loading";
import { getApiErrorMessage } from "../../utils/apiError";

function JobDetails() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [jobSaved, setJobSaved] = useState(false);

  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [resumeLoading, setResumeLoading] = useState(true);
  const [resumeError, setResumeError] = useState("");

  const [atsLoading, setAtsLoading] = useState(false);
  const [atsResult, setAtsResult] = useState(null);
  const [atsError, setAtsError] = useState("");

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

  useEffect(() => {
    const loadResumes = async () => {
      try {
        setResumeLoading(true);
        setResumeError("");

        const data = await getMyResumes();
        const resumeList = data?.items || data || [];

        setResumes(resumeList);

        const primaryResume = resumeList.find(
          (resume) => resume.is_primary
        );

        if (primaryResume) {
          setSelectedResumeId(String(primaryResume.id));
        } else if (resumeList.length > 0) {
          setSelectedResumeId(String(resumeList[0].id));
        }
      } catch (error) {
        console.error("Failed to load resumes:", error);
        setResumeError(getApiErrorMessage(error));
      } finally {
        setResumeLoading(false);
      }
    };

    loadResumes();
  }, []);

  const handleSaveJob = async () => {
    try {
      setSaving(true);
      setError("");
      setSaveMessage("");

      await saveJob(jobId);

      setJobSaved(true);
      setSaveMessage("Job saved successfully.");
    } catch (error) {
      console.error("Failed to save job:", error);

      if (error.response?.status === 409) {
        setJobSaved(true);
        setSaveMessage("This job is already saved.");
        return;
      }

      setError(getApiErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  const handleATSAnalysis = async () => {
    if (!selectedResumeId) {
      setAtsError("Please select a resume first.");
      return;
    }

    try {
      setAtsLoading(true);
      setAtsError("");
      setAtsResult(null);

      const result = await analyzeResume(
        Number(selectedResumeId),
        Number(jobId)
      );

      setAtsResult(result);
    } catch (error) {
      console.error("Failed to analyze resume:", error);
      setAtsError(getApiErrorMessage(error));
    } finally {
      setAtsLoading(false);
    }
  };

  if (loading) {
    return <Loading message="Loading job details..." />;
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <h1>Job Details</h1>
        </div>

        <div className="form-error" role="alert">
          {error}
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() => navigate("/candidate/jobs")}
        >
          Back to Jobs
        </button>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="dashboard-page">
        <p>Job not found.</p>

        <button
          type="button"
          className="secondary-button"
          onClick={() => navigate("/candidate/jobs")}
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

        <p>View complete job posting details.</p>
      </div>

      <section className="dashboard-section">
        <div className="dashboard-card">
          <h2>Job Information</h2>

          <p>
            <strong>Company:</strong>{" "}
            {job.company?.name || "Company not available"}
          </p>

          <p>
            <strong>Description:</strong> {job.description}
          </p>

          <p>
            <strong>Salary:</strong> ₹{job.salary}
          </p>

          <p>
            <strong>Location:</strong>{" "}
            {job.location || "Not specified"}
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
            {Array.isArray(job.skills) && job.skills.length > 0
              ? job.skills.join(", ")
              : "Not provided"}
          </p>

          <p>
            <strong>Posted:</strong>{" "}
            {job.posted_at
              ? new Date(job.posted_at).toLocaleDateString()
              : "Not available"}
          </p>
        </div>
      </section>

      {saveMessage && (
        <div
          className="form-success"
          role="status"
          aria-live="polite"
        >
          {saveMessage}
        </div>
      )}

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
          onClick={() => navigate("/candidate/jobs")}
        >
          Back to Jobs
        </button>

        <button
          type="button"
          className="secondary-button"
          disabled={saving || jobSaved}
          onClick={handleSaveJob}
        >
          {saving
            ? "Saving..."
            : jobSaved
              ? "Job Saved"
              : "Save Job"}
        </button>

        <button
          type="button"
          className="secondary-button"
          disabled={
            atsLoading ||
            resumeLoading ||
            resumes.length === 0
          }
          onClick={handleATSAnalysis}
        >
          {atsLoading ? "Analyzing..." : "Analyze Resume"}
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={() =>
            navigate(`/candidate/jobs/${jobId}/apply`)
          }
        >
          Apply to Job
        </button>
      </div>

      <section className="dashboard-section">
        <div className="dashboard-card">
          <h2>Resume for ATS Analysis</h2>

          {resumeLoading && (
            <Loading message="Loading your resumes..." />
          )}

          {resumeError && (
            <div className="form-error" role="alert">
              {resumeError}
            </div>
          )}

          {!resumeLoading &&
            !resumeError &&
            resumes.length === 0 && (
              <div className="empty-state">
                <p>You don't have any resumes yet.</p>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    navigate("/candidate/resumes")
                  }
                >
                  Manage Resumes
                </button>
              </div>
            )}

          {!resumeLoading &&
            !resumeError &&
            resumes.length > 0 && (
              <div className="form-group">
                <label htmlFor="resume">
                  Select Resume
                </label>

                <select
                  id="resume"
                  value={selectedResumeId}
                  onChange={(event) =>
                    setSelectedResumeId(event.target.value)
                  }
                >
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
              </div>
            )}
        </div>
      </section>

      {atsError && (
        <div className="form-error" role="alert">
          {atsError}
        </div>
      )}

      {atsResult && (
        <section className="dashboard-section">
          <div className="dashboard-card">
            <h2>ATS Analysis Result</h2>

            <p>
              <strong>Overall Score:</strong>{" "}
              {atsResult.overall_score}
            </p>

            <p>
              <strong>Skill Score:</strong>{" "}
              {atsResult.skill_score}
            </p>

            <p>
              <strong>Experience Score:</strong>{" "}
              {atsResult.experience_score}
            </p>

            <p>
              <strong>Education Score:</strong>{" "}
              {atsResult.education_score}
            </p>

            <p>
              <strong>Keyword Score:</strong>{" "}
              {atsResult.keyword_score}
            </p>
          </div>
        </section>
      )}
    </div>
  );
}

export default JobDetails;

