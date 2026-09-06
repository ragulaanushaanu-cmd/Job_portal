import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createJob } from "../../api/jobsApi";
import { getEmployerCompanies } from "../../api/companyApi";
import Loading from "../../components/Loading";
import { getApiErrorMessage } from "../../utils/apiError";

function CreateJob() {
  const navigate = useNavigate();

  const [companies, setCompanies] = useState([]);
  const [loadingCompanies, setLoadingCompanies] = useState(true);

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    salary: "",
    location: "",
    skills: "",
    company_id: "",
    employment_type: "Full-time",
    experience_level: "Entry",
    work_mode: "Onsite",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // ----------------------------------------------------------
  // Load employer's companies
  // ----------------------------------------------------------

  useEffect(() => {
    const loadCompanies = async () => {
      try {
        setError("");

        const data = await getEmployerCompanies();
        setCompanies(data);
      } catch (error) {
        console.error("Failed to load companies:", error);

        setError(getApiErrorMessage(error));
      } finally {
        setLoadingCompanies(false);
      }
    };

    loadCompanies();
  }, []);

  // ----------------------------------------------------------
  // Handle input changes
  // ----------------------------------------------------------

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // ----------------------------------------------------------
  // Submit
  // ----------------------------------------------------------

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    const salary = Number(formData.salary);

    if (!Number.isFinite(salary) || salary <= 0) {
      setError("Please enter a valid salary greater than 0.");
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

    setLoading(true);

    try {
      const jobData = {
        title: formData.title,
        description: formData.description,
        salary,
        location: formData.location,
        skills,
        company_id: Number(formData.company_id),
        employment_type: formData.employment_type,
        experience_level: formData.experience_level,
        work_mode: formData.work_mode,
      };

      await createJob(jobData);

      setSuccess("Job created successfully.");

      setTimeout(() => {
        navigate("/employer/jobs");
      }, 800);
    } catch (error) {
      console.error("Failed to create job:", error);

      setError(getApiErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  // ----------------------------------------------------------
  // Loading companies
  // ----------------------------------------------------------

  if (loadingCompanies) {
    return <Loading message="Loading companies..." />;
  }

  // ----------------------------------------------------------
  // Render
  // ----------------------------------------------------------

  return (
    <div className="form-page">
      <div className="page-header">
        <h1>Create Job</h1>
        <p>Create a new job posting for your company.</p>
      </div>

      <form
        className="form-card"
        onSubmit={handleSubmit}
      >
        {/* Company */}

        <div className="form-group">
          <label htmlFor="company_id">
            Company
          </label>

          <select
            id="company_id"
            name="company_id"
            value={formData.company_id}
            onChange={handleChange}
            required
          >
            <option value="">
              Select a company
            </option>

            {companies.map((company) => (
              <option
                key={company.id}
                value={company.id}
              >
                {company.name}
              </option>
            ))}
          </select>
        </div>

        {/* Job Title */}

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

        {/* Description */}

        <div className="form-group">
          <label htmlFor="description">
            Description
          </label>

          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            minLength={10}
            maxLength={2000}
            rows={6}
            required
          />
        </div>

        {/* Salary */}

        <div className="form-group">
          <label htmlFor="salary">
            Salary
          </label>

          <input
            id="salary"
            name="salary"
            type="number"
            value={formData.salary}
            onChange={handleChange}
            min="0.01"
            step="0.01"
            required
          />
        </div>

        {/* Location */}

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

        {/* Skills */}

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
            placeholder="Python, FastAPI, SQL, Docker"
            required
          />

          <small>
            Enter skills separated by commas.
          </small>
        </div>

        {/* Employment Type */}

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
            <option value="Full-time">Full-time</option>
            <option value="Part-time">Part-time</option>
            <option value="Contract">Contract</option>
            <option value="Internship">Internship</option>
          </select>
        </div>

        {/* Experience Level */}

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

        {/* Work Mode */}

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

        {/* Messages */}

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        {success && (
          <div className="form-success">
            {success}
          </div>
        )}

        {/* Actions */}

        <div className="form-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate("/employer/jobs")}
            disabled={loading}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-button"
            disabled={loading || companies.length === 0}
          >
            {loading ? "Creating..." : "Create Job"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default CreateJob;