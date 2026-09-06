import api from "./axios";

export const getEmployerJobs = async () => {
  const response = await api.get("/employer/jobs");
  return response.data;
};

export const createJob = async (jobData) => {
  const response = await api.post("/jobs/", jobData);
  return response.data;
};

export const getJob = async (jobId) => {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
};

export const updateJob = async (jobId, jobData) => {
  const response = await api.put(`/jobs/${jobId}`, jobData);
  return response.data;
};

export const deleteJob = async (jobId) => {
  const response = await api.delete(`/jobs/${jobId}`);
  return response.data;
};