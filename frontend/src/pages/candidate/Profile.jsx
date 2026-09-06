import { useCallback, useEffect, useState } from "react";

import {
  getMyProfile,
  createProfile,
  updateProfile,
  deleteProfile,
} from "../../api/candidateProfileApi";
import Loading from "../../components/Loading";
import { getApiErrorMessage } from "../../utils/apiError";

const EMPTY_FORM = {
  headline: "",
  bio: "",
  phone: "",
  location: "",
  experience_years: "",
  education: "",
  skills: "",
  linkedin_url: "",
  github_url: "",
  portfolio_url: "",
};

function profileToFormData(profile) {
  return {
    headline: profile?.headline || "",
    bio: profile?.bio || "",
    phone: profile?.phone || "",
    location: profile?.location || "",
    experience_years: profile?.experience_years ?? "",
    education: profile?.education || "",
    skills: Array.isArray(profile?.skills)
      ? profile.skills.join(", ")
      : "",
    linkedin_url: profile?.linkedin_url || "",
    github_url: profile?.github_url || "",
    portfolio_url: profile?.portfolio_url || "",
  };
}

function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [formData, setFormData] = useState({ ...EMPTY_FORM });

  const resetForm = useCallback(() => {
    setFormData({ ...EMPTY_FORM });
  }, []);

  const loadProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      setSuccess("");

      const data = await getMyProfile();

      setProfile(data);
      setFormData(profileToFormData(data));
    } catch (err) {
      console.error("Failed to load profile:", err);

      if (err.response?.status === 404) {
        setProfile(null);
        resetForm();
        setError("");
      } else {
        setError(getApiErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }, [resetForm]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));

    if (error) {
      setError("");
    }

    if (success) {
      setSuccess("");
    }
  };

  const buildProfileData = () => {
    let experienceYears = null;

    if (formData.experience_years !== "") {
      experienceYears = Number(formData.experience_years);

      if (!Number.isFinite(experienceYears)) {
        throw new Error("Experience years must be a valid number.");
      }

      if (experienceYears < 0) {
        throw new Error("Experience years cannot be negative.");
      }

      if (experienceYears > 99.9) {
        throw new Error("Experience years cannot exceed 99.9.");
      }

      if (
        Math.round(experienceYears * 10) !==
        experienceYears * 10
      ) {
        throw new Error(
          "Experience years can have at most one decimal place."
        );
      }
    }

    const skills = formData.skills
      ? formData.skills
          .split(",")
          .map((skill) => skill.trim())
          .filter(Boolean)
      : null;

    return {
      headline: formData.headline.trim() || null,
      bio: formData.bio.trim() || null,
      phone: formData.phone.trim() || null,
      location: formData.location.trim() || null,
      experience_years: experienceYears,
      education: formData.education.trim() || null,
      skills,
      linkedin_url: formData.linkedin_url.trim() || null,
      github_url: formData.github_url.trim() || null,
      portfolio_url: formData.portfolio_url.trim() || null,
    };
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (deleting) {
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const data = buildProfileData();

      let result;

      if (profile) {
        result = await updateProfile(data);
        setSuccess("Profile updated successfully.");
      } else {
        result = await createProfile(data);
        setSuccess("Profile created successfully.");
      }

      setProfile(result);
      setFormData(profileToFormData(result));
    } catch (err) {
      console.error("Failed to save profile:", err);

      if (err instanceof Error && !err.response) {
        setError(err.message);
      } else {
        setError(getApiErrorMessage(err));
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (saving || deleting) {
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to delete your profile?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);
      setError("");
      setSuccess("");

      await deleteProfile();

      setProfile(null);
      resetForm();

      setSuccess("Profile deleted successfully.");
    } catch (err) {
      console.error("Failed to delete profile:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <Loading message="Loading profile..." />;
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1>Candidate Profile</h1>
        <p>Create and manage your professional profile.</p>
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

      <section className="dashboard-section">
        <form className="form-card" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="headline">Professional Headline</label>
            <input
              id="headline"
              name="headline"
              type="text"
              maxLength={150}
              value={formData.headline}
              onChange={handleChange}
              placeholder="e.g. Backend Developer"
              disabled={saving || deleting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="bio">Bio</label>
            <textarea
              id="bio"
              name="bio"
              maxLength={1000}
              rows={5}
              value={formData.bio}
              onChange={handleChange}
              placeholder="Tell employers about yourself..."
              disabled={saving || deleting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone</label>
            <input
              id="phone"
              name="phone"
              type="tel"
              maxLength={15}
              value={formData.phone}
              onChange={handleChange}
              disabled={saving || deleting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="location">Location</label>
            <input
              id="location"
              name="location"
              type="text"
              maxLength={100}
              value={formData.location}
              onChange={handleChange}
              placeholder="e.g. Hyderabad"
              disabled={saving || deleting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="experience_years">
              Experience (Years)
            </label>

            <input
              id="experience_years"
              name="experience_years"
              type="number"
              min="0"
              max="99.9"
              step="0.1"
              value={formData.experience_years}
              onChange={handleChange}
              disabled={saving || deleting}
            />

            <small>
              Enter experience in years, including decimals such as 1.5.
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="education">Education</label>

            <textarea
              id="education"
              name="education"
              maxLength={500}
              rows={3}
              value={formData.education}
              onChange={handleChange}
              placeholder="e.g. B.Tech Computer Science"
              disabled={saving || deleting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="skills">Skills</label>

            <input
              id="skills"
              name="skills"
              type="text"
              value={formData.skills}
              onChange={handleChange}
              placeholder="Python, FastAPI, SQL, MySQL"
              disabled={saving || deleting}
            />

            <small>Separate skills with commas.</small>
          </div>

          <div className="form-group">
            <label htmlFor="linkedin_url">LinkedIn URL</label>

            <input
              id="linkedin_url"
              name="linkedin_url"
              type="url"
              maxLength={255}
              value={formData.linkedin_url}
              onChange={handleChange}
              placeholder="https://linkedin.com/in/..."
              disabled={saving || deleting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="github_url">GitHub URL</label>

            <input
              id="github_url"
              name="github_url"
              type="url"
              maxLength={255}
              value={formData.github_url}
              onChange={handleChange}
              placeholder="https://github.com/..."
              disabled={saving || deleting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="portfolio_url">Portfolio URL</label>

            <input
              id="portfolio_url"
              name="portfolio_url"
              type="url"
              maxLength={255}
              value={formData.portfolio_url}
              onChange={handleChange}
              placeholder="https://..."
              disabled={saving || deleting}
            />
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="primary-button"
              disabled={saving || deleting}
            >
              {saving
                ? "Saving..."
                : profile
                ? "Update Profile"
                : "Create Profile"}
            </button>

            {profile && (
              <button
                type="button"
                className="secondary-button"
                disabled={saving || deleting}
                onClick={handleDelete}
              >
                {deleting ? "Deleting..." : "Delete Profile"}
              </button>
            )}
          </div>
        </form>
      </section>
    </div>
  );
}

export default Profile;