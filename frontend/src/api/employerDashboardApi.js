import api from "./axios";

export const getEmployerDashboard = async () => {
  const response = await api.get("/employer/dashboard");
  return response.data;
};