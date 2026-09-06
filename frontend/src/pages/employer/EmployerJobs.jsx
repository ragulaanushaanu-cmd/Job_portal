import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import Loading from "../../components/Loading";
import { getEmployerJobs, deleteJob } from "../../api/jobsApi";
import { getApiErrorMessage } from "../../utils/apiError";

function EmployerJobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingJobId, setDeletingJobId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadJobs = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getEmployerJobs();

      setJobs(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to load employer jobs:", error);
      setError(getApiErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleDelete = async (jobId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this job?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingJobId(jobId);
      setError("");
      setSuccess("");

      await deleteJob(jobId);

      setJobs((currentJobs) =>
        currentJobs.filter((job) => job.id !== jobId)
      );

      setSuccess("Job deleted successfully.");
    } catch (error) {
      console.error("Failed to delete job:", error);
      setError(getApiErrorMessage(error));
    } finally {
      setDeletingJobId(null);
    }
  };

  if (loading) {
    return <Loading message="Loading your jobs..." />;
  }

  return (
    <div className="employer-jobs-page">
      <div className="page-header">
        <div>
          <h1>My Jobs</h1>
          <p>Manage the jobs you have posted.</p>
        </div>

        <Link
          to="/employer/jobs/new"
          className="primary-button"
        >
          Create Job
        </Link>
      </div>

      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="form-success" role="status">
          {success}
        </div>
      )}

      {jobs.length === 0 ? (
        <div className="empty-state">
          <h2>No jobs posted yet</h2>

          <p>
            You have not created any job postings. Create your first job to
            start receiving applications.
          </p>

          <Link
            to="/employer/jobs/new"
            className="primary-button"
          >
            Create Your First Job
          </Link>
        </div>
      ) : (
        <div className="jobs-list">
          {jobs.map((job) => (
            <div className="job-card" key={job.id}>
              <div className="job-card-content">
                <h2>{job.title}</h2>

                <p>
                  <strong>Location:</strong>{" "}
                  {job.location || "Not specified"}
                </p>

                <p>
                  <strong>Employment Type:</strong>{" "}
                  {job.employment_type || "Not specified"}
                </p>

                <p>
                  <strong>Experience Level:</strong>{" "}
                  {job.experience_level || "Not specified"}
                </p>

                <p>
                  <strong>Work Mode:</strong>{" "}
                  {job.work_mode || "Not specified"}
                </p>

                <p>
                  <strong>Salary:</strong>{" "}
                  {job.salary != null ? job.salary : "Not specified"}
                </p>

                {Array.isArray(job.skills) && job.skills.length > 0 && (
                  <p>
                    <strong>Skills:</strong>{" "}
                    {job.skills.join(", ")}
                  </p>
                )}
              </div>

              <div className="job-card-actions">
                <Link
                  to={`/employer/jobs/${job.id}/edit`}
                  className="secondary-button"
                >
                  Edit
                </Link>

                <Link
                  to={`/employer/jobs/${job.id}`}
                  className="secondary-button"
                >
                  View
                </Link>

                <button
                  type="button"
                  className="danger-button"
                  onClick={() => handleDelete(job.id)}
                  disabled={deletingJobId === job.id}
                >
                  {deletingJobId === job.id
                    ? "Deleting..."
                    : "Delete"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default EmployerJobs;














// import { useEffect, useState } from "react";
// import { Link } from "react-router-dom";

// import Loading from "../../components/Loading";
// import { getEmployerJobs, deleteJob } from "../../api/jobsApi";
// import { getApiErrorMessage } from "../../utils/apiError";

// function EmployerJobs() {
//   const [jobs, setJobs] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [deletingJobId, setDeletingJobId] = useState(null);
//   const [error, setError] = useState("");
//   const [success, setSuccess] = useState("");

//   const loadJobs = async () => {
//     try {
//       setLoading(true);
//       setError("");

//       const data = await getEmployerJobs();
//       setJobs(data || []);
//     } catch (error) {
//       console.error("Failed to load employer jobs:", error);
//       setError(getApiErrorMessage(error));
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     loadJobs();
//   }, []);

//   const handleDelete = async (jobId) => {
//     const confirmed = window.confirm("Are you sure you want to delete this job?");
//     if (!confirmed) return;

//     try {
//       setDeletingJobId(jobId);
//       setError("");
//       setSuccess("");

//       await deleteJob(jobId);

//       setJobs((currentJobs) => currentJobs.filter((job) => job.id !== jobId));
//       setSuccess("Job deleted successfully.");
//     } catch (error) {
//       console.error("Failed to delete job:", error);
//       setError(getApiErrorMessage(error));
//     } finally {
//       setDeletingJobId(null);
//     }
//   };

//   if (loading) {
//     return <Loading message="Loading your jobs..." />;
//   }

//   return (
//     <div className="employer-jobs-page">
//       <div className="page-header">
//         <div>
//           <h1>My Jobs</h1>
//           <p>Manage the jobs you have posted.</p>
//         </div>

//         <Link to="/employer/jobs/create" className="primary-button">
//           Create Job
//         </Link>
//       </div>

//       {error && (
//         <div className="form-error" role="alert">
//           {error}
//         </div>
//       )}

//       {success && (
//         <div className="form-success" role="status">
//           {success}
//         </div>
//       )}

//       {jobs.length === 0 ? (
//         <div className="empty-state">
//           <h2>No jobs posted yet</h2>
//           <p>
//             You have not created any job postings. Create your first job to
//             start receiving applications.
//           </p>
//           <Link to="/employer/jobs/create" className="primary-button">
//             Create Your First Job
//           </Link>
//         </div>
//       ) : (
//         <div className="jobs-list">
//           {jobs.map((job) => (
//             <div className="job-card" key={job.id}>
//               <div className="job-card-content">
//                 <h2>{job.title}</h2>

//                 <p>
//                   <strong>Location:</strong> {job.location || "Not specified"}
//                 </p>

//                 <p>
//                   <strong>Employment Type:</strong>{" "}
//                   {job.employment_type || "Not specified"}
//                 </p>

//                 <p>
//                   <strong>Experience Level:</strong>{" "}
//                   {job.experience_level || "Not specified"}
//                 </p>

//                 <p>
//                   <strong>Work Mode:</strong> {job.work_mode || "Not specified"}
//                 </p>

//                 {job.salary_min != null || job.salary_max != null ? (
//                   <p>
//                     <strong>Salary:</strong>{" "}
//                     {job.salary_min != null ? job.salary_min : "—"} -{" "}
//                     {job.salary_max != null ? job.salary_max : "—"}
//                   </p>
//                 ) : null}
//               </div>

//               <div className="job-card-actions">
//                 <Link to={`/employer/jobs/${job.id}/edit`} className="secondary-button">
//                   Edit
//                 </Link>

//                 <Link to={`/jobs/${job.id}`} className="secondary-button">
//                   View
//                 </Link>

//                 <button
//                   type="button"
//                   className="danger-button"
//                   onClick={() => handleDelete(job.id)}
//                   disabled={deletingJobId === job.id}
//                 >
//                   {deletingJobId === job.id ? "Deleting..." : "Delete"}
//                 </button>
//               </div>
//             </div>
//           ))}
//         </div>
//       )}
//     </div>
//   );
// }

// export default EmployerJobs;