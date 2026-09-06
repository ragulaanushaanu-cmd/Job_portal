import api from "./axios";

export const getMyResumes = async () => {
  const response = await api.get("/resumes/");
  return response.data;
};