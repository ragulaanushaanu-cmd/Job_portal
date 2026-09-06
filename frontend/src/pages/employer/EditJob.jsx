import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getJob, updateJob } from "../../api/jobsApi";
import Loading from "../../components/Loading";
import { getApiErrorMessage } from "../../utils/apiError";

function EditJob() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    salary: "",
    location: "",
    skills: "",
    employment_type: "Full-time",
    experience_level: "Entry",
    work_mode: "Onsite",
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadJob = async () => {
      try {
        setError("");

        const job = await getJob(jobId);

        setFormData({
          title: job.title || "",
          description: job.description || "",
          salary: job.salary || "",
          location: job.location || "",
          skills: job.skills?.join(", ") || "",
          employment_type:
            job.employment_type || "Full-time",
          experience_level:
            job.experience_level || "Entry",
          work_mode: job.work_mode || "Onsite",
        });
      } catch (error) {
        console.error("Failed to load job:", error);

        setError(getApiErrorMessage(error));
      } finally {
        setLoading(false);
      }
    };

    loadJob();
  }, [jobId]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    const salary = Number(formData.salary);

    if (!Number.isFinite(salary) || salary <= 0) {
      setError(
        "Please enter a valid salary greater than 0."
      );
      return;
    }

    const skills = formData.skills
      .split(",")
      .map((skill) => skill.trim())
      .filter(Boolean);

    if (skills.length === 0) {
      setError("Please enter at least one skill.");
      return;
    }

    try {
      setSaving(true);

      const jobData = {
        title: formData.title,
        description: formData.description,
        salary,
        location: formData.location,
        skills,
        employment_type: formData.employment_type,
        experience_level: formData.experience_level,
        work_mode: formData.work_mode,
      };

      await updateJob(jobId, jobData);

      navigate(`/employer/jobs/${jobId}`);
    } catch (error) {
      console.error("Failed to update job:", error);

      setError(getApiErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Loading message="Loading job..." />;
  }

  if (error && !formData.title) {
    return (
      <div className="dashboard-page">
        <div className="page-header">
          <h1>Edit Job</h1>
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

  return (
    <div className="form-page">
      <div className="page-header">
        <h1>Edit Job</h1>
        <p>Update your job posting.</p>
      </div>

      <form
        className="form-card"
        onSubmit={handleSubmit}
      >
        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="title">
            Job Title
          </label>

          <input
            id="title"
            name="title"
            type="text"
            value={formData.title}
            onChange={handleChange}
            minLength={3}
            maxLength={100}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">
            Description
          </label>

          <textarea
            id="description"
            name="description"
            rows="6"
            value={formData.description}
            onChange={handleChange}
            minLength={10}
            maxLength={2000}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="salary">
            Salary
          </label>

          <input
            id="salary"
            name="salary"
            type="number"
            min="0.01"
            step="0.01"
            value={formData.salary}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="location">
            Location
          </label>

          <input
            id="location"
            name="location"
            type="text"
            value={formData.location}
            onChange={handleChange}
            minLength={2}
            maxLength={100}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="skills">
            Skills
          </label>

          <input
            id="skills"
            name="skills"
            type="text"
            value={formData.skills}
            onChange={handleChange}
            placeholder="Python, FastAPI, SQL"
            required
          />

          <small>
            Separate skills with commas.
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="employment_type">
            Employment Type
          </label>

          <select
            id="employment_type"
            name="employment_type"
            value={formData.employment_type}
            onChange={handleChange}
          >
            <option value="Full-time">
              Full-time
            </option>
            <option value="Part-time">
              Part-time
            </option>
            <option value="Contract">
              Contract
            </option>
            <option value="Internship">
              Internship
            </option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="experience_level">
            Experience Level
          </label>

          <select
            id="experience_level"
            name="experience_level"
            value={formData.experience_level}
            onChange={handleChange}
          >
            <option value="Entry">Entry</option>
            <option value="Junior">Junior</option>
            <option value="Mid">Mid</option>
            <option value="Senior">Senior</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="work_mode">
            Work Mode
          </label>

          <select
            id="work_mode"
            name="work_mode"
            value={formData.work_mode}
            onChange={handleChange}
          >
            <option value="Onsite">Onsite</option>
            <option value="Remote">Remote</option>
            <option value="Hybrid">Hybrid</option>
          </select>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              navigate(
                `/employer/jobs/${jobId}`
              )
            }
            disabled={saving}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-button"
            disabled={saving}
          >
            {saving
              ? "Saving..."
              : "Save Changes"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default EditJob;