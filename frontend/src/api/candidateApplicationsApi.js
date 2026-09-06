import api from "./axios";

export const createApplication = async (applicationData) => {
  const response = await api.post(
    "/applications/",
    applicationData
  );

  return response.data;
};

export const getMyApplications = async (params = {}) => {
  const response = await api.get(
    "/applications/",
    { params }
  );

  return response.data;
};

export const getApplication = async (applicationId) => {
  const response = await api.get(
    `/applications/${applicationId}`
  );

  return response.data;
};

export const getApplicationHistory = async (applicationId) => {
  const response = await api.get(
    `/applications/${applicationId}/history`
  );

  return response.data;
};