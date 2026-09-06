import api from "./axios";

export const getMyResumes = async () => {
  const response = await api.get("/resumes/");
  return response.data;
};

export const downloadResume = async (resumeId) => {
  const response = await api.get(`/resumes/${resumeId}/download`, {
    responseType: "blob",
  });

  return response;
};

export const setPrimaryResume = async (resumeId) => {
  const response = await api.put(`/resumes/${resumeId}/primary`);
  return response.data;
};

export const deleteResume = async (resumeId) => {
  const response = await api.delete(`/resumes/${resumeId}`);
  return response.data;
};

export const uploadResume = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/resumes/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};