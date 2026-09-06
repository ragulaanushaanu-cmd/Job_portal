import api from "./axios";

export const getEmployerCompanies = async () => {
  const response = await api.get("/employer/companies");
  return response.data;
};

export const createCompany = async (companyData) => {
  const response = await api.post("/companies/", companyData);
  return response.data;
};

export const getCompany = async (companyId) => {
  const response = await api.get(`/companies/${companyId}`);
  return response.data;
};

export const updateCompany = async (companyId, companyData) => {
  const response = await api.put(
    `/companies/${companyId}`,
    companyData
  );
  return response.data;
};

export const deleteCompany = async (companyId) => {
  const response = await api.delete(
    `/companies/${companyId}`
  );
  return response.data;
};