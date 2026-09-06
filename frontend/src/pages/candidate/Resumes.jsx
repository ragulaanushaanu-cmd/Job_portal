import { useEffect, useRef ,useState } from "react";

import {
  getMyResumes,
  downloadResume,
  setPrimaryResume,
  deleteResume,
  uploadResume,
} from "../../api/candidateResumesApi";
import Loading from "../../components/Loading";
import { getApiErrorMessage } from "../../utils/apiError";

const ALLOWED_FILE_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

const ALLOWED_FILE_EXTENSIONS = [".pdf", ".docx"];

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) {
    return "Unknown size";
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isSupportedResumeFile(file) {
  if (!file) {
    return false;
  }

  const fileName = file.name.toLowerCase();

  const hasValidExtension = ALLOWED_FILE_EXTENSIONS.some(
    (extension) => fileName.endsWith(extension)
  );

  const hasValidMimeType =
    !file.type || ALLOWED_FILE_TYPES.includes(file.type);

  return hasValidExtension && hasValidMimeType;
}

function Resumes() {
  const [resumes, setResumes] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const uploadFormRef = useRef(null);

  const loadResumes = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getMyResumes();

      const resumeList = Array.isArray(data)
        ? data
        : data?.items || [];

      setResumes(resumeList);
    } catch (err) {
      console.error("Failed to fetch resumes:", err);

      setError(getApiErrorMessage(err));
      setResumes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResumes();
  }, []);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0] || null;

    setError("");

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!isSupportedResumeFile(file)) {
      setSelectedFile(null);
      event.target.value = "";

      setError(
        "Please select a valid PDF or DOCX resume."
      );
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      setError("Please select a PDF or DOCX file.");
      return;
    }

    if (!isSupportedResumeFile(selectedFile)) {
      setError("Please select a valid PDF or DOCX resume.");
      return;
    }

    try {
      setUploading(true);
      setError("");

      await uploadResume(selectedFile);

      setSelectedFile(null);

      uploadFormRef.current?.reset();

      await loadResumes();
    } catch (err) {
      console.error("Failed to upload resume:", err);

      setError(getApiErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (resume) => {
    try {
      setActionLoadingId(resume.id);
      setError("");

      const response = await downloadResume(resume.id);

      const blob = new Blob([response.data], {
        type:
          response.headers["content-type"] ||
          "application/octet-stream",
      });

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");

      link.href = url;
      link.download =
        resume.original_filename ||
        `resume-${resume.id}`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download resume:", err);

      setError(getApiErrorMessage(err));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleSetPrimary = async (resumeId) => {
    try {
      setActionLoadingId(resumeId);
      setError("");

      const updatedResume =
        await setPrimaryResume(resumeId);

      setResumes((previousResumes) =>
        previousResumes.map((resume) => ({
          ...resume,
          is_primary:
            resume.id === updatedResume.id,
        }))
      );
    } catch (err) {
      console.error(
        "Failed to set primary resume:",
        err
      );

      setError(getApiErrorMessage(err));
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDelete = async (resume) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${resume.original_filename}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setActionLoadingId(resume.id);
      setError("");

      await deleteResume(resume.id);

      setResumes((previousResumes) =>
        previousResumes.filter(
          (currentResume) =>
            currentResume.id !== resume.id
        )
      );
    } catch (err) {
      console.error(
        "Failed to delete resume:",
        err
      );

      setError(getApiErrorMessage(err));
    } finally {
      setActionLoadingId(null);
    }
  };

  if (loading) {
    return <Loading message="Loading resumes..." />;
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1>My Resumes</h1>
          <p>Manage your uploaded resumes.</p>
        </div>
      </div>

      {error && (
        <div
          className="form-error"
          role="alert"
        >
          {error}
        </div>
      )}

      <section className="dashboard-section">
        <h2>Upload Resume</h2>

        <form
          ref={uploadFormRef}
          className="form-card"
          onSubmit={handleUpload}
        >
          <div className="form-group">
            <label htmlFor="resume-file">
              Select Resume
            </label>

            <input
              id="resume-file"
              name="resume-file"
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={handleFileChange}
              disabled={uploading}
              aria-describedby="resume-file-help"
            />

            <p id="resume-file-help">
              PDF or DOCX files only.
            </p>

            {selectedFile && (
              <p>
                Selected:{" "}
                <strong>{selectedFile.name}</strong>
                {" · "}
                {formatFileSize(selectedFile.size)}
              </p>
            )}
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="primary-button"
              disabled={
                uploading || !selectedFile
              }
            >
              {uploading
                ? "Uploading..."
                : "Upload Resume"}
            </button>
          </div>
        </form>
      </section>

      <section className="dashboard-section">
        <h2>Your Uploaded Resumes</h2>

        {resumes.length === 0 ? (
          <div className="empty-state">
            <h3>No resumes uploaded</h3>
            <p>
              Upload a PDF or DOCX resume to use it
              for job applications and ATS analysis.
            </p>
          </div>
        ) : (
          <div className="dashboard-grid">
            {resumes.map((resume) => {
              const isLoading =
                actionLoadingId === resume.id;

              return (
                <div
                  className="dashboard-card"
                  key={resume.id}
                >
                  <h3>
                    {resume.original_filename ||
                      `Resume #${resume.id}`}
                  </h3>

                  {resume.is_primary && (
                    <p>
                      <strong>
                        Primary Resume
                      </strong>
                    </p>
                  )}

                  <p>
                    <strong>File Type:</strong>{" "}
                    {resume.file_type ||
                      "Not available"}
                  </p>

                  <p>
                    <strong>File Size:</strong>{" "}
                    {formatFileSize(
                      Number(resume.file_size)
                    )}
                  </p>

                  <p>
                    <strong>Uploaded:</strong>{" "}
                    {resume.uploaded_at
                      ? new Date(
                          resume.uploaded_at
                        ).toLocaleDateString()
                      : "Not available"}
                  </p>

                  <p>
                    <strong>Resume ID:</strong>{" "}
                    {resume.id}
                  </p>

                  <div className="form-actions">
                    <button
                      type="button"
                      className="primary-button"
                      disabled={isLoading}
                      onClick={() =>
                        handleDownload(resume)
                      }
                    >
                      {isLoading
                        ? "Processing..."
                        : "Download"}
                    </button>

                    {!resume.is_primary && (
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={isLoading}
                        onClick={() =>
                          handleSetPrimary(
                            resume.id
                          )
                        }
                      >
                        Set as Primary
                      </button>
                    )}

                    <button
                      type="button"
                      className="secondary-button"
                      disabled={isLoading}
                      onClick={() =>
                        handleDelete(resume)
                      }
                    >
                      {isLoading
                        ? "Processing..."
                        : "Delete"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

export default Resumes;