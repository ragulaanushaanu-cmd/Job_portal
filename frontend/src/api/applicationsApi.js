import api from "./axios";

export const getEmployerApplications = async (params = {}) => {
  const response = await api.get("/applications/employer", {
    params,
  });

  return response.data;
};

export const updateApplicationStatus = async (applicationId, status) => {
  const response = await api.put(
    `/applications/${applicationId}`,
    {
      status,
    }
  );

  return response.data;
};