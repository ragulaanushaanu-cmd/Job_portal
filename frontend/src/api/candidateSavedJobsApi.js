import api from "./axios";

export const getSavedJobs = async (params = {}) => {
  const response = await api.get("/saved-jobs/", { params });
  return response.data;
};

export const saveJob = async (jobId) => {
  const response = await api.post(`/saved-jobs/${jobId}`);
  return response.data;
};

export const deleteSavedJob = async (jobId) => {
  const response = await api.delete(`/saved-jobs/${jobId}`);
  return response.data;
};