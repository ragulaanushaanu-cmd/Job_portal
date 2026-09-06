import api from "./axios";

export const loginUser = async (username, password) => {
  const formData = new URLSearchParams();

  formData.append("grant_type", "password");
  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post("/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return response.data;
};