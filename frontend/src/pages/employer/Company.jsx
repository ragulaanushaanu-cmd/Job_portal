import { useEffect, useState } from "react";

import {
  createCompany,
  getEmployerCompanies,
  updateCompany,
  deleteCompany,
} from "../../api/companyApi";

function Company() {
  const [companies, setCompanies] = useState([]);

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deletingCompanyId, setDeletingCompanyId] = useState(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editingCompanyId, setEditingCompanyId] = useState(null);

  const [formData, setFormData] = useState({
    name: "",
    location: "",
    description: "",
    website: "",
  });

  const loadCompanies = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getEmployerCompanies();

      setCompanies(data);
    } catch (error) {
      console.error(
        "Failed to load employer companies:",
        error
      );

      setError(
        error.response?.data?.detail ||
          "Failed to load your companies."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCompanies();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setCreating(true);

    try {
      const companyData = {
        name: formData.name.trim(),
        location: formData.location.trim(),
        description: formData.description.trim(),
        website: formData.website.trim(),
      };

      if (editingCompanyId !== null) {
        const updatedCompany = await updateCompany(
          editingCompanyId,
          companyData
        );

        setCompanies((previous) =>
          previous.map((company) =>
            company.id === editingCompanyId
              ? updatedCompany
              : company
          )
        );

        setSuccess("Company updated successfully.");
        setEditingCompanyId(null);
      } else {
        const newCompany = await createCompany(companyData);

        setCompanies((previous) => [
          ...previous,
          newCompany,
        ]);

        setSuccess("Company created successfully.");
      }

      setFormData({
        name: "",
        location: "",
        description: "",
        website: "",
      });
    } catch (error) {
      console.error(
        "Failed to save company:",
        error
      );

      setError(
        error.response?.data?.detail ||
          "Failed to save company."
      );
    } finally {
      setCreating(false);
    }
  };

  const handleEdit = (company) => {
    setEditingCompanyId(company.id);

    setFormData({
      name: company.name || "",
      location: company.location || "",
      description: company.description || "",
      website: company.website || "",
    });

    setError("");
    setSuccess("");
  };

  const handleCancelEdit = () => {
    setEditingCompanyId(null);

    setFormData({
      name: "",
      location: "",
      description: "",
      website: "",
    });

    setError("");
    setSuccess("");
  };

  const handleDelete = async (companyId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this company?"
    );

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");
    setDeletingCompanyId(companyId);

    try {
      const data = await deleteCompany(companyId);

      setCompanies((previous) =>
        previous.filter(
          (company) => company.id !== companyId
        )
      );

      if (editingCompanyId === companyId) {
        handleCancelEdit();
      }

      setSuccess(
        data?.message ||
          "Company deleted successfully."
      );
    } catch (error) {
      console.error(
        "Failed to delete company:",
        error
      );

      setError(
        error.response?.data?.detail ||
          "Failed to delete company."
      );
    } finally {
      setDeletingCompanyId(null);
    }
  };

  if (loading) {
    return <p>Loading companies...</p>;
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1>Company</h1>
        <p>Manage your companies.</p>
      </div>

      <section className="dashboard-section">
        <h2>
          {editingCompanyId !== null
            ? "Edit Company"
            : "Create Company"}
        </h2>

        <form
          className="form-card"
          onSubmit={handleSubmit}
        >
          <div className="form-group">
            <label htmlFor="name">
              Company Name
            </label>

            <input
              id="name"
              name="name"
              type="text"
              value={formData.name}
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
              value={formData.description}
              onChange={handleChange}
              rows={5}
            />
          </div>

          <div className="form-group">
            <label htmlFor="website">
              Website
            </label>

            <input
              id="website"
              name="website"
              type="url"
              value={formData.website}
              onChange={handleChange}
              placeholder="https://example.com"
            />
          </div>

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

          <div className="form-actions">
            <button
              type="submit"
              className="primary-button"
              disabled={creating}
            >
              {creating
                ? editingCompanyId !== null
                  ? "Updating..."
                  : "Creating..."
                : editingCompanyId !== null
                  ? "Update Company"
                  : "Create Company"}
            </button>

            {editingCompanyId !== null && (
              <button
                type="button"
                className="secondary-button"
                onClick={handleCancelEdit}
                disabled={creating}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="dashboard-section">
        <h2>Your Companies</h2>

        {companies.length === 0 ? (
          <div className="empty-state">
            <p>No companies found.</p>
          </div>
        ) : (
          <div className="dashboard-grid">
            {companies.map((company) => (
              <div
                className="dashboard-card"
                key={company.id}
              >
                <h3>{company.name}</h3>

                <p>
                  <strong>Location:</strong>{" "}
                  {company.location}
                </p>

                <p>
                  <strong>Description:</strong>{" "}
                  {company.description ||
                    "Not provided"}
                </p>

                <p>
                  <strong>Website:</strong>{" "}
                  {company.website ||
                    "Not provided"}
                </p>

                <div className="form-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      handleEdit(company)
                    }
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="logout-button"
                    onClick={() =>
                      handleDelete(company.id)
                    }
                    disabled={
                      deletingCompanyId ===
                      company.id
                    }
                  >
                    {deletingCompanyId ===
                    company.id
                      ? "Deleting..."
                      : "Delete"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Company;